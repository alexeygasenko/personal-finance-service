from http import HTTPStatus

from flask import (
    Blueprint,
    request,
    jsonify,
)

from flask.views import MethodView

from database import db
from auth import auth_required
from services.categories import CategoriesService
from services.exceptions import ServiceError


class CategoriesView(MethodView):
    @auth_required(pass_user=True)
    def get(self, user):
        """
        Получение категорий пользователя
        :param user: Пользователь
        :return: Категории
        """
        with db.connection as connection:
            service = CategoriesService(connection)
            categories = service.get_categories(user['id'])
            return jsonify(categories)

    @auth_required(pass_user=True)
    def post(self, user):
        """
        Добавление категории
        :param user: Пользователь
        :return: Созданная категория
        """
        with db.connection as connection:
            service = CategoriesService(connection)
            try:
                category = service.create_category(user['id'], request.json)
            except ServiceError as e:
                return e.error, e.code
            return category, HTTPStatus.CREATED


class CategoryView(MethodView):
    @auth_required(pass_user=True)
    def patch(self, category_id, user):
        """
        Редактирование категории
        :param category_id: id категории
        :param user: Пользователь
        :return: Измененная категория
        """
        with db.connection as connection:
            service = CategoriesService(connection)
            if not service.is_owner(user['id'], category_id):
                return '', HTTPStatus.FORBIDDEN
            try:
                category = service.update_category(user['id'], category_id, request.json)
            except ServiceError as e:
                return e.error, e.code
            return category, HTTPStatus.OK

    @auth_required(pass_user=True)
    def delete(self, category_id, user):
        """
        Удаление категории и её потомков
        :param category_id: id категории
        :param user: Пользователь
        """
        with db.connection as connection:
            service = CategoriesService(connection)
            if not service.is_owner(user['id'], category_id):
                return '', HTTPStatus.FORBIDDEN
            try:
                service.delete_category(category_id)
            except ServiceError as e:
                return e.error, e.code
            return '', HTTPStatus.NO_CONTENT


bp = Blueprint('categories', __name__)
bp.add_url_rule('', view_func=CategoriesView.as_view('categories'))
bp.add_url_rule('/<int:category_id>', view_func=CategoryView.as_view('category'))
