import sqlite3


class SQLiteDB:
    def __init__(self, app=None):
        self._connection = None
        self._app = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self._app = app
        self._app.teardown_appcontext(self._disconnect)

    @property
    def connection(self):
        self._connect()
        return self._connection

    def _connect(self):
        database_connection = self._app.config['DB_CONNECTION']
        self._connection = sqlite3.connect(
            database_connection,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute(
            'PRAGMA foreign_keys = ON'
        )

    def _disconnect(self, exception=None):
        if self._connection is not None:
            self._connection.close()
            self._connection = None


db = SQLiteDB()
