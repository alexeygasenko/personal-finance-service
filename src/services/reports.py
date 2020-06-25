from .base import BaseService
from .categories import CategoriesService
from .exceptions import ConflictError, DoesNotExistError, BrokenRulesError


class ReportService(BaseService):
    def get_report(self, user_id, qs):
        """
        category, from, to, period, page, page_size
        """
        raw_operations = self._get_report(user_id, qs)
        operations = self._get_operation_categories(user_id, raw_operations)

        report = {'operations': operations}

        return report

    def _get_report(self, user_id, qs):
        query = (
            'SELECT'
            ' operation.id,'
            ' operation.operation_date,'
            ' operation.type,'
            ' operation.amount,'
            ' operation.description,'
            ' category.tree_path, '
            'SUM(amount) AS total_amount '
            'FROM operation '
            'LEFT JOIN category ON operation.category_id = category.id '
            '{where_clause} '
            '{limit_clause} '
            '{offset_clause} '
        )
        where_conditions = []
        limit_clause = ''
        offset_clause = ''
        params = []

        where_conditions.append('operation.user_id = ?')
        params.append(user_id)

        if qs:
            category_id = qs.get('category')
            if category_id:
                node = '"%' + str(category_id).zfill(8) + '%"'
                where_conditions.append(f'category.tree_path LIKE {node} ')

            page = qs.get('page')
            page_size = qs.get('page_size')
            if not page:
                page = 1
            if not page_size:
                page_size = 15
            limit_clause = f'LIMIT {page_size}'
            offset = (int(page) - 1) * int(page_size)
            offset_clause = f'OFFSET {offset}'

        where_clause = ''
        if where_conditions:
            where_clause = 'WHERE {}'.format(' AND '.join(where_conditions))
        query = query.format(where_clause=where_clause, limit_clause=limit_clause, offset_clause=offset_clause)
        print(query)

        cur = self.connection.execute(query, params)
        rows = cur.fetchall()
        raw_operations = [dict(row) for row in rows]
        return raw_operations

    def _get_operation_categories(self, user_id, raw_operations):
        categories_service = CategoriesService(self.connection)
        user_categories = categories_service.get_categories(user_id)

        for operation in raw_operations:
            operation['categories'] = []
            categories_ids = [s.lstrip('0') for s in operation['tree_path'].split('.')]
            for category in user_categories:

                # Отсортированы в верном порядке?
                if str(category['id']) in categories_ids:
                    operation['categories'].append(category)
                    operation.pop('tree_path', None)

        return raw_operations
