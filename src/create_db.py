import sqlite3


def create_db(app):
	with sqlite3.connect(app.config['DB_CONNECTION']) as connection:
		connection.executescript("""
			CREATE TABLE category (
			id              INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
			title           TEXT NOT NULL, 
			parent_id 		INTEGER, 
			user_id         INTEGER NOT NULL,
			tree_path		TEXT NOT NULL,
			UNIQUE(title, user_id), 
			FOREIGN KEY(parent_id) REFERENCES category(id),
			FOREIGN KEY(user_id) REFERENCES user(id) 
			); 
			
			CREATE TABLE user (
			id         INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
			first_name TEXT NOT NULL, 
			last_name  TEXT NOT NULL, 
			email      TEXT NOT NULL UNIQUE, 
			password   TEXT NOT NULL 
			);
			
			CREATE TABLE operation (
			id             INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
			type           TEXT NOT NULL, 
			amount         INTEGER NOT NULL, 
			description    TEXT, 
			category_id    INTEGER, 
			record_date    TEXT NOT NULL, 
			operation_date TEXT NOT NULL, 
			user_id        INTEGER NOT NULL, 
			FOREIGN KEY(user_id) REFERENCES user(id), 
			FOREIGN KEY(category_id) REFERENCES category(id) ON DELETE SET NULL
			); 
		""")
		connection.commit()
