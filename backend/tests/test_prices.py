from datetime import date
from unittest.mock import patch

import pytest

from app.routers.prices import HourPrice, cheapest_window, fetch_prices


def _raw_hour(h, nok):
    # h+1 wraps past 23 → next day at 00:00 so Pydantic accepts the datetime.
    end_day = 28 if h < 23 else 29
    end_hour = (h + 1) % 24
    return {
        "NOK_per_kWh": nok,
        "EUR_per_kWh": nok / 10.0,
        "EXR": 10.0,
        "time_start": f"2026-05-28T{h:02d}:00:00+02:00",
        "time_end": f"2026-05-{end_day:02d}T{end_hour:02d}:00:00+02:00",
    }


def _hour(h, nok):
    return HourPrice.model_validate(_raw_hour(h, nok))


def test_cheapest_window_picks_lowest_average():
    # REQ-001: 4 consecutive hours with the lowest average NOK_per_kWh.
    prices = [_hour(h, nok) for h, nok in enumerate([2, 2, 0.5, 0.5, 0.5, 0.5, 3, 3])]
    w = cheapest_window(prices, window=4)
    assert w["start"] == prices[2].time_start.isoformat()
    assert w["end"] == prices[5].time_end.isoformat()
    assert w["avg_nok_per_kwh"] == 0.5
    assert w["hours"] == 4


def test_cheapest_window_returns_consecutive_hours_over_full_day():
    # REQ-001: window must be 4 *consecutive* hours, not the 4 cheapest hours overall.
    # Cheap singletons at non-adjacent positions must lose to a contiguous run.
    nok = [5.0] * 24
    # Two isolated cheap hours plus a contiguous cheap run of 4 starting at index 10.
    nok[1] = 0.1
    nok[20] = 0.1
    for i in range(10, 14):
        nok[i] = 1.0
    prices = [_hour(h, nok[h]) for h in range(24)]
    w = cheapest_window(prices)
    assert w["hours"] == 4
    assert w["start"] == prices[10].time_start.isoformat()
    assert w["end"] == prices[13].time_end.isoformat()
    assert w["avg_nok_per_kwh"] == 1.0


def test_cheapest_window_handles_short_series():
    assert cheapest_window([_hour(0, 1.0)], window=4) is None


def test_cheapest_window_default_is_four_hours():
    # REQ-001: default window length is 4 consecutive hours.
    prices = [_hour(h, 1.0) for h in range(24)]
    w = cheapest_window(prices)
    assert w["hours"] == 4


def test_get_prices_rejects_invalid_area(client):
    r = client.get("/api/prices?area=NO9")
    assert r.status_code == 400


def test_get_prices_returns_data(client):
    fake = [_raw_hour(h, h + 0.1) for h in range(24)]
    with patch("app.routers.prices.fetch_prices", return_value=fake):
        r = client.get("/api/prices?area=NO1")
    assert r.status_code == 200
    body = r.json()
    assert body["area"] == "NO1"
    assert len(body["prices"]) == 24
    assert body["cheapest_window"]["hours"] == 4
    # Cheapest 4-hour window should start at the first hour (lowest values).
    assert body["cheapest_window"]["start"] == body["prices"][0]["time_start"]


def test_fetch_prices_url_format(monkeypatch):
    captured = {}

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"[]"

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        return FakeResp()

    monkeypatch.setattr("app.routers.prices.urllib.request.urlopen", fake_urlopen)
    fetch_prices("NO2", date(2026, 1, 5))
    assert (
        captured["url"]
        == "https://www.hvakosterstrommen.no/api/v1/prices/2026/01-05_NO2.json"
    )


@pytest.mark.parametrize("area", ["NO1", "NO2", "NO3", "NO4", "NO5"])
def test_all_valid_areas_accepted(client, area):
    with patch(
        "app.routers.prices.fetch_prices",
        return_value=[_raw_hour(h, 1.0) for h in range(24)],
    ):
        r = client.get(f"/api/prices?area={area}")
    assert r.status_code == 200
