import sqlite3
import os


def create_db(app, db_name):
	connection = sqlite3.connect(
		db_name,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
	)
	connection.row_factory = sqlite3.Row
	connection.cursor().executescript(
		'CREATE TABLE "category" ('
		'"id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, '
		'"title" TEXT NOT NULL, '
		'"parent_category" INTEGER, '
		'FOREIGN KEY("parent_category") REFERENCES "category"("id") '
		'); '
		'CREATE TABLE "user" ('
		'"id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, '
		'"first_name" TEXT NOT NULL, '
		'"last_name" TEXT NOT NULL, '
		'"email" TEXT NOT NULL UNIQUE, '
		'"password" TEXT NOT NULL '
		'); '
		'CREATE TABLE "operation" ('
		'"id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, '
		'"type" NUMERIC NOT NULL, '
		'"amount" INTEGER NOT NULL, '
		'"description" TEXT, '
		'"category_id" INTEGER, '
		'"record_date" TEXT NOT NULL, '
		'"operation_date" TEXT NOT NULL, '
		'"user_id" INTEGER NOT NULL, '
		'FOREIGN KEY("user_id") REFERENCES "user"("id"), '
		'FOREIGN KEY("category_id") REFERENCES "category"("id")'
		'); '
	)