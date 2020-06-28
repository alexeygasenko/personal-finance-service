import os

from flask import Flask

from blueprints.auth import bp as auth_bp
from blueprints.categories import bp as categories_bp
from blueprints.operations import bp as operations_bp
from blueprints.reports import bp as report_bp
from blueprints.users import bp as users_bp
from create_db import create_db
from database import db


def create_app():
	app = Flask(__name__)
	app.config.from_object('config.Config')
	if not os.path.exists(os.path.join(os.getcwd(), app.config['DB_CONNECTION'])):
		create_db(app)
	db.init_app(app)
	app.register_blueprint(auth_bp, url_prefix='/auth')
	app.register_blueprint(categories_bp, url_prefix='/categories')
	app.register_blueprint(operations_bp, url_prefix='/operations')
	app.register_blueprint(report_bp, url_prefix='/report')
	app.register_blueprint(users_bp, url_prefix='/users')
	return app
