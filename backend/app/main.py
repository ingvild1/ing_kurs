from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401 — register tables on Base before create_all
from .database import REPO_ROOT, Base, engine
from .routers import health, pings, prices

FRONTEND_DIR = REPO_ROOT / "frontend"
if not FRONTEND_DIR.is_dir():
    # Fail loudly at import time rather than serving 404s from a silently-empty mount.
    raise RuntimeError(f"frontend directory not found at {FRONTEND_DIR}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # REQ-013 — create tables when the application starts (not at import time,
    # so tests that override the DB dependency never touch workshop.db).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Agentic Coding Workshop", lifespan=lifespan)

# REQ-015 — API endpoints under /api/
app.include_router(health.router, prefix="/api")
app.include_router(pings.router, prefix="/api")
app.include_router(prices.router, prefix="/api")

# REQ-014 — mount frontend at /, serving index.html as default.
# MUST come AFTER the API routers, otherwise the StaticFiles mount swallows /api/* requests.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
