from datetime import datetime
from .base import BaseService
from .exceptions import (
    DoesNotExistError,
    BrokenRulesError
)



class OperationsService(BaseService):
    def create_operation(self, operation_data, user):
        # добавить проверку категорий
        operation_data['user_id'] = user['id']
        if not operation_data.get('type') or not operation_data.get('amount'):
            raise BrokenRulesError(f'Incomplete request.')
        operation_data['record_date'] = datetime.now(tz=None).isoformat(sep='T')
        if operation_data.get('operation_date') is None:
            operation_data['operation_date'] = datetime.now(tz=None).isoformat(sep='T')
        if operation_data.get('category_id') is None:
            operation_data['category_id'] = None
        if operation_data.get('description') is None:
            operation_data['description'] = None
        cur = self.connection.execute(
            'INSERT INTO operation (type, amount, description, category_id, record_date, operation_date, user_id) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (
                operation_data['type'],
                operation_data['amount'],
                operation_data['description'],
                operation_data['category_id'],
                operation_data['record_date'],
                operation_data['operation_date'],
                operation_data['user_id'],
            ),
        )
        operation_data['id'] = cur.lastrowid
        return operation_data


    def get_operation(self, operation_id):
        cur = self.connection.execute(
            'SELECT * '
            'FROM operation '
            'WHERE id = ?',
            (operation_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise DoesNotExistError(f'Operation with ID {operation_id} does not exist.')
        operation = {
            key: row[key]
            for key in row.keys()
            if row[key] is not None
        }
        return operation

    def update_operation(self, operation_data, operation_id):
        try:
            operation = OperationsService.get_operation(self, operation_id)
        except:
            raise DoesNotExistError(f'Operation with ID {operation_id} does not exist.')
        # проверить категорию
        if operation_data.get('type'):
            operation['type'] = operation_data.get('type')
        if operation_data.get('amount'):
            operation['amount'] = operation_data.get('amount')
        if operation_data.get('category_id'):

            operation['category_id'] = operation_data.get('category_id')
        if operation_data.get('operation_date'):
            operation['operation_date'] = operation_data.get('operation_date')
        if operation.get('category_id') is None:
            operation['category_id'] = None
        self.connection.execute(
            'UPDATE operation '
            'SET type = ?, amount = ?, category_id = ?, operation_date = ? '
            'WHERE id = ?',
            (operation['type'], operation['amount'], operation['category_id'], operation['operation_date'], operation_id,),
        )
        return OperationsService.get_operation(self, operation_id)

    def delete_operation(self, operation_id):
        try:
             operation = OperationsService.get_operation(self, operation_id)
        except:
            raise DoesNotExistError(f'Operation with ID {operation_id} does not exist.')
        self.connection.execute(
            'DELETE FROM operation '
            'WHERE id = ?',
            (operation_id,),
        )

    def is_owner(self, user, operation_id):
        cur = self.connection.execute(
            'SELECT user_id '
            'FROM operation '
            'WHERE id = ?',
            (operation_id,),
        )
        row = cur.fetchone()
        return row is not None and (row['user_id']) == user['id']








