from typing import Any

from app.core.error_codes import ErrorCode
from app.schemas.error import ErrorResponse, ValidationErrorResponse


_ERROR_RESPONSE_DEFINITIONS = {
    401: (
        ErrorResponse,
        "Authentication failed or missing credentials",
        {"code": ErrorCode.AUTHENTICATION_REQUIRED.value, "detail": "Authentication required"},
    ),
    403: (
        ErrorResponse,
        "Permission denied",
        {"code": ErrorCode.PERMISSION_DENIED.value, "detail": "Permission denied"},
    ),
    404: (
        ErrorResponse,
        "Resource not found",
        {"code": ErrorCode.NOT_FOUND.value, "detail": "Resource not found"},
    ),
    409: (
        ErrorResponse,
        "Resource conflict",
        {"code": ErrorCode.CONFLICT.value, "detail": "Resource conflict"},
    ),
    422: (
        ValidationErrorResponse,
        "Request validation failed",
        {
            "code": ErrorCode.VALIDATION_ERROR.value,
            "detail": "Validation failed",
            "errors": [
                {
                    "loc": ["body", "field_name"],
                    "msg": "Field is required",
                    "type": "missing",
                }
            ],
        },
    ),
}


def build_error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    responses: dict[int | str, dict[str, Any]] = {}
    for status_code in status_codes:
        model, description, example = _ERROR_RESPONSE_DEFINITIONS[status_code]
        responses[status_code] = {
            "model": model,
            "description": description,
            "content": {
                "application/json": {
                    "example": example,
                }
            },
        }
    return responses