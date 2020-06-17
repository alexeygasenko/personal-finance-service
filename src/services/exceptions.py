class ServiceError(Exception):
    code = 400

    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.error = {
            'message': message,
        }


class ConflictError(ServiceError):
    code = 409


class DoesNotExistError(ServiceError):
    code = 404


class BrokenRulesError(ServiceError):
    code = 422
