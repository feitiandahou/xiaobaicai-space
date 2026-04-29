from enum import StrEnum


class ErrorCode(StrEnum):
    APP_ERROR = "app_error"
    AUTHENTICATION_REQUIRED = "authentication_required"
    INVALID_TOKEN = "invalid_token"
    PERMISSION_DENIED = "permission_denied"
    ADMIN_ACCESS_REQUIRED = "admin_access_required"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    VALIDATION_ERROR = "validation_error"

    POST_NOT_FOUND = "post_not_found"
    POST_CONFLICT = "post_conflict"
    POST_VALIDATION_ERROR = "post_validation_error"
    POST_PERMISSION_DENIED = "post_permission_denied"

    USER_NOT_FOUND = "user_not_found"
    USER_CONFLICT = "user_conflict"
    USER_PERMISSION_DENIED = "user_permission_denied"
    USER_AUTHENTICATION_FAILED = "user_authentication_failed"
    USER_INACTIVE = "user_inactive"