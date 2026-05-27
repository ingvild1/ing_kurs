# backend/AGENTS.md

## Test isolation
Tests must never touch `workshop.db`. Use the `client` fixture from [`tests/conftest.py`](tests/conftest.py) — it builds an in-memory SQLite engine (`StaticPool`, shared across threads) and overrides `get_db`. Do not wrap `TestClient(app)` in `with`: the lifespan would `create_all` against the real engine and create `workshop.db` at the repo root.
