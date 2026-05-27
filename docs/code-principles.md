# Code principles

These are widely-endorsed defaults, not strong style opinions. Linked from [`../AGENTS.md`](../AGENTS.md). The short imperatives there are the rule; this file explains the *why* and shows what each looks like in practice.

## Subtract code first

The cheapest line of code to maintain is one that doesn't exist. Before adding a class, helper, or config knob, ask whether deleting code somewhere else would satisfy the same requirement.

When it bites: codebases grow faster than they shrink. Defensive checks, "just in case" parameters, and one-off helpers all accrete until the simplest change requires reading three files.

Example: a function that takes a `default=None` parameter "in case someone needs it" but is only ever called with the default. Delete the parameter, delete the branch that handles it.

## Comments explain *why*, not *what*

If the code shows what it does, a comment restating that just doubles the reading work and rots when the code changes. Use comments to record the non-obvious reason — a constraint, a workaround, a rejected alternative.

When it bites: `# increment i by 1` adds noise. `# +1 because the upstream API uses 1-based indexing` saves the next reader fifteen minutes.

Example:

```python
# BAD
i = i + 1  # increment i

# GOOD
i = i + 1  # upstream pagination is 1-based; our cursor is 0-based
```

## Trust internal code; validate at boundaries

Validate untrusted input once, at the edge it enters (HTTP request, DB row, env var). Inside the system, pass plain types and trust them. Re-validating everywhere produces duplicate error paths and hides the real boundary.

When it bites: Pydantic at every function call site turns a one-line function into ten lines and obscures which checks are load-bearing.

Example: in this repo, request bodies are Pydantic models in `backend/app/schemas.py`; ORM objects come from SQLAlchemy in `backend/app/models.py`. Inside a router handler, you can pass an `int` to another function without re-asserting it's an int.

## No premature abstraction

Wait for the third concrete use before extracting a helper, base class, or generic. Two call sites is a coincidence; three is a pattern. Abstractions built from one example almost always have the wrong shape and have to be torn out later.

When it bites: a `BaseHandler` extracted after the second route ends up with `if self.kind == "ping"` branches once a real third case arrives.

Example: see `backend/app/routers/health.py` and `backend/app/routers/pings.py` — two routers, no shared base class, ~20 lines each. If a third router showed up with overlapping logic, *then* extract.

## Keep functions small and named for intent

A function name that needs "and" — `load_and_validate_user` — is two functions glued together. Split them; let the caller compose. The function name should describe the single thing it does, not the sequence of things.

When it bites: long names hide control flow; the "and" function becomes the only sensible place to add the next concern, growing into a 200-line god-function.

Example:

```python
# BAD
def load_and_validate_and_email_user(id): ...

# GOOD
user = load_user(id)
validate(user)
send_welcome_email(user)
```
