from datetime import datetime
from .base import BaseService
from .categories import CategoriesService
from .exceptions import (
    DoesNotExistError,
    BrokenRulesError
)
from database import db


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
        operation_data['amount'] = abs(operation_data['amount'])
        if operation_data.setdefault('category_id', None) is not None:
            service = CategoriesService(self.connection)
            try:
                service.get_category_by_id(operation_data['category_id'])
            except DoesNotExistError:
                raise BrokenRulesError('Wrong id of category')

        if operation_data['type'] not in ('income', 'expenses'):
            raise BrokenRulesError('Wrong type of operation')

        operation_data['record_date'] = datetime.now(tz=None).strftime('%Y-%m-%d %H:%M')
        operation_data.setdefault('operation_date', operation_data['record_date'])
        operation_data.setdefault('description', None)

        operation_data['id'] = self._create_operation(operation_data)
        return operation_data

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
        if operation_data.get('type') not in ('income', 'expenses', None):
            raise BrokenRulesError('Wrong type of operation')

        if operation_data.get('category_id'):
            service_category = CategoriesService(self.connection)
            service_category.get_category_by_id(operation_data['category_id'])
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
