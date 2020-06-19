from http import HTTPStatus

from flask import (
    Blueprint,
    request,
)

from flask.views import MethodView

from database import db
from services.users import UsersService
from services.exceptions import (
    ServiceError,
)


class UsersView(MethodView):
    def post(self):
        """
        Создание пользователя в базе данных
        :return: Информация о пользователе (id, email и имя)
        """
        with db.connection as connection:
            service = UsersService(connection)
            try:
                user = service.create_user(request.json)
            except ServiceError as e:
                connection.rollback()
                return e.error, e.code
            else:
                connection.commit()
                return user, HTTPStatus.CREATED


bp = Blueprint('users', __name__)
bp.add_url_rule('', view_func=UsersView.as_view('users'))
