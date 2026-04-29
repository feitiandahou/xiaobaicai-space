# Assemblers

Purpose: convert persistence objects into stable read-side DTOs.

Allowed dependencies:
- `app.models.*`
- `app.core.read_models`
- Python standard library only

Forbidden dependencies:
- `app.api.*`
- `app.presenters.*`
- `app.services.commands.*`
- `app.services.queries.*`
- database sessions or SQL execution

Rules:
- Assemblers are pure functions.
- Assemblers must not commit, query, or mutate ORM objects.
- If a DTO needs aggregated fields, the caller computes the values and passes them in.