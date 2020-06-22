import sqlite3

from .base import BaseService
from .exceptions import ConflictError, DoesNotExistError, BrokenRulesError


class CategoriesService(BaseService):
    def get_categories(self, user_id):
        """
        Получение категорий пользователя
        :param user_id: id пользователя
        :return: Все категории, созданные данным пользователем
        """
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
        """
        Получение пути внутри дерева для категории
        :param category_id: id категории
        :return tree_path: Путь до категории в дереве категорий
        """
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

    def _get_category_by_id(self, category_id):
        """
        Полученеи категории по её id
        :param category_id: id категории
        :return: Категория
        """
        cur = self.connection.execute(
            'SELECT id, title, parent_id, user_id, tree_path '
            'FROM category '
            'WHERE id = ?',
            (category_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise DoesNotExistError(f'Category with id {category_id} does not exist.')
        category = dict(row)
        return category

    def create_category(self, user_id, category_data):
        """
        Создание категории
        :param user_id: id пользователя
        :param category_data: Информация о добавляемой категории (имя, id родителя (если есть))
        :return:
        """
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

        self._update_category(category_id, tree_path=path)
        self.connection.commit()

        return category_data

    def _create_category(self, user_id, category_data):
        """
        Добавление категории в базу данных
        :param user_id: id пользователя
        :param category_data: Информация о добавляемой категории
        :return:
        """
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

    def _update_category(self, category_id, **category_data):
        """
        Обновление информации (title, tree_path) для категории внутри дерева категорий
        :param category_id: id категории
        :param **category_data: Поля, для которых требуются изменения
        """
        if not category_data:
            return
        category_params = ', '.join(f'{key} = ?' for key in category_data)
        category_query = f'UPDATE category SET {category_params} WHERE id = ?'
        self.connection.execute(category_query, (*category_data.values(), category_id))

    def is_owner(self, user_id, category_id):
        """
        Проверка, является ли пользователь владельцем категории
        :param user_id: id пользователя
        :param category_id: id категории
        :return: true/false - является или нет
        """
        cur = self.connection.execute(
            'SELECT (user.id = ?) AS is_owner '
            'FROM category '
            'INNER JOIN user ON user.id = category.user_id '
            'WHERE category.id = ?',
            (user_id, category_id,),
        )
        row = cur.fetchone()
        return row is None or bool(row['is_owner'])

    def update_category(self, category_id, category_data):
        """
        Изменение категории
        :param category_id: id категории
        :param category_data: Информация об изменяемой категории (имя (если есть), id родителя (если есть))
        :return: Измененная категория
        """
        if 'parent_id' in category_data:
            category = self._get_category_by_id(category_id)
            old_parent_id = category['parent_id']
            new_parent_id = category_data['parent_id']

            if old_parent_id != new_parent_id:
                current_node = str(category_id).zfill(8)
                old_path = category['tree_path']
                if new_parent_id is not None:
                    new_parent = self._get_category_by_id(new_parent_id)
                    new_path = new_parent['tree_path'] + '.' + current_node
                else:
                    new_path = current_node
                self._update_tree_path_prefix(old_path, new_path)

        self._update_category(category_id, **category_data)
        category = self._get_category_by_id(category_id)
        return category

    def _update_tree_path_prefix(self, old_prefix, new_prefix):
        """
        Обновляем пути категорий
        :param old_prefix: Старый префикс пути
        :param new_prefix: Новй префикс пути
        """
        self.connection.execute(
            'UPDATE category '
            'SET tree_path = replace(tree_path, ?, ?) '
            'WHERE tree_path LIKE ?',
            (old_prefix, new_prefix, old_prefix + '%'),
        )

    def delete_category(self, category_id):
        """
        Удаление категории и её потомков
        :param category_id: id категории
        """
        self._get_category_by_id(category_id)
        tree_path = self._get_category_path(category_id)
        self._delete_category(tree_path)

    def _delete_category(self, tree_path):
        self.connection.execute(
            'DELETE FROM category '
            'WHERE tree_path LIKE ?',
            (tree_path + '%',),
        )
