# AGENTS.md

> Claude Code loads this file via `CLAUDE.md` (`@AGENTS.md` import) — the two stay
> in sync. Edit **this** file, not `CLAUDE.md`.

## Tech Stack & Architecture
- Language/Version: Python 3.11+
- Core Libraries: `agent-utilities`, `fastmcp` (via `agent-utilities[mcp]`), `pydantic-ai`
- Domain: **local** Dell PowerEdge thermal control — `ipmitool` (fan) + `lm-sensors` (temperature). No remote API/credentials.
- Key principles: Functional patterns, Pydantic for data validation, asynchronous tool execution, action-routed MCP tools.

### Architecture Diagram
```mermaid
graph TD
    User([User/A2A]) --> Agent[Pydantic AI Agent]
    Agent --> MCP[MCP Server / FastMCP]
    MCP --> Temp[temperature tool — CONCEPT:FAN-001]
    MCP --> Fan[fan-control tool — CONCEPT:FAN-002]
    Temp --> Sensors([lm-sensors])
    Fan --> IPMI([BMC via ipmitool])
```

## Commands (run these exactly)
# Installation
pip install .[all]

# Quality & Linting (run from project root)
pre-commit run --all-files

# Execution Commands
# fan-manager        -> fan_manager.fan_manager:fan_manager   (CLI service)
# fan-manager-mcp    -> fan_manager.mcp_server:mcp_server      (MCP server)
# fan-manager-agent  -> fan_manager.agent_server:agent_server  (A2A agent)

## Project Structure Quick Reference
- Core logic → `fan_manager/fan_manager.py`
- MCP Entry Point → `fan_manager/mcp_server.py`
- Action-routed tools → `fan_manager/mcp/` (`mcp_temperature.py`, `mcp_fan_control.py`)
- Agent Entry Point → `fan_manager/agent_server.py`
- Local-command facade → `fan_manager/api_client.py`
- Concept registry → `docs/concepts.md` (`CONCEPT:FAN-*`)

### File Tree
```text
├── .bumpversion.cfg
├── .codespellignore
├── .dockerignore
├── .env.example
├── .gitattributes
├── .github/workflows/{docs.yml,pages.yml,pipeline.yml}
├── .gitignore
├── .pre-commit-config.yaml
├── AGENTS.md
├── CHANGELOG.md
├── CLAUDE.md
├── LICENSE
├── MANIFEST.in
├── README.md
├── docker/
│   ├── Dockerfile
│   ├── debug.Dockerfile
│   ├── mcp.compose.yml
│   ├── agent.compose.yml
│   └── starship.toml
├── docs/
│   ├── index.md
│   ├── overview.md
│   ├── installation.md
│   ├── usage.md
│   ├── deployment.md
│   └── concepts.md
├── fan_manager/
│   ├── __init__.py
│   ├── __main__.py
│   ├── fan_manager.py        # core logic (CLI, sensors, IPMI)
│   ├── api_client.py         # local-command facade (Api)
│   ├── models.py
│   ├── auth.py               # no-op/local auth
│   ├── middlewares.py
│   ├── mcp_server.py
│   ├── agent_server.py
│   ├── main_agent.json
│   ├── mcp_config.json
│   ├── agent_data/IDENTITY.md
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── mcp_temperature.py
│   │   └── mcp_fan_control.py
│   └── skills/
├── mcp_config.json
├── mkdocs.yml
├── pyproject.toml
├── pytest.ini
├── requirements.txt
├── scripts/                  # pre-commit verifiers (integration parity, sanitizer)
└── tests/
```

## Code Style & Conventions
**Always:**
- Use `agent-utilities` for common patterns (`create_mcp_server`, `create_agent_server`).
- Define input/output models using Pydantic (`fan_manager/models.py`).
- Include descriptive docstrings on all MCP tools (they are the LLM tool descriptions) and embed the `CONCEPT:FAN-*` id.
- Check for optional dependencies using `try/except ImportError`.

## Dos and Don'ts
**Do:**
- Run `pre-commit` before pushing changes.
- Keep tools focused, action-routed, and idempotent where possible.
- Wrap the real callables in `fan_manager/fan_manager.py` — never duplicate the logic.

**Don't:**
- Add new runtime deps without checking `optional-dependencies` first.
- Hardcode secrets; this tool needs none (it is local).
- Re-introduce a bespoke FastMCP server — register tools via `fan_manager/mcp/`.

## Safety & Boundaries
- Fan control issues raw IPMI commands; validate fan levels are within 0-100.
- On a temperature read failure during automatic control, fail safe to maximum fans.

**Never do:**
- Commit `.env` files or secrets.
- Modify `agent-utilities` or `universal-skills` files from within this package.

## ⛔ Keep the Repository Root Pristine
The repository ROOT must contain only canonical project files (packaging, config,
docs, lockfiles). The only hidden dirs allowed at root are `.git/`, `.github/`,
and `.specify/` (plus a local, git-ignored `.venv/`). Never write debug/scratch
scripts, logs, dumps, or build artifacts anywhere in the repo. Scratch goes in
`~/workspace/scratch/`; tests go in `tests/` (pytest).

## Working with Git Worktrees (multi-session)
Do not edit the canonical checkout — a background `repository-manager` sync can
reset its working tree. Take your own git worktree on your own branch under
`/home/apps/worktrees/`, commit often, then merge to main locally. Push only when
asked.
