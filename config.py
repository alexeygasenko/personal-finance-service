import os


class Config:
	SECRET_KEY = os.getenv('SECRET_KEY', 'secret')
	DB_CONNECTION = os.getenv('DB_CONNECTION', 'db.db')