from datetime import datetime
from .base import BaseService
from .categories import CategoriesService
from .exceptions import (
    DoesNotExistError,
    BrokenRulesError
)


class OperationsService(BaseService):
    def _create_operation(self, operation_data):
        """
        Создание операции

        :param operation_data: данные об операции
        :return: id созданной операции
        """
        operation_id = self.insert_row(
            table_name='operation',
            **operation_data
        )
        return operation_id

    def create_operation(self, operation_data, user):
        """
        Создание операции

        :param user: id пользователя, добавляющего данную операцию
        :param operation_data: данные об операции(тип, сумма, описание(если есть),
         id категории(если есть), дата)
        :return: Созданная операция
        """

        operation_data['user_id'] = user['id']

        if not operation_data.get('type'):
            raise BrokenRulesError('Missing type.')
        if not operation_data.get('amount'):
            raise BrokenRulesError('Missing amount')

        if operation_data.setdefault('category_id', None) is not None:
            service = CategoriesService(self.connection)
            try:
                service.get_category_by_id(operation_data['category_id'])
            except DoesNotExistError:
                raise BrokenRulesError('Wrong id of category')

        if operation_data['type'] not in ('income', 'expenses'):
            raise BrokenRulesError('Wrong type of operation')
        self.check_amount(operation_data)

        date_format = self.get_format_of_date()
        operation_data['record_date'] = datetime.now(tz=None).strftime(date_format)
        if operation_data.get('operation_date') is None:
            operation_data['operation_date'] = operation_data['record_date']
        else:
            self.format_date(operation_data, date_format)

        operation_data.setdefault('description', None)

        operation_id = self._create_operation(operation_data)
        return self.get_operation(operation_id)

    def get_operation(self, operation_id):
        """
        Получение операции по её id

        :param operation_id: id операии
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
        operation = {
            key: row[key]
            for key in row.keys()
            if row[key] is not None
        }
        return operation

    def update_operation(self, operation_data, operation_id):
        """
        Обновляет данные у существующей операции

        :param operation_data: информация, на которую будет заменены поля, которые были отправлены
         (тип(если есть), сумма(если есть), описание(если есть), id категории(если есть), дата
         произведения операции)
        :param operation_id: id изменяемой операции

        :return: Изменённая операция
        """

        old_operation = self.get_operation(operation_id)

        if operation_data.get('type'):
            if operation_data['type'] not in ('income', 'expenses'):
                raise BrokenRulesError('Wrong type of operation')
            if operation_data['type'] != old_operation['type']:
                operation_data.setdefault('amount', -old_operation['amount'])
            self.check_amount(operation_data)

        if operation_data.get('category_id'):
            service_category = CategoriesService(self.connection)
            service_category.get_category_by_id(operation_data['category_id'])

        if operation_data.get('operation_date'):
            date_format = self.get_format_of_date()
            self.format_date(operation_data, date_format)

        self.update_row(
            table_name='operation',
            where='id',
            equals_to=operation_id,
            **operation_data
        )
        return self.get_operation(operation_id)

    def delete_operation(self, operation_id):
        """
        Удаляет операцию

        :param operation_id: id удаляемой операции
        """
        self.get_operation(operation_id)
        self.connection.execute(
            'DELETE FROM operation '
            'WHERE id = ?',
            (operation_id,),
        )

    @classmethod
    def check_amount(cls, operation):
        """
        Проверяет совбадение типа и суммы операции

        :param operation:
        :return:
        """
        if operation['type'] == 'income':
            if operation['amount'] < 0:
                raise BrokenRulesError('Income must be > 0')
        if operation['type'] == 'expenses':
            if operation['amount'] > 0:
                raise BrokenRulesError('Expenses must be < 0')

    @classmethod
    def get_format_of_date(cls):
        return '%Y-%m-%d %H:%M'

    @classmethod
    def format_date(cls, operation, date_format):
        try:
            operation['operation_date'] = datetime.strptime(
                operation['operation_date'],
                date_format
            )
        except ValueError:
            raise BrokenRulesError('Wrong format of date. He`s must be %Y-%m-%d %H:%M')

    def is_owner(self, user_id, operation_id):
        """
        Проверяет является ли пользователь создателем операции

        :param user_id: id пользователя
        :param operation_id: id операции
        :return: true/false является или нет
        """
        cur = self.connection.execute(
            'SELECT user_id '
            'FROM operation '
            'WHERE id = ?',
            (operation_id,),
        )
        row = cur.fetchone()
        return row is not None and (row['user_id']) == user_id
