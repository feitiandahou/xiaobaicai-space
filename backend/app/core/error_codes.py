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

    CATEGORY_NOT_FOUND = "category_not_found"
    CATEGORY_CONFLICT = "category_conflict"
    CATEGORY_PERMISSION_DENIED = "category_permission_denied"
    CATEGORY_VALIDATION_ERROR = "category_validation_error"

    TAG_NOT_FOUND = "tag_not_found"
    TAG_CONFLICT = "tag_conflict"
    TAG_PERMISSION_DENIED = "tag_permission_denied"

    SETTING_NOT_FOUND = "setting_not_found"
    SETTING_CONFLICT = "setting_conflict"
    SETTING_PERMISSION_DENIED = "setting_permission_denied"

    ADMIN_LOG_NOT_FOUND = "admin_log_not_found"
    ADMIN_LOG_PERMISSION_DENIED = "admin_log_permission_denied"