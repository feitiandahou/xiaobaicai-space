from __future__ import annotations

import json
import logging
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


REQUEST_ID_HEADER = "X-Request-ID"
TRACE_ID_HEADER = "X-Trace-ID"

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
_trace_id_ctx: ContextVar[str | None] = ContextVar("trace_id", default=None)

_DEFAULT_LOG_RECORD_KEYS = set(logging.makeLogRecord({}).__dict__.keys())


def get_request_id() -> str | None:
    return _request_id_ctx.get()


def get_trace_id() -> str | None:
    return _trace_id_ctx.get()


def bind_request_context(*, request_id: str, trace_id: str) -> tuple[Token[str | None], Token[str | None]]:
    return _request_id_ctx.set(request_id), _trace_id_ctx.set(trace_id)


def reset_request_context(tokens: tuple[Token[str | None], Token[str | None]]) -> None:
    request_token, trace_token = tokens
    _request_id_ctx.reset(request_token)
    _trace_id_ctx.reset(trace_token)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = get_request_id()
        if not hasattr(record, "trace_id"):
            record.trace_id = get_trace_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None) or get_request_id(),
            "trace_id": getattr(record, "trace_id", None) or get_trace_id(),
        }

        for key, value in record.__dict__.items():
            if key in _DEFAULT_LOG_RECORD_KEYS or key in payload or key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True, default=str)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def configure_logging() -> None:
    app_logger = logging.getLogger("app")
    if any(getattr(handler, "_xiaobaicai_structured", False) for handler in app_logger.handlers):
        return

    handler = logging.StreamHandler()
    handler._xiaobaicai_structured = True  # type: ignore[attr-defined]
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestContextFilter())

    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(handler)
    app_logger.propagate = False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid4().hex
        trace_id = request.headers.get(TRACE_ID_HEADER) or request_id
        request.state.request_id = request_id
        request.state.trace_id = trace_id

        tokens = bind_request_context(request_id=request_id, trace_id=trace_id)
        started_at = perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            response.headers.setdefault(REQUEST_ID_HEADER, request_id)
            response.headers.setdefault(TRACE_ID_HEADER, trace_id)
            get_logger("app.http").info(
                "http_request_completed",
                extra={
                    "event": "http_request_completed",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "client_ip": request.client.host if request.client else None,
                    "request_id": request_id,
                    "trace_id": trace_id,
                },
            )
            return response
        finally:
            reset_request_context(tokens)