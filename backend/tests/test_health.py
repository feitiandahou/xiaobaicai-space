from fastapi.testclient import TestClient

from app import main


def test_health_live_returns_process_alive(monkeypatch) -> None:
    async def healthy_db() -> None:
        return None

    monkeypatch.setattr(main, "check_database_readiness", healthy_db)

    with TestClient(main.app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_ready_returns_dependency_status(monkeypatch) -> None:
    async def healthy_db() -> None:
        return None

    monkeypatch.setattr(main, "check_database_readiness", healthy_db)

    with TestClient(main.app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ok"},
    }


def test_health_ready_returns_503_when_database_unavailable(monkeypatch) -> None:
    async def healthy_db() -> None:
        return None

    async def failing_db() -> None:
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(main, "check_database_readiness", healthy_db)

    with TestClient(main.app) as client:
        monkeypatch.setattr(main, "check_database_readiness", failing_db)
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "unavailable"},
    }


def test_health_alias_matches_readiness(monkeypatch) -> None:
    async def healthy_db() -> None:
        return None

    monkeypatch.setattr(main, "check_database_readiness", healthy_db)

    with TestClient(main.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ok"},
    }


def test_app_startup_still_allows_liveness_when_database_unavailable(monkeypatch) -> None:
    async def failing_db() -> None:
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(main, "check_database_readiness", failing_db)

    with TestClient(main.app) as client:
        live_response = client.get("/health/live")
        ready_response = client.get("/health/ready")

    assert live_response.status_code == 200
    assert live_response.json() == {"status": "ok"}
    assert ready_response.status_code == 503
    assert ready_response.json() == {
        "status": "not_ready",
        "checks": {"database": "unavailable"},
    }