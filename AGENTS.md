# AGENTS.md

## Schema changes
No Alembic. After editing `backend/app/models.py`, run `rm -f workshop.db` — next boot recreates schema from models. Skip this and you'll hit "no such column/table" at request time.

## No JS package manager
No `package.json`, npm, or bundler — load-bearing. Add JS to `frontend/app.js`, or vendor one static file under `frontend/vendor/` per `frontend/README.md` (pin version, record SHA-256, header comment).

## Code principles
Full rationale: [`docs/code-principles.md`](docs/code-principles.md).
- Subtract code first; smallest diff wins.
- Comments explain *why*, not *what*.
- Validate at boundaries (Pydantic/SQLAlchemy at HTTP/DB edge); trust internal code.
- No premature abstraction — wait for the third use.
- Small functions named for intent; "and" in the name means split it.

## Subdirs
- `backend/AGENTS.md` — test isolation.
