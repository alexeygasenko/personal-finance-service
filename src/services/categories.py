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
        fields = ['id', 'title', 'parent_id', 'user_id']
        rows = self.select_rows(
            fields,
            table_name='category',
            where='user_id',
            equals_to=user_id,
            order_by='tree_path',
        )
        categories = [dict(row) for row in rows]
        return categories

    def _get_category_path(self, category_id):
        """
        Получение пути внутри дерева для категории
        :param category_id: id категории
        :return tree_path: Путь до категории в дереве категорий
        """
        fields = ['tree_path']
        row = self.select_row(
            fields,
            table_name='category',
            where='id',
            equals_to=category_id,
        )
        if row is None:
            raise DoesNotExistError(f'Category with id {category_id} does not exist.')
        tree_path = row['tree_path']
        return tree_path

    def get_category_by_user_id(self, user_id, category_id):
        """
        Получение категории по её id и id пользователя
        :param user_id: id пользователя
        :param category_id: id категории
        :return: Категория
        """
        fields = ['id', 'title', 'parent_id', 'user_id', 'tree_path']
        row = self.select_row(
            fields,
            table_name='category',
            where='user_id',
            equals_to=user_id,
            where_and='category.id',
            and_equals_to=category_id,
        )
        if row is None:
            raise DoesNotExistError(f'Category with id {category_id} does not exist.')
        category = dict(row)
        return category

    def get_category_by_id(self, category_id):
        """
        Получение категории по её id
        :param category_id: id категории
        :return: Категория
        """
        fields = ['id', 'title', 'parent_id', 'user_id', 'tree_path']
        row = self.select_row(
            fields,
            table_name='category',
            where='id',
            equals_to=category_id,
        )
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
                raise BrokenRulesError('Parent category does not exist.')

        """
        tree_path нужен для того, чтобы хранить путь от корневой категории до текущей в виде дерева.
        Это понадобится при выводе отчета и при лексикографической сортировке категорий внутри отчета.
        Нули дописываем вперед именно из-за лексикографической сортировки, иначе при сравнении
        строка '15' будет меньше строки '5'.
        8 нулей потому, что суммарно на всех пользователей категорий будет достаточно много, поэтому взял с запасом.
        """
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
        parent_id = category_data['parent_id']
        if parent_id is not None:
            self.get_category_by_user_id(user_id, parent_id)
        try:
            category_id = self.insert_row(
                table_name='category',
                title=category_data['title'],
                parent_id=category_data.get('parent_id'),
                user_id=user_id,
                tree_path=''
            )
        except sqlite3.IntegrityError:
            raise ConflictError(f'Category with name {category_data["title"]} already exists.')
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
        self.update_row(
            table_name='category',
            where='id',
            equals_to=category_id,
            **category_data
        )

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

    def update_category(self, user_id, category_id, category_data):
        """
        Изменение категории
        :param user_id: id пользователя
        :param category_id: id категории
        :param category_data: Информация об изменяемой категории (имя (если есть), id родителя (если есть))
        :return: Измененная категория
        """
        if 'parent_id' in category_data:
            try:
                category = self.get_category_by_user_id(user_id, category_id)
            except DoesNotExistError:
                raise BrokenRulesError(f'Category with id {category_id} does not exist.')
            old_parent_id = category['parent_id']
            new_parent_id = category_data['parent_id']
            if category_id == new_parent_id:
                raise BrokenRulesError('Category id and parent id must be different.')

            if old_parent_id != new_parent_id:
                current_node = str(category_id).zfill(8)
                old_path = category['tree_path']
                if new_parent_id is not None:
                    try:
                        new_parent = self.get_category_by_id(new_parent_id)
                    except DoesNotExistError:
                        raise BrokenRulesError(f'Category with id {new_parent_id} does not exist.')
                    if current_node in new_parent['tree_path']:
                        raise BrokenRulesError('Categories must not create cycles.')
                    new_path = new_parent['tree_path'] + '.' + current_node
                else:
                    new_path = current_node
                self._update_tree_path_prefix(old_path, new_path)

        self._update_category(category_id, **category_data)
        category = self.get_category_by_id(category_id)
        category.pop('tree_path')
        return category

    def _update_tree_path_prefix(self, old_prefix, new_prefix):
        """
        Обновление пути категорий
        :param old_prefix: Старый префикс пути
        :param new_prefix: Новый префикс пути
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
        try:
            tree_path = self._get_category_path(category_id)
        except DoesNotExistError:
            raise BrokenRulesError(f'Category with id {category_id} does not exist.')
        self._delete_category(tree_path)

    def _delete_category(self, tree_path):
        self.connection.execute(
            'DELETE FROM category '
            'WHERE tree_path LIKE ?',
            (tree_path + '%',),
        )
