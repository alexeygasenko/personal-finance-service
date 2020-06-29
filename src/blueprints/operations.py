from http import HTTPStatus
from flask import (
    Blueprint,
    request,
    jsonify,
)

from flask.views import MethodView
from auth import auth_required
from database import db
from services.operations import OperationsService
from services.exceptions import (
    ServiceError,
)


class OperationsView(MethodView):

    @auth_required(pass_user=True)
    def post(self, user):
        with db.connection as connection:
            service = OperationsService(connection)
            try:
                operation = service.create_operation(user, request.json)
            except ServiceError as e:
                connection.rollback()
                return e.error, e.code
            else:
                connection.commit()
                return operation, HTTPStatus.CREATED


class OperationView(MethodView):
 
    @auth_required(pass_user=True)
    def patch(self, operation_id, user):
        with db.connection as connection:
            service = OperationsService(connection)
            if not service.is_owner(user['id'], operation_id):
                return '', HTTPStatus.FORBIDDEN
            try:
                operation = service.update_operation(operation_id, request.json)
            except ServiceError as e:
                connection.rollback()
                return e.error, e.code
            else:
                connection.commit()
                return jsonify(operation), HTTPStatus.OK

    @auth_required(pass_user=True)
    def delete(self, operation_id, user):
        with db.connection as connection:
            service = OperationsService(connection)
            if not service.is_owner(user['id'], operation_id):
                return '', HTTPStatus.FORBIDDEN
            try:
                service.delete_operation(operation_id)
            except ServiceError as e:
                connection.rollback()
                return e.error, e.code
            else:
                connection.commit()
                return '', HTTPStatus.NO_CONTENT


bp = Blueprint('operations', __name__)
bp.add_url_rule('', view_func=OperationsView.as_view('operations'))
bp.add_url_rule('/<int:operation_id>', view_func=OperationView.as_view('operation'))
