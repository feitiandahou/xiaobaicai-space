# Command Services

Purpose: handle write-side use cases.

Allowed dependencies:
- `app.models.*`
- `app.assemblers.*`
- `app.core.*`
- `app.services.queries.*` for shared loaders, permissions, and error types
- SQLAlchemy write APIs

Forbidden dependencies:
- `app.presenters.*`
- `app.api.*`

Rules:
- Commands own validation, mutation, transaction boundaries, and side effects.
- Commands may call query helpers, but command orchestration stays on the write side.
- Commands should emit audit records for successful admin writes.
- Audit failure must not invalidate a business write that has already committed.