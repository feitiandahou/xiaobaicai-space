import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DB_USER: str = Field(min_length=1)
    DB_PASSWORD: str = Field(min_length=1)
    DB_HOST: str = Field(min_length=1)
    DB_PORT: int = Field(default=3306, ge=1, le=65535)
    DB_NAME: str = Field(min_length=1)
    DB_ECHO: bool = False
    JWT_SECRET_KEY: str = Field(min_length=32)
    JWT_ALGORITHM: str = Field(default="HS256", min_length=1)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, gt=0)
    CORS_ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(default_factory=list)

    @field_validator("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME", "JWT_SECRET_KEY", "JWT_ALGORITHM")
    @classmethod
    def _strip_required_strings(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_allowed_origins(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []
            if raw_value.startswith("["):
                parsed_value = json.loads(raw_value)
                if not isinstance(parsed_value, list):
                    raise ValueError("CORS_ALLOWED_ORIGINS must be a list or comma-separated string")
                return [str(item).strip() for item in parsed_value if str(item).strip()]
            return [item.strip() for item in raw_value.split(",") if item.strip()]
        raise ValueError("CORS_ALLOWED_ORIGINS must be a list or comma-separated string")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            "?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()  # pyright: ignore[reportCallIssue]
    except ValidationError as exc:
        raise RuntimeError(f"Invalid application settings: {exc}") from exc


settings = get_settings()