from app.core.config import Settings, settings


def test_database_url_is_built():
    assert settings.DB_PORT == 3306 or isinstance(settings.DB_PORT, int)
    assert isinstance(settings.DATABASE_URL, str)
    assert settings.DATABASE_URL.startswith("mysql+aiomysql://")
    assert "?charset=utf8mb4" in settings.DATABASE_URL


def test_db_echo_defaults_to_false() -> None:
    assert Settings.model_fields["DB_ECHO"].default is False


def test_cors_allowed_origins_supports_comma_separated_values() -> None:
    configured = Settings.model_validate(
        {
            "DB_USER": "root",
            "DB_PASSWORD": "password",
            "DB_HOST": "localhost",
            "DB_PORT": 3306,
            "DB_NAME": "xiaobaicai",
            "JWT_SECRET_KEY": "test-only-jwt-secret-key-with-32-plus-characters",
            "JWT_ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": 60,
            "CORS_ALLOWED_ORIGINS": "http://localhost:3000,http://127.0.0.1:3000",
        }
    )

    assert configured.CORS_ALLOWED_ORIGINS == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_auth_settings_are_available():
    assert isinstance(settings.JWT_SECRET_KEY, str)
    assert settings.JWT_SECRET_KEY
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0


def test_jwt_secret_key_is_required() -> None:
    assert Settings.model_fields["JWT_SECRET_KEY"].is_required() is True
