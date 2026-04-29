from fastapi import Request

from app.services.commands.audit import AuditContext


def build_audit_context(request: Request) -> AuditContext:
    return AuditContext(
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        os_info=request.headers.get("sec-ch-ua-platform") or request.headers.get("x-client-os"),
    )