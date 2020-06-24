from flask import (
    Blueprint,
    request,
    jsonify,
)
from flask.views import MethodView

from auth import auth_required
from database import db
from services.exceptions import ServiceError
from services.reports import ReportService


class ReportView(MethodView):
    @auth_required(pass_user=True)
    def get(self, user):
        qs = dict(request.args)
        with db.connection as connection:
            service = ReportService(connection)
            try:
                report = service.get_report(user['id'], qs)
            except ServiceError as e:
                return e.error, e.code
            return jsonify(report)


bp = Blueprint('reports', __name__)
bp.add_url_rule('', view_func=ReportView.as_view('report'))
