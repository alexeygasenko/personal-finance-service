from flask import Flask
import os

from blueprints.auth import bp as auth_bp
from blueprints.users import bp as users_bp
from create_db import create_db
from database import db


def create_app():
	app = Flask(__name__)
	app.config.from_object('config.Config')
	db.init_app(app)
	if not os.path.exists(os.path.join(os.getcwd(), app.config['DB_CONNECTION'])):
		create_db(app)
	app.register_blueprint(auth_bp, url_prefix='/auth')
	app.register_blueprint(users_bp, url_prefix='/users')
	return app
