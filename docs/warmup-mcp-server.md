# Warm-up: Build your own MCP server with Claude Code

A short warm-up exercise. You'll use Claude Code to build a local MCP server that
wraps the Norwegian spot electricity price API at
[hvakosterstrommen.no](https://www.hvakosterstrommen.no/strompris-api), then
register it so Claude Code itself can call it as a tool.

The point: practice agentic prompting — state the goal, let Claude figure out
the details.

## 1. Start Claude Code

Open a terminal **in the root of this workshop repo** and run:

```bash
claude
```

You'll create `strompris-mcp/` inside this repo and register it at project
scope here, so the server auto-loads whenever you launch Claude Code from this
repo root. Steps 2 and 3 happen in the same Claude Code session — don't
exit between them.

## 2. Paste this prompt

> Build a Python MCP server in a new folder `strompris-mcp/` in the current directory. Initialise the project with `uv init --package strompris-mcp` so it has a CLI entry point named `strompris-mcp`, then add the official Python MCP SDK (`mcp` package on PyPI) and an HTTP client. Expose one tool, `get_electricity_price`, that fetches Norwegian spot electricity prices from
> ```
> https://www.hvakosterstrommen.no/api/v1/prices/{YYYY}/{MM}-{DD}_{AREA}.json
> ```
> (example: `https://www.hvakosterstrommen.no/api/v1/prices/2026/05-17_NO1.json`)
> for a given date and price area (NO1–NO5). Before telling me you're done, smoke-test the implementation against the live API for yesterday's date and one area, and show me the output.

Note: the API publishes the next day's prices around 13:00 Europe/Oslo.
Yesterday and earlier are always available; "today" before noon may not be.

## 3. Paste this prompt (same Claude Code session)

> Register this server with Claude Code at **project scope** from the root of this repo so it auto-loads whenever I launch `claude` here. Run this exact command (the `--` separator is required, and the relative path keeps the registration portable across clones):
> ```
> claude mcp add --scope project strompris -- uv run --directory ./strompris-mcp strompris-mcp
> ```
> Then tell me exactly what to do next to verify it works.

## 4. Verify it works

Follow Claude's verification instructions. They should match this:

1. Exit Claude Code (`/exit` or Ctrl-D).
2. Relaunch `claude` from this same workshop repo root.
3. Accept the trust prompt for the new `.mcp.json` (it appears once, the
   first time Claude Code sees a new project-scoped MCP config).
4. Run `/mcp` and confirm `strompris` shows as **connected** with one tool.

## 5. Try it

> What was the average spot electricity price in NO1 yesterday in øre/kWh (1 NOK = 100 øre)? Use the strompris MCP tool.

The API returns prices in NOK/kWh, so the answer needs `× 100` to get øre/kWh.
Claude should handle that conversion on its own.

## If something goes wrong

Recovery is part of the learning. A few patterns:

- `/mcp` shows `strompris` as **failed** → prompt Claude to investigate (it
  can read the server logs, check the `.mcp.json` path, etc.).
- `/mcp` doesn't list `strompris` at all → you relaunched Claude Code from a
  different directory than the workshop repo root. Project-scoped servers
  only load when Claude Code's working directory contains the `.mcp.json`.
  Confirm with `ls .mcp.json` from the repo root.
- API returns 404 → see the timezone note in step 2; before 13:00 Europe/Oslo
  only yesterday and earlier are guaranteed.
- Trust prompt never appears → either you've already accepted it in a
  previous session (harmless — proceed to `/mcp`), or `.mcp.json` wasn't
  created at the repo root.

`.mcp.json` is currently not gitignored in this repo. Feel free to leave it
uncommitted (or add it to your local `.gitignore`) — it's not needed for the
rest of the workshop.

## Stretch goals

- Add a `get_price_range(start_date, end_date, area)` tool that fetches several
  days concurrently.
- Add an MCP **resource** (not a tool) describing the NO1–NO5 price zones.
- Compare: in the workshop project, ask Claude Code "what was electricity
  yesterday" first without the MCP server, then with it. Notice the difference
  in how it approaches the task.
