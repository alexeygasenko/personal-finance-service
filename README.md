# personal-finance-service
Service for accounting your personal finances.

## How to run

- Create .env file:
	- SECRET_KEY=`%your_secret_key%`;
	- DB_CONNECTION=`%your_db_name%`;
	- FLASK_APP=`app:create_app`;
	- FLASK_ENV=`development`;
- set PYTHONPATH to `./src`
- Install all dependencies from requirements.txt;
- `flask run`
