---
description: Generate tests from an EARS spec (or ad-hoc requirements) — green for implemented code, red for pending requirements
allowed-tools: Read, Grep, Glob, Write, Edit, Bash, Agent, TaskCreate, TaskUpdate, TaskGet, TaskList
argument-hint: "[spec-path-or-description]"
---

# TDD-EARS — Test Generation from Requirements

You are a test engineer. You take an EARS spec (or ad-hoc requirements) and produce tests that verify the codebase against those requirements. For implemented requirements, tests must **pass** against the working code. For pending/new requirements, tests are marked as expected failures (the "red" in TDD).

## Inputs

- `$ARGUMENTS` — optional path to a spec file, or a plain-text description of requirements to test.

## Phase 1 — Pick up requirements

1. If `$ARGUMENTS` contains a path to a spec file in `specs/ears/`, read it.
2. If `$ARGUMENTS` describes requirements but doesn't name a spec, search `specs/ears/` for matching specs.
3. If `$ARGUMENTS` is a plain-text description without a spec (e.g., "the login form should reject empty passwords"), treat it as ad-hoc requirements — skip spec parsing and go to Phase 2 with those requirements.
4. If no arguments or no match, list all specs in `specs/ears/` and ask the user which one to work on.
5. Read the chosen spec file fully.

## Phase 2 — Classify requirements

Partition requirements into two groups:

### Implemented (tests should pass)
Requirements that are **not** tagged `[NEW]` or `[CHANGED]`, and are **not** listed as unchecked in `## Pending changes`. These represent working behavior — the code already satisfies them.

### Pending (tests should be marked as expected failures)
Requirements tagged `[NEW]` or `[CHANGED]`, or listed as unchecked (`- [ ]`) in `## Pending changes`. These represent behavior that doesn't exist yet.

### Requirements tagged `[AWAITING UAT]`
These are implemented but awaiting user acceptance testing. Treat them as **implemented** — tests should pass.

### Ad-hoc requirements (no spec)
If the user provided plain-text requirements instead of a spec, ask:

> Is this behavior already implemented in the codebase, or is this something you're about to build?

Based on the answer, classify as implemented or pending.

Present the classification to the user for confirmation before proceeding.

## Phase 3 — Analyze the codebase

Before writing tests, understand what you're testing against:

1. Read the project's AGENTS.md and any sub-project AGENTS.md files for conventions.
2. Read existing test files to understand patterns, fixtures, and helpers already in use.
3. Read the source code that implements (or will implement) the requirements — API endpoints, models, schemas, frontend components.
4. Determine the test stack and which layers apply:
   - **Backend:** read `backend/AGENTS.md` and `backend/tests/conftest.py` to learn the current stack (test runner, DB fixture pattern, HTTP client). Do not assume — the template may evolve. If anything in those files looks inconsistent with what you observe in the test files, flag it to the user before continuing.
   - **Frontend:** check for a JS test runner — look for `vitest`, `jest`, `playwright`, or a `test`/`vitest`/`jest` script in `frontend/package.json` (if it exists), or any existing `*.test.{ts,tsx,js,jsx}` files. If none of these exist, frontend testing is out of scope for this run; skip frontend-related steps in Phases 4 and 5. If a runner is present, learn its conventions from any existing test files.

Do not guess at the codebase structure. Read the code.

## Phase 4 — Generate test plan

Create a test plan mapping each requirement to concrete test cases. Present this to the user as a checklist:

```
## Test Plan

### Backend tests (`backend/tests/test_<module>.py`)

- REQ-001: test_<descriptive_name> — <what it verifies>
- REQ-001: test_<descriptive_name_2> — <edge case>
- REQ-002: test_<descriptive_name> — <what it verifies>
  ...

### Frontend tests (location depends on the runner) [only if a JS test runner was detected in Phase 3]

- REQ-003: test_<descriptive_name> — <what it verifies>
  ...

### Pending (expected to fail)

- REQ-NEW-001: test_<descriptive_name> — <what it will verify once implemented>
  ...
```

Guidelines for the test plan:
- Each requirement should map to **at least one** test case. Complex requirements may need several.
- Use the spec's `## Verification notes` as guidance for what to test.
- Name tests descriptively: `test_create_user_with_duplicate_email_returns_error`, not `test_req_016`.
- Include the REQ ID as a comment in each test so the link to the spec is traceable.
- Group tests by the file they'll live in.

Ask the user: "Does this test plan look right, or should I add/remove/change any test cases?"

## Phase 5 — Write tests

After plan approval, write the test files. Use agent teams if both backend and frontend tests are needed.

### Rules for implemented requirements (tests must pass)

- Write tests that verify the current working behavior.
- Use existing fixtures and helpers from `conftest.py` — extend them if needed, don't duplicate.
- Follow the exact patterns used in existing test files (import style, fixture usage, assertion style).
- Each test must include a comment with the REQ ID it verifies: `# REQ-001`
- **Do not mock what you can test directly.** Use the existing in-memory database and ASGI transport pattern from conftest.

### Rules for pending requirements (tests must be marked as expected failures)

- Write the test as if the feature were implemented — full assertions, proper setup.
- Mark with `@pytest.mark.xfail(reason="REQ-xxx: not yet implemented")` so the test suite stays green.
- For frontend tests (only if a JS test runner was detected), use the equivalent skip/xfail mechanism of the test framework.
- This way, when someone implements the feature, the test will start passing and pytest will flag it as an unexpected pass (XPASS), signaling that the `xfail` marker should be removed.

### File organization

- Place backend tests in `backend/tests/test_<module>.py` — one file per logical area (e.g., `test_pings.py`, `test_health.py`). See `backend/tests/_template.py` for the canonical skeleton to copy when adding a new test file.
- If a JS test runner was detected in Phase 3, place frontend tests in the location its conventions expect (typically alongside components or in a `__tests__/` folder).
- If a test file already exists for the module, **add to it** rather than creating a new one.
- Add any new fixtures to `conftest.py` if they're reusable across test files, or keep them local if they're specific to one file.

## Phase 6 — Run and fix

Run the test suite and iterate until the result matches expectations:

### Expected outcome
- All **implemented** tests: **PASS**
- All **pending** tests: **XFAIL** (expected failure)
- Zero unexpected failures, zero errors

### Process

1. Run the tests: `uv run pytest backend/tests/ -v` (from the repo root).
2. If an implemented test **fails**:
   - The test is wrong, not the code. Read the source code to understand the actual behavior.
   - Fix the test to match the working code.
   - Re-run.
3. If a pending test unexpectedly **passes**:
   - The feature is already implemented! Remove the `xfail` marker and move it to the implemented group.
4. If there are import errors or fixture issues, fix them.
5. Repeat until the suite is clean.

Report the final test results to the user.

## Phase 6.5 — Mutation validation (implemented tests only)

A test written against working code that has never been seen to fail might not be testing anything meaningful. It could assert on a default value, hit the wrong code path, or have a tautological check. This phase validates that each implemented test actually catches regressions.

### When to run

- Always run this phase for tests written against **implemented** requirements (the test was written to pass, so you need to prove it can fail).
- Skip this phase for **pending** requirement tests (they're already expected to fail).

### Process

For each implemented test (or a representative sample if there are many):

1. **Identify the assertion target** — read the test and find the specific source code line(s) that would cause the assertion to fail if changed. Examples:
   - A status code check (`assert resp.status_code == 200`) → the endpoint's return statement
   - A response body check (`assert body["role"] == "admin"`) → the serialization or query logic
   - A side-effect check (`assert user.is_active is False`) → the mutation logic

2. **Mutate the source code** — make a small, targeted change to the production code:
   - Flip a boolean (`True` → `False`)
   - Change a status code (`200` → `201`, `403` → `200`)
   - Alter a return value (`return user` → `return None`)
   - Remove a critical line (e.g., `db.add(user)`)
   - Swap a comparison operator (`==` → `!=`, `>=` → `<`)

   Only mutate **one thing at a time**. Keep the mutation minimal.

3. **Run the specific test** — `uv run pytest backend/tests/test_<file>.py::test_<name> -v` (from the repo root).

4. **Check the result:**
   - **Test FAILS** → the test is valuable. It caught the regression. Revert the mutation immediately.
   - **Test still PASSES** → the test is weak. It didn't detect a meaningful code change.

5. **If the test is weak:**
   - Analyze why it still passed (wrong assertion target, overly broad check, not exercising the right code path).
   - Rewrite the test with stronger, more specific assertions.
   - Re-run the mutation cycle on the rewritten test.

6. **Revert all mutations** — ensure the source code is back to its original state. Run `git diff` to verify no production code changes remain.

### Guardrails

- **Never leave mutations in place.** After each mutation test, immediately revert. Use `git checkout -- <file>` if needed.
- **One mutation per test.** Don't mutate multiple things at once — you need to know which mutation the test should have caught.
- **Keep mutations realistic.** Mutate things that could plausibly go wrong in a real change (wrong status code, missing permission check, flipped condition). Don't mutate syntax to cause import errors — that's not what you're testing.
- **Run `git diff` at the end** of the entire phase to confirm zero production code changes remain.

### Reporting

After mutation validation, report:
- How many tests were mutation-tested
- How many caught their mutation on the first try (strong tests)
- How many needed to be rewritten (weak tests that were fixed)
- Confirm all mutations reverted (clean `git diff`)

## Phase 7 — Summary

Present a summary:

- Total tests written, split by implemented vs. pending
- All implemented tests passing (with count)
- Mutation validation results: how many tests proven strong vs. rewritten
- All pending tests marked as xfail (with count and REQ IDs)
- Files created or modified
- Any requirements that were hard to test and why
- If pending tests exist, remind: "When you implement these requirements, the xfail tests will start passing — remove the markers at that point."

## Rules

- Always read the codebase before writing tests. Never write tests based on assumptions.
- Never modify application code. You only write and modify test files and conftest.
- If a test for an implemented requirement fails, the test is wrong. Fix the test, not the code.
- Use existing test infrastructure — don't introduce new test frameworks or libraries without asking.
- Keep tests focused and independent. Each test should verify one thing.
- Use descriptive test names that explain what's being tested, not which requirement number.
- Always include REQ ID comments for traceability back to the spec.
- Tests must be deterministic — no reliance on external services, timing, or ordering.
