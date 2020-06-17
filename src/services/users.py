from werkzeug.security import generate_password_hash

from .base import BaseService
from .exceptions import (
    ConflictError,
)


class UsersService(BaseService):
    def create_user(self, user_data):
        cur = self.connection.execute(
            'SELECT id '
            'FROM user '
            'WHERE email = ?',
            (user_data['email'],),
        )
        row = cur.fetchone()

        if row is not None:
            raise ConflictError(f'User with email "{user_data["email"]}" already exists.')

        user_id = self._create_user(user_data)
        user_data['id'] = user_id
        user_data.pop('password')
        return user_data

    def _create_user(self, user_data):
        user_data['password'] = generate_password_hash(user_data['password'])
        cur = self.connection.execute(
            'INSERT INTO user (email, password, first_name, last_name) '
            'VALUES (?, ?, ?, ?)',
            (
                user_data['email'],
                user_data['password'],
                user_data['first_name'],
                user_data['last_name'],
            ),
        )
        user_id = cur.lastrowid
        return user_id
