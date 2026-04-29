from __future__ import annotations

import asyncio
import logging
from types import SimpleNamespace
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_actions import AdminAction
from app.core.errors import NotFoundError
from app.core.exception_handlers import register_exception_handlers
from app.core.observability import (
    JsonFormatter,
    REQUEST_ID_HEADER,
    TRACE_ID_HEADER,
    RequestLoggingMiddleware,
)
from app.models.user import User
from app.services.commands.audit import AuditContext, record_admin_action


class FakeLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, str, dict[str, object] | None]] = []

    def info(self, message: str, *, extra: dict[str, object] | None = None) -> None:
        self.records.append(("info", message, extra))

    def warning(self, message: str, *, extra: dict[str, object] | None = None) -> None:
        self.records.append(("warning", message, extra))

    def exception(self, message: str, *, extra: dict[str, object] | None = None) -> None:
        self.records.append(("exception", message, extra))


def test_json_formatter_outputs_structured_payload() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-1"
    record.trace_id = "trace-1"
    record.event = "unit_test"

    payload = formatter.format(record)

    assert '"message": "hello"' in payload
    assert '"request_id": "req-1"' in payload
    assert '"trace_id": "trace-1"' in payload
    assert '"event": "unit_test"' in payload


def test_request_logging_middleware_sets_headers_and_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/ping")
    async def ping() -> JSONResponse:
        return JSONResponse({"ok": True})

    fake_logger = FakeLogger()
    monkeypatch.setattr("app.core.observability.get_logger", lambda name: fake_logger)

    with TestClient(app) as client:
        response = client.get("/ping", headers={REQUEST_ID_HEADER: "req-123", TRACE_ID_HEADER: "trace-456"})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "req-123"
    assert response.headers[TRACE_ID_HEADER] == "trace-456"
    duration_payload = fake_logger.records[0][2]
    assert duration_payload is not None
    assert fake_logger.records == [
        (
            "info",
            "http_request_completed",
            {
                "event": "http_request_completed",
                "method": "GET",
                "path": "/ping",
                "status_code": 200,
                "duration_ms": duration_payload["duration_ms"],
                "client_ip": "testclient",
                "request_id": "req-123",
                "trace_id": "trace-456",
            },
        )
    ]


def test_exception_handlers_log_app_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/missing")
    async def missing() -> JSONResponse:
        raise NotFoundError("missing resource")

    fake_logger = FakeLogger()
    monkeypatch.setattr("app.core.exception_handlers.get_logger", lambda name: fake_logger)

    with TestClient(app) as client:
        response = client.get("/missing")

    assert response.status_code == 404
    assert response.json() == {"code": "not_found", "detail": "missing resource"}
    assert fake_logger.records == [
        (
            "warning",
            "app_error",
            {
                "event": "app_error",
                "path": "/missing",
                "method": "GET",
                "status_code": 404,
                "error_code": "not_found",
                "detail": "missing resource",
            },
        )
    ]


def test_exception_handlers_log_unhandled_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom() -> JSONResponse:
        raise RuntimeError("boom")

    fake_logger = FakeLogger()
    monkeypatch.setattr("app.core.exception_handlers.get_logger", lambda name: fake_logger)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {"code": "app_error", "detail": "Internal server error"}
    assert fake_logger.records == [
        (
            "exception",
            "unhandled_exception",
            {
                "event": "unhandled_exception",
                "path": "/boom",
                "method": "GET",
                "status_code": 500,
                "error_type": "RuntimeError",
            },
        )
    ]


def test_record_admin_action_logs_success(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = FakeLogger()

    async def fake_record_admin_log(db, payload, *, actor):
        return None

    monkeypatch.setattr("app.services.commands.audit.get_logger", lambda name: fake_logger)
    monkeypatch.setattr("app.services.commands.audit.record_admin_log", fake_record_admin_log)

    actor = cast(object, SimpleNamespace(id=1, role="admin"))

    asyncio.run(
        record_admin_action(
            cast(AsyncSession, object()),
            actor=cast(User, actor),
            action=AdminAction.UPDATE_POST,
            detail="Updated post 1",
            audit_context=AuditContext(ip_address="127.0.0.1"),
        )
    )

    assert fake_logger.records == [
        (
            "info",
            "admin_audit_record_requested",
            {
                "event": "admin_audit_record_requested",
                "actor_id": 1,
                "action": "update_post",
                "detail": "Updated post 1",
                "ip_address": "127.0.0.1",
            },
        ),
        (
            "info",
            "admin_audit_recorded",
            {
                "event": "admin_audit_recorded",
                "actor_id": 1,
                "action": "update_post",
                "detail": "Updated post 1",
            },
        ),
    ]


def test_record_admin_action_logs_failure_and_rolls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = FakeLogger()
    rollback_called = False

    async def failing_record_admin_log(db, payload, *, actor):
        raise RuntimeError("audit failure")

    class FakeDb:
        async def rollback(self) -> None:
            nonlocal rollback_called
            rollback_called = True

    monkeypatch.setattr("app.services.commands.audit.get_logger", lambda name: fake_logger)
    monkeypatch.setattr("app.services.commands.audit.record_admin_log", failing_record_admin_log)

    actor = cast(object, SimpleNamespace(id=1, role="admin"))
    asyncio.run(
        record_admin_action(
            cast(AsyncSession, FakeDb()),
            actor=cast(User, actor),
            action=AdminAction.UPDATE_POST,
            detail="Updated post 1",
            audit_context=AuditContext(ip_address="127.0.0.1"),
        )
    )

    assert rollback_called is True
    assert fake_logger.records[-1] == (
        "exception",
        "admin_audit_failed",
        {
            "event": "admin_audit_failed",
            "actor_id": 1,
            "action": "update_post",
            "detail": "Updated post 1",
        },
    )


def test_record_admin_action_allows_admin_override_for_self_role_change(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_logger = FakeLogger()

    async def fake_record_admin_log(db, payload, *, actor):
        return None

    monkeypatch.setattr("app.services.commands.audit.get_logger", lambda name: fake_logger)
    monkeypatch.setattr("app.services.commands.audit.record_admin_log", fake_record_admin_log)

    actor = cast(object, SimpleNamespace(id=1, role="user"))

    asyncio.run(
        record_admin_action(
            cast(AsyncSession, object()),
            actor=cast(User, actor),
            action=AdminAction.UPDATE_USER,
            detail="Self-demoted admin user 1",
            actor_role_override="admin",
        )
    )

    assert fake_logger.records[-1] == (
        "info",
        "admin_audit_recorded",
        {
            "event": "admin_audit_recorded",
            "actor_id": 1,
            "action": "update_user",
            "detail": "Self-demoted admin user 1",
        },
    )