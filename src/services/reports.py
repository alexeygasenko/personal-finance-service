from datetime import datetime
from dateutil.relativedelta import relativedelta, MO
from math import ceil

from .base import BaseService
from .categories import CategoriesService


class ReportService(BaseService):
    def get_report(self, user_id, qs):
        raw_operations, total_items, total_pages = self._get_report(user_id, qs)
        if not raw_operations:
            operations = {
                'operations': [],
                'total_amount': 0,
                'total_items': 0,
                'total_pages': 0
            }
            return operations

        total_amount = raw_operations[0]['total_amount']

        operations = self._get_operation_categories(user_id, raw_operations)

        report = {
            'operations': operations,
            'total_amount': total_amount,
            'total_items': total_items,
            'total_pages': total_pages
        }

        return report

    def _get_report(self, user_id, qs):
        query = (
            'SELECT'
            ' operation.id,'
            ' operation.operation_date,'
            ' operation.type,'
            ' operation.amount,'
            ' operation.description,'
            ' category.tree_path,'
            'SUM(amount) OVER () AS total_amount, '
            'COUNT(*) OVER () AS total_items '
            'FROM operation '
            'LEFT JOIN category ON operation.category_id = category.id '
            '{where_clause} '
            '{limit_clause} '
            '{offset_clause} '
        )
        where_conditions = []
        params = []

        where_conditions.append('operation.user_id = ?')
        params.append(user_id)

        category_id = qs.get('category')
        if category_id:
            node = f'%{str(category_id).zfill(8)}%'
            where_conditions.append('category.tree_path LIKE ? ')
            params.append(node)

        self._convert_time_period(qs)

        date_from = qs.get('from')
        if date_from:
            where_conditions.append("strftime('%s',operation.operation_date) >= strftime('%s', ?) ")
            params.append(date_from)

        date_to = qs.get('to')
        if date_to:
            where_conditions.append("strftime('%s', operation.operation_date) < strftime('%s', ?) ")
            params.append(date_to)

        page = int(qs.get('page', 1))
        page_size = int(qs.get('page_size', 15))

        limit_clause = f'LIMIT ?'
        params.append(page_size)
        offset = (page - 1) * page_size
        offset_clause = f'OFFSET ?'
        params.append(offset)

        where_clause = ''
        if where_conditions:
            where_clause = 'WHERE {}'.format(' AND '.join(where_conditions))
        query = query.format(where_clause=where_clause, limit_clause=limit_clause, offset_clause=offset_clause)

        cur = self.connection.execute(query, params)
        rows = cur.fetchall()
        raw_operations = [dict(row) for row in rows]

        total_items = 0
        total_pages = 0
        if raw_operations:
            total_items = raw_operations[0]['total_items']
            total_pages = ceil(total_items / page_size)

        return raw_operations, total_items, total_pages

    def _get_operation_categories(self, user_id, raw_operations):
        categories_service = CategoriesService(self.connection)
        user_categories = {
            category['id']: {
                'id': category['id'],
                'title': category['title']
            }
            for category in categories_service.get_categories(user_id)
        }

        for operation in raw_operations:
            operation['categories'] = []
            if operation['tree_path'] is not None:
                categories_ids = [int(s.lstrip('0')) for s in operation['tree_path'].split('.')]
                for category_id in categories_ids:
                    operation['categories'].append(user_categories[category_id])
            operation.pop('tree_path', None)
            operation.pop('total_amount', None)
            operation.pop('total_items', None)

        return raw_operations

    def _convert_time_period(self, qs):
        period = qs.get('period')
        if not period:
            return

        current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if period == 'week':
            qs['from'] = (current_date + relativedelta(weekday=MO(-1))).isoformat()

        if period == 'prevweek':
            qs['from'] = (current_date + relativedelta(weekday=MO(-2))).isoformat()
            qs['to'] = (current_date + relativedelta(weekday=MO(-1))).isoformat()

        if period == 'month':
            qs['from'] = (current_date.replace(day=1)).isoformat()

        if period == 'prevmonth':
            qs['from'] = (current_date.replace(day=1) - relativedelta(months=1)).isoformat()
            qs['to'] = (current_date.replace(day=1)).isoformat()

        if period == 'quarter':
            quarter = (current_date.month - 1) // 3
            quarter_start_month = quarter * 3 + 1
            qs['from'] = current_date.replace(month=quarter_start_month, day=1)

        if period == 'prevquarter':
            quarter = (current_date.month - 1) // 3
            quarter_start_month = quarter * 3 + 1
            quarter_end = current_date.replace(month=quarter_start_month, day=1)
            quarter_start = quarter_end - relativedelta(months=3)
            qs['from'] = quarter_start.isoformat()
            qs['to'] = quarter_end.isoformat()

        if period == 'year':
            qs['from'] = current_date.replace(month=1, day=1).isoformat()

        if period == 'prevyear':
            year_end = current_date.replace(month=1, day=1)
            year_start = year_end - relativedelta(years=1)
            qs['from'] = year_start.isoformat()
            qs['to'] = year_end.isoformat()
