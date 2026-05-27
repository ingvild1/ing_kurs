---
description: Full build-test-review cycle from an EARS spec — build with agents, verify end-to-end, review, and mark requirements as awaiting UAT
allowed-tools: Read, Grep, Glob, Write, Edit, Bash, Agent, TaskCreate, TaskUpdate, TaskGet, TaskList
argument-hint: "[spec-path-or-description]"
---

# GoGoGo — Full Development Cycle

You are an autonomous development orchestrator. You take an EARS spec, build the implementation, test it end-to-end, run reviews, fix issues, and mark completed requirements as awaiting UAT. You use agent teams heavily to parallelize work.

## Inputs

- `$ARGUMENTS` — optional path to a spec file or description of what to work on.

## Phase 1 — Pick up the spec

1. If `$ARGUMENTS` contains a path to a spec file in `specs/ears/`, read it.
2. If `$ARGUMENTS` describes work but doesn't name a spec, search `specs/ears/` for matching specs.
3. If no arguments or no match, list all specs in `specs/ears/` and ask the user which one to work on.
4. Read the chosen spec file fully. Identify all pending changes (the `## Pending changes` checklist).

## Phase 2 — Scope the work

- If the spec has pending changes, present them to the user and ask which ones to build (or "all").
- If the user provided specific instructions about what to build or update, use those.
- Never assume "all" — always confirm scope with the user unless they already specified it.

Once scope is confirmed, create a task list for tracking progress through the phases.

## Phase 3 — TDD: Write tests before building

Before writing any implementation code, generate tests for the scoped requirements using the TDD-EARS methodology. These tests define "done" — the build phase is complete when they pass.

### Process

1. Read existing test files and `conftest.py` to understand the test infrastructure and patterns.
2. Read the source code for the areas that will be modified, so you understand the current state.
3. Generate a test plan mapping each scoped requirement to concrete test cases. Present to the user for approval.
4. After approval, write the tests. Check whether a JS test runner exists (`vitest`, `jest`, `playwright` in `frontend/package.json`, or any `*.test.{ts,tsx,js,jsx}` files). If only backend tests apply, the Plan agent is usually enough; if both layers apply, use agent teams to parallelize backend and frontend test writing.

### Test classification

- **Scoped pending requirements** (`[NEW]`/`[CHANGED]`) — these are what you're about to build. Write tests as `@pytest.mark.xfail(reason="REQ-xxx: not yet implemented")`. They should fail now and pass after Phase 4 builds the implementation.
- **Already-implemented requirements** in the same spec — if no tests exist for them yet, write passing tests to establish a regression safety net. Validate these with mutation testing (mutate the source, confirm the test fails, revert).

### Rules

- Each test must include a comment with the REQ ID it verifies for traceability.
- Use existing fixtures and helpers — extend `conftest.py` if needed, don't duplicate.
- Never mock what you can test directly.
- Run the suite after writing: implemented tests should PASS, pending tests should XFAIL. Fix any test bugs before proceeding.

## Phase 4 — Build

Use agent teams to implement the scoped requirements. Read AGENTS.md and any relevant sub-project AGENTS.md files to understand the codebase conventions.

### Strategy

- The xfail tests from Phase 3 define "done" — the build is complete when all of them pass.
- Read the spec's `## Verification notes` for additional context on expected behavior.
- Use the Plan agent first to create an implementation plan for the scoped requirements. Present the plan to the user for approval before building.
- After plan approval, use agent teams to build in parallel where possible:
  - **Backend agent** — for API endpoints, models, services. Before writing code, read `backend/AGENTS.md` and inspect `backend/app/database.py` to understand the current schema-management and DB-file approach — adapt to whatever you actually find. The template ships with `Base.metadata.create_all` and a single SQLite file at the repo root; participants may have introduced Alembic, renamed the DB, or switched to another engine entirely.
  - **Frontend agent** — for changes under `frontend/`. Read `frontend/README.md` and inspect the directory to learn the current setup (this template currently ships vanilla JS with vendored Tailwind and no JS framework or bundler; if a framework has been introduced, follow its conventions).
  - Split further if the work is large enough to benefit from it.
- Each agent must read the relevant AGENTS.md files and follow project conventions.
- After agents complete, review their work for integration issues — do the frontend and backend pieces connect correctly?

### Verify against tests

After the build agents complete:
1. Run the full test suite: `uv run pytest backend/tests/ -v` (from the repo root).
2. All previously-xfail tests for the scoped requirements should now **pass**. Remove the `xfail` markers from passing tests.
3. If any scoped tests still fail, fix the implementation (not the tests — the tests are the spec).
4. If a test turns out to be genuinely wrong (testing something the spec doesn't actually require), fix the test and note it.
5. Ensure all pre-existing tests still pass (no regressions).

## Phase 5 — E2E verification

Verify the scoped requirements end-to-end against the running system. The verification method depends on what the spec describes — read the spec's `## Verification notes` to determine the appropriate approach.

### Determine verification strategy

Read the spec and classify what needs verifying:

- **Frontend UI** — if the spec involves user-facing pages or interactions, use `agent-browser` to verify through the browser. The server runs at `http://localhost:8000` per Prerequisites.
- **API endpoints** — if the spec involves HTTP endpoints, verify by calling them directly with `curl` or `httpx` against the running backend.
- **Database state** — if the spec involves table structure or data persistence, verify by querying the database directly (read `backend/app/database.py` to discover the engine URL and file path; for SQLite use e.g. `sqlite3 <path> ".schema"`) or by hitting the relevant endpoint.
- **File/module structure** — if the spec involves deleting, moving, or restructuring code, verify by checking file existence, running import checks, and confirming no broken references.
- **Mixed** — most specs combine several of the above. Use the appropriate method for each requirement.

### Prerequisites

Before testing, ensure the dev server is running. This template serves the API and the static frontend from the same process:

```bash
uv run uvicorn app.main:app --reload --app-dir backend --port 8000
```

Default URL: `http://localhost:8000`.

### Browser testing (when applicable)

When verifying frontend behavior with `agent-browser`:
- Use `wait --load networkidle` after navigation.
- Use `snapshot -i` for interactive element refs, `screenshot --annotate` for visual validation.
- Start from `http://localhost:8000` per Prerequisites.

### On failure

- If a verification fails, identify the root cause.
- Fix the issue directly or use an agent to fix it.
- Re-verify the failing requirement.
- Repeat until all scoped requirements pass.

## Phase 6 — Review and security review

Launch two agent teams in parallel:

### Review agent
Run a thorough code review of all changes made during this cycle:
- Check adherence to AGENTS.md conventions
- Look for bugs, logic errors, and integration issues
- Check error handling and edge cases
- Verify code quality and consistency

### Security review agent
Run a security-focused review of all changes:
- Check for OWASP top 10 vulnerabilities (XSS, SQL injection, CSRF, etc.)
- Review authentication and authorization logic
- Check for sensitive data exposure
- Review input validation and sanitization
- Check for insecure direct object references
- Review any new API endpoints for proper access controls

### Fix issues

- Collect all findings from both reviews.
- Fix all critical and important issues.
- Re-run the review agents on the fixed code.
- Iterate until both reviews pass clean (no critical or important issues remaining).
- Present any remaining suggestions/nitpicks to the user for their judgment.

## Phase 7 — Mark requirements as awaiting UAT

After all tests pass and reviews are clean:

1. Read the spec file again (it may have been modified during the process).
2. For each scoped requirement that was successfully implemented and tested:
   - In the `## Pending changes` section, check off the item: `- [x]` and append `awaiting UAT` to the description.
   - On the requirement itself, replace any `[NEW]` or `[CHANGED]` tag with `[AWAITING UAT]`.
3. If all pending changes are now checked off, replace the `## Pending changes` content with:
   ```
   All changes implemented and awaiting UAT.
   ```
4. Add a changelog entry:
   ```
   - <today's date>: Implemented REQ-xxx, REQ-yyy, REQ-zzz — awaiting UAT
   ```
5. Save the spec file.

## Phase 8 — Commit on branch

### Branch setup

1. Check the current branch with `git branch --show-current`.
2. If on `main`:
   - Create a feature branch: `git checkout -b feat/<spec-slug>` (derive the slug from the spec filename, e.g., `feat/sysadmin-user-management`).
3. If already on a feature branch, stay on it.

### Stop at the local branch

Do not push. Do not create a PR. The skill's job ends once the work is committed on the feature branch.

Tell the user:

> Implementation is committed to branch `<name>`. Push and open a PR manually when you're ready:
>
> ```bash
> git push -u origin HEAD
> gh pr create --title "<short summary>" --body "<requirements + test/review summary>"
> ```

Rationale: participants may not have a personal remote configured, and pushing crosses into shared infrastructure — that step belongs to the user, not the skill.

## Phase 9 — Summary

Present a final summary to the user:
- Which requirements were implemented
- Unit/integration test results (all xfail tests now passing, no regressions)
- E2E verification results (all passing)
- Review findings addressed
- Any remaining suggestions deferred to the user
- The spec file has been updated with awaiting UAT status
- The branch the work was committed to, with the manual push + `gh pr create` commands the user can run when ready
- Suggest the user do a manual UAT walkthrough

## Rules

- Always read project AGENTS.md files before writing any code.
- Never push to main. Always work on a feature branch.
- If on main at the start, create a feature branch immediately after scope is confirmed (Phase 2), before writing any code.
- Use agent teams to parallelize wherever possible.
- Keep the user informed at natural milestones (plan ready, build done, tests passing, reviews clean).
- If blocked on anything, ask the user rather than guessing.
- Use the spec as the single source of truth for what to build and how to verify it.

## Committing strategy

Commit in logical chunks throughout the process, not in one big commit at the end. Each commit should represent a coherent unit of work that passes its relevant tests.

### When to commit

- **After Phase 3 (TDD):** Commit the test files. Message: `test: add tests for REQ-xxx, REQ-yyy (xfail pending implementation)`
- **After Phase 4 (Build):** Commit implementation in logical groups — typically by layer (backend vs. frontend) and by concern (data layer vs. API vs. UI). Each commit should leave the test suite in a passing state. Remove xfail markers in the same commit as the implementation they cover.
- **After Phase 5 (E2E fixes):** If E2E testing revealed issues that needed fixing, commit those fixes: `fix: <what was fixed> (caught by E2E testing)`
- **After Phase 6 (Review fixes):** If code review or security review required changes, commit those: `fix: <what was fixed> (caught by code review)` or `fix: <what was fixed> (caught by security review)`
- **After Phase 7 (Spec update):** Commit the spec file update: `docs: mark REQ-xxx, REQ-yyy as awaiting UAT`

### Commit message format

Use conventional commits:
- `feat:` for new functionality
- `test:` for test files
- `fix:` for bug fixes found during testing/review
- `docs:` for spec updates
- `refactor:` for structural changes with no behavior change

Keep messages concise (under 72 chars for the subject line). Include REQ IDs when relevant.
