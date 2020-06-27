import sqlite3

from werkzeug.security import generate_password_hash

from .base import BaseService
from .exceptions import (
    ConflictError,
    DoesNotExistError,
)


class UsersService(BaseService):
    def get_user(self, user_id):
        """
        Получение пользователя по его id
        :param user_id: id пользователя
        :return: Информация о пользователе (id, email и имя)
        """
        fields = ['id', 'email', 'first_name', 'last_name']
        row = self.select_row(
            fields,
            table_name='user',
            where='id',
            equals_to=user_id,
        )
        if row is None:
            raise DoesNotExistError(f'User with ID {user_id} does not exist.')
        user = {
            key: row[key]
            for key in row.keys()
            if row[key] is not None
        }
        self.connection.commit()
        return user

    def create_user(self, user_data):
        """
        Создание пользователя в базе данных
        :param user_data: Информация о пользователе (email, имя, пароль)
        :return: Информация о пользователе (id, email и имя)
        """
        user_id = self._create_user(user_data)
        user_data['id'] = user_id
        user_data.pop('password')
        return user_data

    def _create_user(self, user_data):
        """
        Функция для записи нового пользователя в базу данных
        :param user_data: Информация о пользователе (email, имя, пароль)
        :return: id созданного пользователя
        """
        user_data['password'] = generate_password_hash(user_data['password'])
        try:
            user_id = self.insert_row(
                table_name='user',
                **user_data
            )
        except sqlite3.IntegrityError:
            raise ConflictError(f'User with email {user_data["email"]} already exists.') from None
        self.connection.commit()
        return user_id
