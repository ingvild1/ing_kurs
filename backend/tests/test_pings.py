from datetime import datetime, timedelta

from app.models import Ping


def test_post_then_get_pings(client):
    post = client.post("/api/pings")
    assert post.status_code == 201
    body = post.json()
    assert "id" in body
    assert "created_at" in body

    get = client.get("/api/pings")
    assert get.status_code == 200
    arr = get.json()
    assert len(arr) == 1
    assert "id" in arr[0]
    assert "created_at" in arr[0]


def test_get_pings_orders_newest_first(client, db_session):
    # Insert via the session with explicit created_at so ordering is
    # deterministic (SQLite's current_timestamp default has only
    # second-level resolution, which can tie for back-to-back POSTs).
    base = datetime(2026, 5, 16, 12, 0, 0)
    db_session.add_all(
        [
            Ping(created_at=base),
            Ping(created_at=base + timedelta(seconds=10)),
            Ping(created_at=base + timedelta(seconds=5)),
        ]
    )
    db_session.commit()

    arr = client.get("/api/pings").json()
    timestamps = [row["created_at"] for row in arr]
    assert timestamps == sorted(timestamps, reverse=True)
