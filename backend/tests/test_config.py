from app.core.config import settings


def test_database_url_is_built():
    assert settings.DB_PORT == 3306 or isinstance(settings.DB_PORT, int)
    assert isinstance(settings.DATABASE_URL, str)
    assert settings.DATABASE_URL.startswith("mysql+aiomysql://")
    assert "?charset=utf8mb4" in settings.DATABASE_URL


def test_auth_settings_are_available():
    assert isinstance(settings.JWT_SECRET_KEY, str)
    assert settings.JWT_SECRET_KEY
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0