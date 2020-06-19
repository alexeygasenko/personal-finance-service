import sqlite3

from .base import BaseService
from .exceptions import ConflictError, DoesNotExistError, BrokenRulesError


class CategoriesService(BaseService):
    def get_categories(self, user_id):
        cur = self.connection.execute(
            'SELECT id, title, parent_id, user_id '
            'FROM category '
            'WHERE user_id = ? '
            'ORDER BY tree_path',
            (user_id,),
        )
        rows = cur.fetchall()
        categories = [dict(row) for row in rows]
        return categories

    def _get_category_path(self, category_id):
        cur = self.connection.execute(
            'SELECT tree_path '
            'FROM category '
            'WHERE id = ?',
            (category_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise DoesNotExistError(f'Category with id {category_id} does not exist.')
        tree_path = row['tree_path']
        return tree_path

    def create_category(self, user_id, category_data):
        category_id = self._create_category(user_id, category_data)
        category_data['id'] = category_id
        parent_path = None

        if category_data.get('parent_id') is not None:
            try:
                parent_path = self._get_category_path(category_data['parent_id'])
            except DoesNotExistError:
                self.connection.rollback()
                raise BrokenRulesError(f'Parent category does not exist.')

        current_node = str(category_id).zfill(8)
        if parent_path is None:
            path = current_node
        else:
            path = parent_path + '.' + current_node

        self._update_category_path(category_id, path)
        self.connection.commit()

        return category_data

    def _create_category(self, user_id, category_data):
        try:
            cur = self.connection.execute(
                'INSERT INTO category(title, parent_id, user_id, tree_path) '
                'VALUES (?, ?, ?, ?)',
                (
                    category_data['title'],
                    category_data.get('parent_id'),
                    user_id,
                    '',
                ),
            )
        except sqlite3.IntegrityError:
            raise ConflictError(f'Category with name {category_data["title"]} already exists for that user.')
        category_id = cur.lastrowid
        self.connection.commit()
        return category_id

    def _update_category_path(self, category_id, path):
        self.connection.execute(
            'UPDATE category '
            'SET tree_path = ? '
            'WHERE id = ?',
            (path, category_id,),
        )
