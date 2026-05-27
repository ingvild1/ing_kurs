"""Skeleton for new backend test files. Copy to `test_<module>.py` and adapt.

Pytest does not collect files whose name doesn't match `test_*.py` or `*_test.py`,
so this template is inert as-is — it will not run.

Conventions used in this template:

- Request the `client` fixture from conftest.py — never instantiate `TestClient`
  directly. The fixture wires the in-memory SQLite engine and the dependency
  override (see `backend/tests/conftest.py` for why).
- One test function per behavior. Name it after what's verified, not after the
  requirement ID: `test_create_ping_returns_id`, not `test_req_007`.
- Add a `# REQ-xxx` comment as the first line inside the function for
  traceability back to the EARS spec.
- For requirements that are not yet implemented, mark the test with
  `@pytest.mark.xfail(reason="REQ-xxx: not yet implemented")`.
"""

import pytest


def test_describes_what_is_verified(client):
    # REQ-xxx
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.xfail(reason="REQ-yyy: not yet implemented")
def test_describes_pending_behavior(client):
    # REQ-yyy
    response = client.post("/api/example", json={"value": 1})
    assert response.status_code == 201
