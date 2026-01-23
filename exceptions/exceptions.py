# exceptions/exceptions.py
from exceptions.error_messages import ErrorMessage, ERROR_STATUS_CODE


class AppException(Exception):
    def __init__(self, error: ErrorMessage):
        self.message = error.value
        self.status_code = ERROR_STATUS_CODE[error]

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}"
