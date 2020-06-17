from http import HTTPStatus

from flask import (
    Blueprint,
    request,
    session,
)
from werkzeug.security import check_password_hash

from database import db

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['POST'])
def login():
    """
    Авторизация пользователя в сессии
    """
    request_json = request.json
    email = request_json['email']
    password = request_json['password']

    with db.connection as connection:
        cur = connection.execute(
            'SELECT id, password '
            'FROM user '
            'WHERE email = ?',
            (email,),
        )
        row = cur.fetchone()

        if row is None:
            return '', HTTPStatus.FORBIDDEN
        if not check_password_hash(row['password'], password):
            return '', HTTPStatus.FORBIDDEN

        session['user_id'] = row['id']
        return '', HTTPStatus.OK


@bp.route('/logout', methods=['POST'])
def logout():
    """
    Выход пользователя из сессии
    """
    session.clear()
    return '', HTTPStatus.OK
