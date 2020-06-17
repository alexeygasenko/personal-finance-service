from functools import wraps
from http import HTTPStatus

from flask import session

from database import db
from services.users import UsersService
from services.exceptions import DoesNotExistError


def auth_required(*, pass_user=False):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return '', HTTPStatus.UNAUTHORIZED
            with db.connection as connection:
                service = UsersService(connection)
                try:
                    user = service.get_user(user_id)
                except DoesNotExistError as e:
                    return e.error, HTTPStatus.UNAUTHORIZED
            if pass_user:
                kwargs['user'] = user
            return view_func(*args, **kwargs)
        return wrapper
    return decorator
