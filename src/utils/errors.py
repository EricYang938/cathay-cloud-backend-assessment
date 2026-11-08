class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class MissingTask(ApiError):
    def __init__(self):
        super().__init__(404, "NOT_FOUND", "Task not found")
