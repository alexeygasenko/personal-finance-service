from .base import BaseService


class CategoriesService(BaseService):
    def get_categories(self, user_id):
        cur = self.connection.execute(
            'SELECT id, title, parent_id, user_id, tree_path '
            'FROM category '
            'WHERE user_id = ?',
            (user_id,),
        )
        rows = cur.fetchall()
        categories = [dict(row) for row in rows]
        return categories
