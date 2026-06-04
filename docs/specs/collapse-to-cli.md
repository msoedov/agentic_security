# Collapse to CLI: remove MCP + Agno, make scanning agent-invocable

## Why

The MCP server is a thin httpx proxy over the FastAPI server — every MCP tool
just POSTs to `:8718`. So the "run MCP" path actually requires two processes
(MCP stdio + web server) plus the auth/security surface of an exposed server.
Coding agents (Claude, Codex) can call a local CLI directly with none of that.

Goal: one stateless CLI command an agent can invoke and parse. Delete the rest.

## Scope

MCP and Agno are internal/experimental — never a public contract. Hard-delete
in one PR, bump version. No deprecation shims.

## Phase 1 — Delete Agno (dead code, zero risk)

Imported by nothing, not a declared dependency, has undefined-variable bugs.

- [ ] Remove `agentic_security/agents/` (only `operator_agno.py`)
- [ ] Remove Agno references from `docs/mcp_agno_integration.md`

## Phase 2 — Delete MCP

Core scanning (`probe_actor/`, `lib.py`) depends on none of this.

- [ ] Remove `agentic_security/mcp/` (`main.py`, `client.py`, `__init__.py`)
- [ ] Remove `examples/mcp_client_usage.py`
- [ ] Remove `tests/unit/test_mcp.py`
- [ ] Remove `docs/mcp_client_usage.md`, `docs/mcp_agno_integration.md`
- [ ] Drop `mcp = "^1.22.0"` from `pyproject.toml`
- [ ] Strip MCP sections from `Readme.md`

## Phase 3 — Make the CLI agent-invocable (the real work)

Today scanning is config-file-driven: `init` writes `agesec.toml`, then `ci`
reads it. An agent has to do two steps with hidden disk state. Replace with a
direct one-shot command.

Target UX (to be finalized in design):
- [ ] `agentic_security scan --spec <file|->` — stateless, no `agesec.toml`
      required; spec from arg, file, or stdin
- [ ] Streams machine-readable results to stdout (JSON lines), logs to stderr
- [ ] Non-zero exit code on failures found (CI-friendly)
- [ ] Decide fate of existing `ci` (config-driven) vs new `scan`: keep `ci`
      for config workflows, add `scan` for ad-hoc/agent use

Open design questions:
- Output format: JSON lines vs single JSON doc vs both behind a flag
- Does `scan` need the FastAPI `app` at all, or call `fuzzer.scan_router()`
  directly via `lib.SecurityScanner` (preferred — fully standalone)
- What's the minimal spec an agent must pass (llmSpec only? + datasets?)

## Phase 4 — Server stays, but secondary

Keep `agentic_security server` (web UI) — it's the interactive surface. It is
no longer the integration path for agents. Default bind is now `127.0.0.1`.

## Success criteria

- An agent can run a full scan with a single CLI command, no server, no config
  file on disk, parse results from stdout.
- `grep -ri "mcp\|agno" agentic_security/` returns nothing in source.
- Existing fuzzer/probe tests still pass.
