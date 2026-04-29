# Query Services

Purpose: handle read-side use cases.

Allowed dependencies:
- `app.models.*`
- `app.assemblers.*`
- `app.core.*`
- SQLAlchemy query APIs

Forbidden dependencies:
- `app.presenters.*`
- `app.api.*`
- write-side transaction orchestration

Rules:
- Queries return read DTOs or primitive read results.
- Queries own read permission checks and read filtering.
- Queries may expose low-level record loaders for command reuse.
- Queries must not perform business writes.