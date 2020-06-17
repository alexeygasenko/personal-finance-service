class BaseService:
    def __init__(self, connection):
        self.connection = connection

    @classmethod
    def make_placeholders(cls, n):
        return ', '.join('?' for _ in range(n))

    @classmethod
    def make_update_fields(cls, fields):
        return ', '.join(f'{field} = ?' for field in fields)