# ADR-004: Use `uv run` instead of `.venv/bin/` paths

**Date:** 2026-03-29  
**Status:** Accepted

## Context

The project uses `uv` for dependency management. The `.venv` directory is
created locally and its shebang lines are hardcoded to the absolute path of the
machine that built them (e.g. `/home/hogjonny/...`).

When the repo is opened in a different environment — Docker container, CI,
another developer's machine — all `.venv/bin/pytest`, `.venv/bin/python` calls
fail with "not found" even though the binary exists, because the shebang path
doesn't resolve.

This was discovered when running tests from inside the OpenClaw Docker container
(`/home/node/`) against a venv built in WSL (`/home/hogjonny/`).

## Decision

All documentation, skills, hooks, and CLAUDE.md use `uv run` instead of
`.venv/bin/` paths:

```bash
# Correct:
uv run pytest tests/ -q
uv run python scripts/demo.py

# Forbidden:
.venv/bin/pytest tests/ -q       ← breaks outside build machine
.venv/bin/python scripts/demo.py ← breaks outside build machine
```

## Rationale

- `uv run` resolves the correct venv automatically regardless of platform, working directory, or absolute path
- Works in Docker, CI, WSL, native — no environment-specific configuration
- `uv` is already required for this project; no additional tooling needed
- Agents (Claude Code, Codex, etc.) running in isolated environments hit this immediately

## Consequences

- All skills, hooks, and CLAUDE.md updated to use `uv run` (2026-03-29)
- `DAILY_AGENT_PROMPT.md` deprecated — it contained hardcoded `.venv/bin/` paths and WSL-absolute paths
- Any contributor writing new documentation must use `uv run`, not `.venv/bin/`
