import os
from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Settings:
    #Database settings
    DB_USER: str = _require_env("DB_USER")
    DB_PASSWORD: str = _require_env("DB_PASSWORD")
    DB_HOST: str = _require_env("DB_HOST")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_NAME: str = _require_env("DB_NAME")
    DB_ECHO: bool = os.getenv("DB_ECHO", "true").lower() == "true"
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "dev-only-change-me-please-override-with-a-long-random-secret-key",
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            "?charset=utf8mb4"
        )


settings = Settings()