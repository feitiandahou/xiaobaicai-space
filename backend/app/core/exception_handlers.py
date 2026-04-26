from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.post_service import (
    PostConflictError,
    PostNotFoundError,
    PostPermissionError,
    PostValidationError,
)
from app.services.user_service import (
    UserAuthenticationError,
    UserConflictError,
    UserInactiveError,
    UserNotFoundError,
    UserPermissionError,
)


def _json_error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PostNotFoundError)
    @app.exception_handler(UserNotFoundError)
    async def handle_not_found(_: Request, exc: Exception) -> JSONResponse:
        return _json_error(404, str(exc))

    @app.exception_handler(PostConflictError)
    @app.exception_handler(UserConflictError)
    async def handle_conflict(_: Request, exc: Exception) -> JSONResponse:
        return _json_error(409, str(exc))

    @app.exception_handler(PostValidationError)
    async def handle_validation(_: Request, exc: PostValidationError) -> JSONResponse:
        return _json_error(422, str(exc))

    @app.exception_handler(PostPermissionError)
    @app.exception_handler(UserPermissionError)
    @app.exception_handler(UserInactiveError)
    async def handle_forbidden(_: Request, exc: Exception) -> JSONResponse:
        return _json_error(403, str(exc))

    @app.exception_handler(UserAuthenticationError)
    async def handle_authentication(_: Request, exc: UserAuthenticationError) -> JSONResponse:
        return _json_error(401, str(exc))