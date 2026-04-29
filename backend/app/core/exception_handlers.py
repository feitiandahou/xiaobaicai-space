from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.error_codes import ErrorCode
from app.core.errors import AppError
from app.core.observability import get_logger
from app.presenters import present_error_response, present_validation_error_response
from app.schemas.error import ErrorResponse


def _json_response(status_code: int, content: dict[str, object], *, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=content, headers=headers)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        get_logger("app.errors").warning(
            "app_error",
            extra={
                "event": "app_error",
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "error_code": exc.code,
                "detail": exc.detail,
            },
        )
        payload = present_error_response(exc)
        return _json_response(exc.status_code, payload.model_dump(), headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        get_logger("app.errors").warning(
            "request_validation_error",
            extra={
                "event": "request_validation_error",
                "path": request.url.path,
                "method": request.method,
                "status_code": 422,
                "errors_count": len(exc.errors()),
            },
        )
        payload = present_validation_error_response(exc)
        return _json_response(422, payload.model_dump())

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        get_logger("app.errors").exception(
            "unhandled_exception",
            extra={
                "event": "unhandled_exception",
                "path": request.url.path,
                "method": request.method,
                "status_code": 500,
                "error_type": exc.__class__.__name__,
            },
        )
        payload = ErrorResponse(code=ErrorCode.APP_ERROR.value, detail="Internal server error")
        return _json_response(500, payload.model_dump())