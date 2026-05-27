# Agentic Coding Workshop

A minimal template repository for the agentic-coding course. Get from `git clone` to a running FastAPI + SQLite + vanilla-JS app in under 60 seconds. No Node, no Docker, no `make`, no build step, no runtime network calls.

It ships one end-to-end smoke-test feature (`Ping`) that exercises every layer — env, web framework, database, static-file serving, frontend→backend call — so you can verify the environment works before you start building.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — the Python package manager. Installs Python 3.13 automatically using the version pinned in `.python-version`.
- `git`.
- A modern browser to view the app.
- [agent-browser](https://github.com/vercel-labs/agent-browser) — browser-automation CLI used by `/ws-gogogo` for end-to-end frontend verification. Required only if you'll work on specs involving UI changes; backend-only work doesn't need it.

No Node, no Docker, no global Python, no `make`, no JS package manager.

## Platform setup

### macOS

```bash
brew install uv git agent-browser
agent-browser install   # downloads Chrome for Testing; one-time
```

If you don't use Homebrew, follow the [uv install guide](https://docs.astral.sh/uv/getting-started/installation/) and install `git` via Xcode Command Line Tools (`xcode-select --install`). For `agent-browser` alternatives, see the [project README](https://github.com/vercel-labs/agent-browser).

### Linux / Windows (WSL2)

On Windows 11, run all commands inside WSL2 — we recommend the Ubuntu distribution. (Native PowerShell will also work because every command below is just `uv run …`, but WSL2 keeps the experience uniform with macOS/Linux.)

Debian / Ubuntu / WSL2 Ubuntu:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo apt update && sudo apt install -y git
```

Fedora: `sudo dnf install git`, then install uv with the same `curl` command above.
Arch: `sudo pacman -S git`, then install uv with the same `curl` command above.

If you'll use `/ws-gogogo` for frontend verification, also install `agent-browser`. The simplest path is Cargo (requires the Rust toolchain):

```bash
cargo install agent-browser
agent-browser install
```

For alternative install methods (Homebrew on Linux, npm, building from source), see the [agent-browser README](https://github.com/vercel-labs/agent-browser).

## Setup

```bash
git clone <your-fork-url>
cd agentic-coding-workshop
uv sync
```

`uv sync` resolves dependencies from `uv.lock` and creates a local `.venv/`. Expect under 30 seconds on a warm cache.

## Run the dev server

```bash
uv run uvicorn app.main:app --reload --app-dir backend --port 8000
```

Then open <http://localhost:8000> in a browser. You should see the page render with backend health = `ok` and a "Send ping" button.

## Run the tests

```bash
uv run pytest backend/tests/
```

Runs the backend pytest suite against an in-memory SQLite database (your local `workshop.db` is untouched). Expect under 5 seconds.

## Lint

```bash
uv run ruff check .
uv run ruff format --check .
```

Both must be clean.

## Warm-up exercise

New to MCP? Before the main workshop, try the five-minute warm-up in
[`docs/warmup-mcp-server.md`](docs/warmup-mcp-server.md) — it walks you through
connecting Claude Code to an MCP server.

## Reset the database

```bash
rm -f workshop.db
```

Deletes the local `workshop.db` file at the repository root. The app will recreate the schema on next boot via `Base.metadata.create_all`.

## Folder structure

```
backend/
  app/
    main.py          # FastAPI app: routers, StaticFiles mount, create_all on startup
    database.py      # SQLAlchemy engine, session, get_db dependency
    models.py        # SQLAlchemy ORM models (Ping)
    schemas.py       # Pydantic response schemas
    routers/
      health.py      # GET /api/health
      pings.py       # POST /api/pings, GET /api/pings
  tests/
    conftest.py      # in-memory SQLite + dependency override
    test_health.py
    test_pings.py
frontend/
  index.html         # served at /
  app.js             # frontend logic — fetch /api/health, /api/pings
  vendor/
    tailwind.js      # vendored @tailwindcss/browser v4.3.0 (SHA-256 in header)
  README.md          # frontend-specific notes
pyproject.toml       # Python project + dep + tool config
uv.lock              # resolved dependency graph
workshop.db           # SQLite database at repo root (created on first run; gitignored)
LICENSE
CLAUDE.md            # notes for Claude Code agents working in this repo
```

## SQLite database location

The runtime database lives at `./workshop.db` (repo root). It is created on first app boot. It is in `.gitignore` — never commit it.

## Schema-change workflow

This template uses `Base.metadata.create_all` rather than Alembic migrations. After modifying any SQLAlchemy model in `backend/app/models.py`:

```bash
rm -f workshop.db
```

This deletes the database. The next time the app boots, it recreates the schema from the current models. You will lose any local data. Once data persistence matters, swap in Alembic — see the course materials for a later lesson.
