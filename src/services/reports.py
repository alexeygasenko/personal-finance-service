from .base import BaseService
from .exceptions import ConflictError, DoesNotExistError, BrokenRulesError


class ReportService(BaseService):
    def get_report(self, user_id, qs):
        """
        category, from, to, period, page, page_size
        """
        raw_report = self._get_report(user_id, qs)

        return raw_report

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
        return [dict(row) for row in rows]
