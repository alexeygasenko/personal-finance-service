class BaseService:
    def __init__(self, connection):
        self.connection = connection

    @classmethod
    def make_placeholders(cls, n):
        return ', '.join('?' for _ in range(n))

    @classmethod
    def make_update_fields(cls, fields):
        return ', '.join(f'{field} = ?' for field in fields)

    @classmethod
    def make_select_fields(cls, fields):
        return ', '.join(f'{field}' for field in fields)

    @classmethod
    def make_select_query(cls, fields, table_name, where, order_by):
        fields_to_select = cls.make_select_fields(fields)
        select_query = f'SELECT {fields_to_select} FROM {table_name} WHERE {where} = ?'
        if order_by:
            select_query += f' ORDER BY {order_by}'
        return select_query

    def select_row(self, table_name, where, equals_to, order_by=False, **fields):
        select_query = self.make_select_query(fields, table_name, where, order_by)
        cur = self.connection.execute(select_query, (equals_to,),)
        row = cur.fetchone()
        return row

    def select_rows(self, table_name, where, equals_to, order_by=False, **fields):
        select_query = self.make_select_query(fields, table_name, where, order_by)
        cur = self.connection.execute(select_query, (equals_to,), )
        rows = cur.fetchall()
        return rows

    def insert_row(self, table_name, **fields):
        params = self.make_select_fields(fields)
        placeholders = self.make_placeholders(len(fields))
        insert_query = f'INSERT INTO {table_name}({params}) VALUES ({placeholders})'
        cur = self.connection.execute(insert_query, (*fields.values(),))
        return cur.lastrowid

    def update_row(self, table_name, where, equals_to, **fields):
        params = self.make_update_fields(fields)
        update_query = f'UPDATE {table_name} SET {params} WHERE {where} = ?'
        self.connection.execute(update_query, (*fields.values(), equals_to),)

    def delete_row(self):
        pass
