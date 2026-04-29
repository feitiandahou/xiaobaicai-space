from enum import StrEnum


class AdminAction(StrEnum):
    CREATE_POST = "create_post"
    UPDATE_POST = "update_post"
    DELETE_POST = "delete_post"
    UPDATE_USER = "update_user"
    CHANGE_PASSWORD = "change_password"
    UPDATE_USER_STATUS = "update_user_status"
    CREATE_CATEGORY = "create_category"
    UPDATE_CATEGORY = "update_category"
    DELETE_CATEGORY = "delete_category"
    CREATE_TAG = "create_tag"
    UPDATE_TAG = "update_tag"
    DELETE_TAG = "delete_tag"
    UPSERT_SETTING = "upsert_setting"
    DELETE_SETTING = "delete_setting"