from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import AppError
from app.presenters import present_error_response, present_validation_error_response


def _json_response(status_code: int, content: dict[str, object], *, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=content, headers=headers)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        payload = present_error_response(exc)
        return _json_response(exc.status_code, payload.model_dump(), headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        payload = present_validation_error_response(exc)
        return _json_response(422, payload.model_dump())