from collections.abc import Mapping

from app.core.error_codes import ErrorCode


class AppError(Exception):
    status_code = 500
    code = ErrorCode.APP_ERROR.value

    def __init__(self, detail: str, *, code: str | None = None, headers: Mapping[str, str] | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.code = code or self.__class__.code
        self.headers = dict(headers) if headers is not None else None


class NotFoundError(AppError):
    status_code = 404
    code = ErrorCode.NOT_FOUND.value


class ConflictError(AppError):
    status_code = 409
    code = ErrorCode.CONFLICT.value


class ValidationAppError(AppError):
    status_code = 422
    code = ErrorCode.VALIDATION_ERROR.value


class PermissionDeniedError(AppError):
    status_code = 403
    code = ErrorCode.PERMISSION_DENIED.value


class AuthenticationRequiredError(AppError):
    status_code = 401
    code = ErrorCode.AUTHENTICATION_REQUIRED.value

    def __init__(self, detail: str, *, code: str | None = None, headers: Mapping[str, str] | None = None) -> None:
        super().__init__(
            detail,
            code=code,
            headers=headers or {"WWW-Authenticate": "Bearer"},
        )