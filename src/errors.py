from enum import StrEnum


class ErrorCodes(StrEnum):
    UNKNOWN_ERROR = 'UNKNOWN_ERROR'
    AUTH_ERROR = 'AUTH_ERROR'


class BaseError(Exception):
    """Base error class"""

    default_msg = ''
    error_code = ErrorCodes.UNKNOWN_ERROR

    def __init__(self, *args):
        if '%s' in self.default_msg:
            msg = self.default_msg % args
        else:
            try:
                msg = f'{args[0]}'
            except IndexError:
                msg = None
        self.msg = msg or self.default_msg

    def __str__(self) -> str:
        return f'{self.error_code}: {self.msg}'


class AuthError(BaseError):
    """Authorization/Authentication error"""

    default_msg = 'Auth error'
    error_code = ErrorCodes.AUTH_ERROR
