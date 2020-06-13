from flask import Flask
import os
from create_db import create_db


def create_app():
	app = Flask(__name__)
	app.config.from_object('config.Config')
	if not os.path.exists(os.path.join(os.getcwd(), app.config['DB_CONNECTION'])):
		create_db(app)
	return app
