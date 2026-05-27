# Template Repository — Initial Setup

> Bare-bones template repo that gets course participants from `git clone` to a running FastAPI + SQLite + vanilla-JS app in under 60 seconds, with no Node, no Docker, no build step, and no runtime network calls. Includes a single end-to-end smoke-test feature (`Ping`) that exercises every layer so participants can verify their environment is working before they start building.

**Type:** New feature
**System:** Template repository (agentic-coding-workshop)
**Date:** 2026-05-16

## Context

This template will be used by participants in an agentic-coding course as the starting point for their own repos (via GitHub's "Use this template" flow). The priority is **speed-to-first-success and zero environmental friction** over production-grade polish. The repository contains scaffolding for a Python backend, a vanilla JS frontend, a SQLite database, and a test suite — plus one minimal end-to-end feature (`Ping`) whose sole purpose is to prove on day one that every layer (env, web framework, database, static-file serving, frontend→backend call) works correctly. The `Ping` feature is intentionally named to signal "smoke test, not a product feature" so participants do not mistake it for unfinished work. Cross-platform support (macOS, Linux, Windows 11, WSL2) is a hard requirement; verification will be by participant dry-run rather than CI for the initial release. Tailwind is included via its official in-browser runtime (Tailwind 4.3.0's `@tailwindcss/browser` package), vendored locally from jsDelivr with SHA-256 verification — a deliberate learning-template tradeoff documented inline so it is not mistaken for a production pattern. `CLAUDE.md` ships with the schema-reset workflow and no-JS-tooling constraints documented for agents; additional best-practice content will be added in a later iteration once the env is validated.

## Status

**Verified 2026-05-16; amended 2026-05-16 to drop `make`.** All 54 requirements (REQ-001 – REQ-052 with split-IDs REQ-019b, REQ-026b, REQ-033b; REQ-038 unused; REQ-031 retired by amendment) are implemented and verified on macOS:

- **48 requirements** verified by static file inspection (structure, deps, code, tests, documentation, constraints).
- **REQ-018, REQ-024, REQ-025, REQ-026, REQ-026b, REQ-039, REQ-040** additionally verified end-to-end via `agent-browser`: page renders health + ping count, "Send ping" increments the count, count persists across reload, and both error alerts (load-time health failure and POST failure) render when the backend is stopped.
- **REQ-013, REQ-016, REQ-019b** additionally verified end-to-end (count persisted across server restart).
- **REQ-029, REQ-030, REQ-032, REQ-044** verified by running `uv run pytest backend/tests/` (3 passed in 0.02 s).
- **REQ-033, REQ-033b** verified by running `uv run ruff check .` and `uv run ruff format --check .` (both clean).
- **REQ-043** verified by `time uv sync` (17 ms warm-cache).
- **REQ-050** verified by creating `workshop.db` and running `rm -f workshop.db`.
- **REQ-031** retired by amendment (no Makefile shipped; verified by absence).
- **REQ-034, REQ-052** post-amendment verification: confirmed the README documents the exact `uv run uvicorn …` command (REQ-034) and includes macOS + Linux/WSL2 platform setup sections (REQ-052).

Three requirements remain assumed-good rather than fully verified in this environment:

- **REQ-011** — `uv sync` on a clean machine without `.venv`/cache. Only cached idempotency was retested.
- **REQ-042** — cross-platform behavior on Linux, Windows 11, WSL2. macOS only was exercised; participants will validate other platforms during dry-run as noted in the verification plan.
- **REQ-045** — full clone-to-running wall time on a clean machine. Targets are aspirational per the verification notes; component timings (`uv sync` 17 ms cached, `uv run pytest backend/tests/` 0.02 s) leave ample headroom.

No requirements are missing or unimplemented.

## Requirements

### Functional requirements — repository structure & metadata

REQ-001: The template repository shall provide a `pyproject.toml` file at the repository root.

REQ-002: The `pyproject.toml` shall declare a minimum Python version of 3.13.

REQ-003: The `pyproject.toml` shall declare the runtime dependencies `fastapi`, `uvicorn[standard]`, `sqlalchemy>=2.0`, and `pydantic>=2.0`.

REQ-004: The `pyproject.toml` shall declare the development dependencies `pytest`, `httpx`, and `ruff`.

REQ-005: The `pyproject.toml` shall include a `[tool.ruff]` configuration section targeting Python 3.13 with `ruff format` defaults enabled.

REQ-006: The template repository shall commit a `uv.lock` file at the repository root reflecting the fully resolved dependency graph.

REQ-007: The template repository shall provide an MIT `LICENSE` file at the repository root.

REQ-008: The template repository shall provide a `.gitignore` file at the repository root that excludes `.venv/`, `__pycache__/`, `*.pyc`, `workshop.db`, `.pytest_cache/`, `.vscode/`, `.idea/`, `.env`, and `.env.*`.

REQ-009: The template repository shall lay out source files with `backend/` and `frontend/` as top-level sibling directories of `pyproject.toml`.

REQ-049: The template repository shall provide a `.python-version` file at the repository root containing the text `3.13`.

### Functional requirements — Python environment

REQ-010: When a developer runs `uv sync` from the repository root, the template repository shall install all declared dependencies into a local `.venv` directory.

REQ-011: When a developer runs `uv sync` from the repository root on a clean machine with internet access, the template repository shall complete the installation with exit code 0 and no interactive prompts.

### Functional requirements — backend application

REQ-012: The backend application shall expose a FastAPI ASGI application instance importable as `app.main:app` when the working directory is `backend/`.

REQ-013: When the FastAPI application starts, the backend application shall invoke `Base.metadata.create_all` to create any missing SQLAlchemy tables in the SQLite database.

REQ-014: The backend application shall mount the repository's `frontend/` directory as a `StaticFiles` route at the URL path `/`, serving `index.html` as the default document.

REQ-015: The backend application shall expose all JSON API endpoints under the URL prefix `/api/`.

REQ-016: The backend application shall persist data in a SQLite database file named `workshop.db` located at the repository root.

REQ-017: The backend application shall define a `Ping` SQLAlchemy model in `backend/app/models.py` with the fields `id` (integer primary key, autoincrement) and `created_at` (datetime, server-default current UTC time).

REQ-018: When a client issues `GET /api/health`, the backend application shall return HTTP 200 with the JSON body `{"status": "ok"}`.

REQ-019: When a client issues `POST /api/pings` with any body or no body, the backend application shall insert a new `Ping` row into the database.

REQ-019b: When the backend application successfully inserts a `Ping` row in response to `POST /api/pings`, the backend application shall return HTTP 201 with the created ping as JSON.

REQ-020: When a client issues `GET /api/pings`, the backend application shall return HTTP 200 with a JSON array of all pings ordered by `created_at` descending.

### Functional requirements — frontend application

REQ-021: The frontend application shall provide an `index.html` page that loads `vendor/tailwind.js` and `app.js` via local relative paths.

REQ-022: The frontend application shall ship a vendored copy of Tailwind CSS version 4.3.0's `@tailwindcss/browser` runtime at the path `frontend/vendor/tailwind.js`.

REQ-023: The frontend application shall include an HTML comment in `index.html` immediately above the vendored Tailwind script tag identifying the file as the Tailwind 4.3.0 `@tailwindcss/browser` runtime intended for learning and prototyping, with a note that production deployments should swap to the Tailwind CLI build.

REQ-051: The frontend application shall include a header comment at the start of `frontend/vendor/tailwind.js` that documents the source URL, the pinned version, the SHA-256 of the file contents, the vendoring date, and the procedure to update the file.

REQ-024: When `index.html` finishes loading in a browser, the frontend application shall issue `GET /api/health` via `app.js` and render the returned status text in a visible element.

REQ-025: When `index.html` finishes loading in a browser, the frontend application shall issue `GET /api/pings` via `app.js` and render the returned count in a visible element.

REQ-026: When a user clicks the "Send ping" button on `index.html`, the frontend application shall issue `POST /api/pings`.

REQ-026b: When the frontend application receives a successful response from a user-initiated `POST /api/pings`, the frontend application shall refresh the rendered count by re-issuing `GET /api/pings`.

### Functional requirements — tests

REQ-027: The backend tests shall provide a `conftest.py` that creates an isolated in-memory SQLite database for the test session.

REQ-028: The backend tests shall provide a `conftest.py` that overrides the FastAPI dependency yielding database sessions so that tests do not touch `workshop.db`.

REQ-029: The backend tests shall include `test_health.py` which verifies that `GET /api/health` returns HTTP 200 with the JSON body `{"status": "ok"}`.

REQ-030: The backend tests shall include `test_pings.py` which verifies that after issuing `POST /api/pings` followed by `GET /api/pings`, the returned array contains exactly one record with an `id` field and a `created_at` field.

### Functional requirements — developer commands

> *Amended 2026-05-16.* The original `Makefile` requirement (REQ-031) was retired in favor of direct `uv run …` invocations documented in the README. Rationale: dropping `make` removes a cross-platform install prerequisite (notably absent from native Windows and from minimal Linux images / fresh WSL2 Ubuntu without `build-essential`) and keeps the template's "no extra tooling" spirit consistent with the existing no-Node / no-Docker / no-build-step constraints. REQ-032 / REQ-033 / REQ-033b / REQ-034 / REQ-050 below are rephrased to require README documentation of the underlying commands instead of `make` targets.

REQ-031: *Retired by amendment 2026-05-16.* The template repository shall not ship a `Makefile`; all developer commands are documented directly in `README.md`.

REQ-032: The `README.md` shall document `uv run pytest backend/tests/` as the command to run the backend test suite.

REQ-033: The `README.md` shall document `uv run ruff check .` as one of the lint commands.

REQ-033b: The `README.md` shall document `uv run ruff format --check .` as one of the lint commands.

REQ-034: The `README.md` shall document `uv run uvicorn app.main:app --reload --app-dir backend --port 8000` as the command to start the development server on port 8000.

REQ-050: The `README.md` shall document deleting the `workshop.db` file at the repository root (e.g. `rm -f workshop.db`) as the schema-reset workflow.

REQ-052: The `README.md` shall include platform-specific install instructions for macOS and for Linux / Windows (WSL2), covering at minimum how to install `uv` and `git` on each.

### Functional requirements — documentation

REQ-035: The template repository shall provide a participant-facing `README.md` at the repository root that documents prerequisites, platform-specific install instructions, setup commands, run commands, test commands, the folder structure, the location of the SQLite database file, and the schema-change workflow (delete `workshop.db` after modifying a model).

REQ-036: The template repository shall provide a `CLAUDE.md` file at the repository root that documents for Claude Code agents the schema-change workflow (delete `workshop.db` after modifying a model schema) and the no-JS-package-manager constraint (additional client-side JS goes in `app.js` directly or as a vendored static file following the `tailwind.js` procedure; never via npm, `package.json`, or a JS bundler), with additional best-practice content to be added in a later iteration.

REQ-037: The template repository shall provide a `frontend/README.md` that explains the no-build-step approach, the fact that all static files are served by the FastAPI backend, the pinned Tailwind version vendored in `vendor/tailwind.js`, and the procedure to re-vendor it from jsDelivr with SHA-256 verification.

### Unwanted behavior / error handling

REQ-039: If the frontend application fails to reach `/api/health` on page load, then the frontend application shall display a visible error message indicating the backend is unreachable.

REQ-040: If the frontend application fails to reach `/api/pings` on page load or after a button click, then the frontend application shall display a visible error message indicating the backend is unreachable.

### Constraints

REQ-041: The template repository shall make zero external network calls at application runtime.

REQ-042: The template repository shall function on macOS, Linux, Windows 11, and Windows Subsystem for Linux 2 without platform-specific configuration files.

REQ-043: The template repository shall complete `uv sync` in under 30 seconds on a clean machine with a warm uv package cache.

REQ-044: The template repository shall complete `uv run pytest backend/tests/` in under 5 seconds on a clean machine.

REQ-045: The template repository shall reach a running server state in under 60 seconds when measured from `git clone` through `uv sync` to `uv run uvicorn app.main:app --reload --app-dir backend --port 8000` on a clean machine with a warm uv package cache.

REQ-046: The backend application shall not depend on Node.js or Docker.

REQ-047: The frontend application shall not require any build step to render correctly in a browser.

REQ-048: The backend application shall use `Base.metadata.create_all` rather than a migrations framework to establish the database schema.

## Verification notes

- **Structure (REQ-001–009):** verified by inspecting the working tree against the agreed folder layout.
- **Environment (REQ-010–011):** verified by running `uv sync` from a fresh checkout and confirming `.venv/` populates without error.
- **Backend HTTP behavior (REQ-018–020):** verified by `pytest` against the running app via `TestClient`, asserting status codes and JSON payloads.
- **Static mount (REQ-014, REQ-021–023):** verified by curling `/` and confirming `index.html` is returned, and by curling `/vendor/tailwind.js` and confirming the vendored file is served.
- **Frontend behavior (REQ-024–026, REQ-039–040):** verified manually by loading `http://localhost:8000/` in a browser, clicking the "Send ping" button, refreshing the page to confirm the count persists, and stopping the backend to confirm the unreachable-state error renders.
- **Developer commands (REQ-031–034, REQ-050, REQ-052):** verified by inspecting `README.md` to confirm each documented command matches the spec, and by running each `uv run …` command from the repository root to confirm it executes successfully. Original `make`-target verification (pre-amendment 2026-05-16) was performed by invoking each target.
- **Performance (REQ-043–045):** verified with `time uv sync`, `time uv run pytest`, and a stopwatch on the full clone-to-running sequence on the author's macOS machine; targets are aspirational on first-time-without-cache machines.
- **Cross-platform (REQ-042):** assumed-good for the initial release (no CI verification); to be validated by participants during dry-run.
- **Structural & wiring (REQ-012, REQ-013, REQ-015, REQ-016, REQ-017, REQ-027, REQ-028, REQ-035–037, REQ-041, REQ-046–049, REQ-051):** verified by code review and file inspection — presence and correctness of files, imports, declarations, and header-comment fields is sufficient. REQ-013 is additionally validated implicitly by passing tests (a missing `create_all` would surface as "no such table" failures). REQ-051 verified by reading the first lines of `frontend/vendor/tailwind.js` and confirming the SHA-256 in the header matches `shasum -a 256 frontend/vendor/tailwind.js`.
- **Schema reset and port pin (REQ-034, REQ-050):** verified manually by creating `workshop.db`, running `rm -f workshop.db` and confirming the file is removed, and curling `http://localhost:8000/api/health` after `uv run uvicorn …` to confirm the port binding.

## Decisions

The following calls are already settled by requirements but worth surfacing for reviewers.

1. **Frontend mount path** — `/` (root). Alternative `/app` was rejected as it creates a confusing two-path mental model. See REQ-014.
2. **`POST /api/pings` body** — accepts any body (including empty/none); no validation. Keeps the smoke test minimal. See REQ-019.
3. **Frontend display detail** — count only (no list of timestamps). Refreshing the page demonstrates persistence; a list was rejected as gold-plating. See REQ-025.
4. **Test database** — in-memory SQLite rather than a temp file. Slightly faster, no cleanup needed. See REQ-027.
5. **Dev-server port** — pinned to `8000` in the documented `uv run uvicorn …` command so the canonical local URL is `http://localhost:8000`. See REQ-034.
6. **Schema-change workflow** — deleting `workshop.db` (via `rm -f workshop.db`) is the documented reset path; README and CLAUDE.md document that students should run it after modifying a model. We deliberately did not adopt Alembic for this template; Alembic is the right answer once data persistence matters and the course can introduce it as a later lesson. See REQ-035, REQ-036, REQ-050.
7. **Python version** — pinned to `3.13` via `.python-version` and the `requires-python` declaration in `pyproject.toml`. Chosen for improved error messages and modern-default status while keeping library compatibility comfortable. See REQ-002, REQ-049.
8. **Tailwind version & vendoring source** — pinned to Tailwind CSS `4.3.0` vendored from jsDelivr's `@tailwindcss/browser` package with SHA-256 verification at vendoring time. v4 chosen over v3 (still supported until Feb 2027) because by mid-2026 LLMs default to v4 syntax when generating Tailwind classes; pinning a course template to v3 would create friction between agent-generated code and what works in the template. jsDelivr chosen over Tailwind's own CDN because it publishes per-file SRI hashes, giving an independent integrity source alongside npm package provenance. SHA-256 is recorded in a header comment in the vendored file at vendoring time, and re-vendoring instructions are documented in `frontend/README.md` so future updates remain auditable. See REQ-022, REQ-023, REQ-037, REQ-051.
9. **No JavaScript package manager** — the template ships zero `package.json`, no npm/yarn/pnpm, no Node, no bundler. The entire client-side JS surface is `frontend/app.js` (own code) plus `frontend/vendor/tailwind.js` (one vendored static file pinned by commit + header SHA-256). Additional client-side JS should be added inline to `app.js` or vendored as a static file following the `tailwind.js` procedure. Rationale: eliminates transitive-dependency supply chain risk, removes lockfile drift, removes any cross-platform Node toolchain requirement, and gives a single auditable file as the entire client-side third-party surface. CLAUDE.md instructs agents accordingly. See REQ-036, REQ-051.
10. **Dependency-update tooling left to the template repo, not propagated to forks** — Dependabot is configured on the template's own GitHub repository for the maintainer's benefit but no `.github/dependabot.yml` is shipped in the template itself. Students who want automated dep updates on their own forks can enable Dependabot via GitHub's UI. Keeps the template free of GitHub-platform config that participants may not want.

## Open questions

None — all decisions captured above.
