from http import HTTPStatus
import json
from flask import (
    Blueprint,
    request,
)

from flask.views import MethodView
from auth import auth_required
from database import db
from services.operations import OperationsService
from services.exceptions import (
    ServiceError,
)


class OperationsView(MethodView):

    @auth_required(pass_user=False)
    def post(self):
        with db.connection as connection:
            service = OperationsService(connection)
            try:
                operation = service.create_operation(request.json)
            except ServiceError as e:
                connection.rollback()
                return e.error, e.code
            else:
                connection.commit()
                return operation, HTTPStatus.CREATED


class OperationView(MethodView):
 
    @auth_required(pass_user=False)
    def patch(self, operation_id):
        with db.connection as connection:
            service = OperationsService(connection)
            try:
                operation = service.patch_operation(request.json, operation_id)
            except ServiceError as e:
                connection.rollback()
                return e.error, e.code
            else:
                connection.commit()
                return json.dumps(operation), HTTPStatus.OK

    @auth_required(pass_user=False)
    def delete(self, operation_id):
        with db.connection as connection:
            service = OperationsService(connection)
            try:
                service.delete_operation(operation_id)
            except ServiceError as e:
                connection.rollback()
                return e.error, e.code
            else:
                connection.commit()
                return '', HTTPStatus.OK


bp = Blueprint('operations', __name__)
bp.add_url_rule('', view_func=OperationsView.as_view('operations'))
bp.add_url_rule('/<int:operation_id>', view_func=OperationView.as_view('operation'))
