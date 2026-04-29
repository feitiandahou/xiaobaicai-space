from fastapi.exceptions import RequestValidationError

from app.core.errors import AppError
from app.schemas.error import ErrorResponse, ValidationErrorItem, ValidationErrorResponse


def present_error_response(error: AppError) -> ErrorResponse:
    return ErrorResponse(code=error.code, detail=error.detail)


def present_validation_error_response(error: RequestValidationError) -> ValidationErrorResponse:
    return ValidationErrorResponse(
        code="validation_error",
        detail="Validation failed",
        errors=[
            ValidationErrorItem(
                loc=list(item.get("loc", ())),
                msg=item.get("msg", "Invalid request"),
                type=item.get("type", "validation_error"),
            )
            for item in error.errors()
        ],
    )