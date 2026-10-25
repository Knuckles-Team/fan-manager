# CONN-FAN-MANAGER — Fan manager served tool surface and node endpoints

## Outcome

The connector must serve the telemetry ingest operations as typed tools beside the fan, temperature, and IPMI tools.
The served surface holds 39 tools, including `fan_ingest_telemetry_temperature` and `fan_ingest_telemetry_sensors`.

The connector runs away from the servers it reads. Each fan-manager daemon runs on one server, next to that server's BMC.
Each daemon must serve a read-only endpoint for its own BMC (R002). The connector must read every node through those endpoints
and return the answers keyed by node (R003). Writes must never travel over the node endpoints.

## Scope and owner

The `fan-manager` repository owns this behavior. The shared connector Scion (SDK) owns the tool-surface mechanism.
The shared pipelines repository owns quality gates and delivery rendering.

Component: Connector integration
References: [Connector Scion (SDK)](https://github.com/Knuckles-Team/agent-connector-sdk/blob/main/README.md)
Code: ../../fan_manager/node_api.py ../../fan_manager/fleet.py ../../fan_manager/mcp_server.py:69 ../../fan_manager/mcp/mcp_kg.py ../../tests/test_served_surface_keeps_ingest.py ../../pyproject.toml ../../fan_manager/fan_manager.py:75 ../../tests/test_engine_identity.py

## Non-goals

This specification grants no service access, credential creation, deployment, or approval exception.
The connector must not implement a graph engine, a policy authority, or a duplicate Scion (SDK) runtime.

## Why a new spec

The search `git grep -n ingest -- specs` found no spec in this repository. The `specs/` tree holds only the template. No other repository owns the fan manager tool surface.

## Requirements

See [requirements.md](requirements.md), [plan.md](plan.md), and [test-spec.md](test-spec.md).
