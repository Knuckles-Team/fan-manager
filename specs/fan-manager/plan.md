# CONN-FAN-MANAGER — Design and implementation plan

Governing spec: [spec.md](spec.md).

## Existing system and reuse

`fan_manager/mcp/mcp_kg.py` defines `fan_ingest_telemetry`, which routes an `action` of `temperature` or `sensors`.
The shared SDK `register_tool_surface` splits it into one tool per action. The connector adds no splitting code.

## Architecture

The connector depends on the shared SDK only. The SDK owns tool naming and registration.
The connector owns the IPMI operations, the fan-control logic, and the telemetry ingest actions.

## Interfaces and data model

The served set holds 39 tools: the temperature tools, the fan-control tools, the IPMI tools, and the two ingest tools.
The package requires `agent-connector-sdk[mcp]>=0.3.8,<1.0.0`. An older SDK drops `fan_ingest_telemetry` from the served surface.

## Live integration path

Entry point: `fan_manager.mcp_server:get_mcp_instance`, run by the `fan-manager-mcp` console script.
It calls `create_mcp_server`, then `register_tool_surface` at `fan_manager/mcp_server.py:69`.

## Quality and release gates

Run `pytest tests/test_served_surface_keeps_ingest.py` and `pipelines-hook spec-standard`.

## Risks, alternatives, and decisions

An SDK below 0.3.8 serves no ingest tools. `R001.3` guards the floor, and `R001.1` guards the served names.
