# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Action-routed dynamic MCP tools (`temperature`, `fan-control`) under
  `fan_manager/mcp/`, gated behind `TEMPERATURETOOL` / `FANCONTROLTOOL`.
- A2A agent server (`fan-manager-agent`) with `agent_data/IDENTITY.md`.
- Local-command facade `fan_manager.api_client.Api` and Pydantic `models`.
- Concept registry `CONCEPT:FAN-001` (Temperature), `CONCEPT:FAN-002` (Fan Control).
- Standardized docs site, Docker images, and packaging metadata.

### Changed
- Rebuilt `mcp_server.py` on `agent-utilities.create_mcp_server` (was a bespoke
  FastMCP server in `fan_manager_mcp.py`).
- Migrated core dependency from `fastmcp` to `agent-utilities` (with `mcp`/`agent`
  extras); raised `requires-python` to `>=3.11,<3.15`.

### Removed
- Legacy `fan_manager/fan_manager_mcp.py` (folded into the modular MCP layout).

## [1.0.9]

### Added
- Initial release: CLI fan controller and FastMCP server for Dell PowerEdge.
