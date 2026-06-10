# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-06-10

### Added

- Action-routed dynamic MCP tools (`temperature`, `fan-control`) under
  `fan_manager/mcp/`, gated behind `TEMPERATURETOOL` / `FANCONTROLTOOL`.
- A2A agent server (`fan-manager-agent`) with `agent_data/IDENTITY.md` and an
  externalized system prompt in `prompts/main_agent.md`.
- Local-command facade `fan_manager.api_client.Api` and Pydantic `models`.
- Concept registry `CONCEPT:FAN-001` (Temperature) and `CONCEPT:FAN-002`
  (Fan Control), traced across code docstrings, `docs/concepts.md`, and
  `@pytest.mark.concept` test markers.
- Injectable `CommandRunner` seam for the `sensors`/`ipmitool` shell-out so the
  fan-control and temperature paths can be tested without monkeypatching
  `subprocess` globally.
- Negative-path, boundary, and contract tests for the action-routed MCP tools.
- Complete Environment Variables reference in `README.md` and `.env.example`.
- `logfire` observability dependency in the `agent` extra.
- Standardized docs site, Docker images, and packaging metadata.

### Changed

- Rebuilt `mcp_server.py` on `agent-utilities.create_mcp_server` (was a bespoke
  FastMCP server in `fan_manager_mcp.py`).
- Migrated the core dependency from `fastmcp` to `agent-utilities` (with
  `mcp`/`agent` extras); raised `requires-python` to `>=3.11,<3.15`.
- Cross-project concept references in `docs/concepts.md` are now listed as
  external bridge IDs (without the `CONCEPT:` marker prefix) so traceability
  tooling treats them as external rather than orphaned local concepts.

### Removed

- Legacy `fan_manager/fan_manager_mcp.py` (folded into the modular MCP layout).

## [1.0.9] - 2024-05-08

### Added

- Initial release: CLI fan controller and FastMCP server for Dell PowerEdge.
