import json
import urllib.error
import urllib.request
from datetime import date as date_cls, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ValidationError

router = APIRouter()

PRICE_AREAS = {"NO1", "NO2", "NO3", "NO4", "NO5"}
UPSTREAM = "https://www.hvakosterstrommen.no/api/v1/prices/{year}/{month:02d}-{day:02d}_{area}.json"
CHARGE_WINDOW_HOURS = 4
OSLO = ZoneInfo("Europe/Oslo")


class HourPrice(BaseModel):
    NOK_per_kWh: float
    time_start: datetime
    time_end: datetime


def fetch_prices(area: str, date: date_cls) -> list[dict]:
    url = UPSTREAM.format(year=date.year, month=date.month, day=date.day, area=area)
    req = urllib.request.Request(
        url, headers={"User-Agent": "agentic-coding-workshop/0.1"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def cheapest_window(
    prices: list[HourPrice], window: int = CHARGE_WINDOW_HOURS
) -> dict | None:
    # Cheapest `window` consecutive hours by average NOK/kWh.
    if len(prices) < window:
        return None
    best_start, best_avg = 0, float("inf")
    for i in range(len(prices) - window + 1):
        avg = sum(p.NOK_per_kWh for p in prices[i : i + window]) / window
        if avg < best_avg:
            best_start, best_avg = i, avg
    return {
        "start": prices[best_start].time_start.isoformat(),
        "end": prices[best_start + window - 1].time_end.isoformat(),
        "avg_nok_per_kwh": round(best_avg, 4),
        "hours": window,
    }


@router.get("/prices")
def get_prices(area: str = Query("NO1")) -> dict:
    if area not in PRICE_AREAS:
        raise HTTPException(
            400, f"area must be one of: {', '.join(sorted(PRICE_AREAS))}"
        )
    now = datetime.now(OSLO)
    today = now.date()
    try:
        raw = fetch_prices(area, today)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise HTTPException(503, "Prices not yet published for today") from e
        raise HTTPException(502, f"Upstream error: {e.code}") from e
    except urllib.error.URLError as e:
        raise HTTPException(502, f"Upstream unreachable: {e.reason}") from e

    try:
        prices = [HourPrice.model_validate(p) for p in raw]
    except ValidationError as e:
        raise HTTPException(502, "upstream returned unexpected shape") from e

    current_hour_idx = None
    for i, p in enumerate(prices):
        if p.time_start <= now < p.time_end:
            current_hour_idx = i
            break

    return {
        "area": area,
        "date": today.isoformat(),
        "prices": prices,
        "cheapest_window": cheapest_window(prices),
        "current_hour_index": current_hour_idx,
    }
