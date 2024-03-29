from datetime import datetime

from .base import BaseService
from .categories import CategoriesService
from .exceptions import (
    DoesNotExistError,
    BrokenRulesError
)


def check_amount(operation_type, amount):
    """
    Проверяет совпадение типа и суммы операции
    :param operation_type: Тип операции
    :param amount: Сумма
    """
    if operation_type == 'income' and amount < 0:
        raise BrokenRulesError('Income must be > 0.')
    if operation_type == 'expenses' and amount > 0:
        raise BrokenRulesError('Expenses must be < 0.')


def validate_date(operation):
    try:
        operation['operation_date'] = datetime.fromisoformat(operation['operation_date']).isoformat()
    except ValueError:
        raise BrokenRulesError('Wrong date format. It must be %Y-%m-%dT%H:%M:%S.%f')


class OperationsService(BaseService):
    def create_operation(self, user, operation_data):
        """
        Создание операции
        :param user: id пользователя, добавляющего данную операцию
        :param operation_data: данные об операции(тип, сумма, описание(если есть),
            id категории(если есть), дата)
        :return: Созданная операция
        """
        operation_data['user_id'] = user['id']

        if not operation_data.get('type'):
            raise BrokenRulesError('Missing field "type".')
        if not operation_data.get('amount'):
            raise BrokenRulesError('Missing field "amount".')

        if operation_data.setdefault('category_id', None) is not None:
            category_id = operation_data['category_id']
            try:
                service = CategoriesService(self.connection)
                service.get_category_by_user_id(user['id'], category_id)
            except DoesNotExistError:
                raise BrokenRulesError(f'Category with id {category_id} does not exist for that user.')

        if operation_data['type'] not in ('income', 'expenses'):
            raise BrokenRulesError('Wrong operation type.')
        check_amount(operation_data['type'], operation_data['amount'])
        operation_data['amount'] = int(operation_data['amount'] * 100)

        operation_data['record_date'] = datetime.now().isoformat()
        if operation_data.get('operation_date') is None:
            operation_data['operation_date'] = operation_data['record_date']
        validate_date(operation_data)

        operation_data.setdefault('description', None)

        operation_id = self._create_operation(operation_data)
        return self.get_operation_by_id(operation_id)

    def _create_operation(self, operation_data):
        """
        Добавление операции в базу данных операции
        :param operation_data: данные об операции
        :return: id добавленной операции
        """
        operation_id = self.insert_row(
            table_name='operation',
            **operation_data
        )
        return operation_id

    def get_operation_by_id(self, operation_id):
        """
        Получение операции по её id
        :param operation_id: id операции
        :return: Операция
        """
        fields = [
            'id',
            'type',
            'amount',
            'description',
            'category_id',
            'record_date',
            'operation_date',
            'user_id'
        ]
        row = self.select_row(
            table_name='operation',
            where='id',
            equals_to=operation_id,
            fields=fields
        )
        if row is None:
            raise DoesNotExistError(f'Operation with id {operation_id} does not exist.')
        operation = dict(row)
        operation['amount'] /= 100
        return operation

    def update_operation(self, user_id, operation_id, operation_data):
        """
        Обновляет данные у существующей операции
        :param operation_data: информация, на которую будет заменены поля, которые были отправлены
            (тип(если есть), сумма(если есть), описание(если есть), id категории(если есть), дата
            произведения операции)
        :param operation_id: id изменяемой операции
        :param user_id: id пользователя
        :return: Изменённая операция
        """
        try:
            old_operation = self.get_operation_by_id(operation_id)
        except DoesNotExistError:
            raise BrokenRulesError(f'Operation with id {operation_id} does not exist.')

        if operation_data.get('type'):
            if operation_data['type'] not in ('income', 'expenses'):
                raise BrokenRulesError('Wrong operation type.')
            if operation_data['type'] != old_operation['type']:
                operation_data.setdefault('amount', -old_operation['amount'])
            check_amount(operation_data['type'], operation_data['amount'])
            operation_data['amount'] = int(operation_data['amount'] * 100)

        if operation_data.get('category_id'):
            service = CategoriesService(self.connection)
            service.get_category_by_user_id(user_id, operation_data['category_id'])

        if operation_data.get('operation_date'):
            validate_date(operation_data)

        self.update_row(
            table_name='operation',
            where='id',
            equals_to=operation_id,
            **operation_data
        )
        return self.get_operation_by_id(operation_id)

    def delete_operation(self, operation_id):
        """
        Удаление операции
        :param operation_id: id операции
        """
        try:
            self.get_operation_by_id(operation_id)
        except DoesNotExistError:
            raise BrokenRulesError(f'Operation with id {operation_id} does not exist.')
        self.connection.execute(
            'DELETE FROM operation '
            'WHERE id = ?',
            (operation_id,),
        )

    def is_owner(self, user_id, operation_id):
        """
        Проверка, является ли пользователь создателем операции
        :param user_id: id пользователя
        :param operation_id: id операции
        :return: true/false - является или нет
        """
        cur = self.connection.execute(
            'SELECT (user.id = ?) AS is_owner '
            'FROM operation '
            'INNER JOIN user ON user.id = operation.user_id '
            'WHERE operation.id = ?',
            (user_id, operation_id,),
        )
        row = cur.fetchone()
        return row is None or bool(row['is_owner'])
