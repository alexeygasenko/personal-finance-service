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


class CategoriesView(MethodView):
    @auth_required(pass_user=True)
    def get(self, user):
        with db.connection as connection:
            service = CategoriesService(connection)
            categories = service.get_categories(user['id'])
            return jsonify(categories)

    @auth_required(pass_user=True)
    def post(self):
        pass


class CategoryView(MethodView):
    @auth_required(pass_user=True)
    def patch(self):
        pass

    @auth_required(pass_user=True)
    def delete(self):
        pass


bp = Blueprint('categories', __name__)
bp.add_url_rule('', view_func=CategoriesView.as_view('categories'))
bp.add_url_rule('/<int:category_id>', view_func=CategoryView.as_view('category'))
