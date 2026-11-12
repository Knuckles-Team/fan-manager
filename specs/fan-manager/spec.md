# CONN-FAN-MANAGER — Fan manager served tool surface and node endpoints

## Outcome

The connector must serve the telemetry ingest operations as typed tools beside the fan, temperature, and IPMI tools.
The served surface holds 35 tools, including `fan_ingest_telemetry_temperature` and `fan_ingest_telemetry_sensors`.

The connector runs away from the servers it reads. Each fan-manager daemon runs on one server, next to that server's BMC.
Each daemon must serve a read-only endpoint for its own BMC (R002). The connector must read every node through those endpoints
and return the answers keyed by node (R003). Writes must never travel over the node endpoints.

## Scope and owner

The `fan-manager` repository owns this behavior. The shared connector SDK owns the tool-surface mechanism.
The shared pipelines repository owns quality gates and delivery rendering.

Component: Connector integration
References: [Connector SDK](https://github.com/Knuckles-Team/scion-sdk/blob/main/README.md)
Code: ../../fan_manager/node_api.py ../../fan_manager/fleet.py ../../fan_manager/mcp_server.py:69 ../../fan_manager/mcp/mcp_kg.py ../../tests/test_served_surface_keeps_ingest.py ../../pyproject.toml ../../fan_manager/fan_manager.py:75 ../../tests/test_engine_identity.py

## Non-goals

This specification grants no service access, credential creation, deployment, or approval exception.
The connector must not implement a graph engine, a policy authority, or a duplicate shared SDK runtime.

## Why a new spec

The search `git grep -n ingest -- specs` found no spec in this repository. The `specs/` tree holds only the template. No other repository owns the fan manager tool surface.

## Requirements

See [requirements.md](requirements.md), [plan.md](plan.md), and [test-spec.md](test-spec.md).

## Scope and interfaces

In scope: the rows of [requirements.md](requirements.md). Out of scope: the SDK modules and the engine, which own the shared capabilities.

## User Scenarios & Testing

### User Story 1 - Fan manager served tool surface and node endpoints (Priority: P1)

The connector must serve the telemetry ingest operations as typed tools beside the fan, temperature, and IPMI tools.

**Acceptance Scenarios**:

1. **Given** the connector is configured, **When** the behaviour of row `CONN-FAN-MANAGER-R001` (ingest tools stay served) is exercised, **Then** `tests/test_served_surface_keeps_ingest.py` rows R001.1 to R001.5 pass.
2. **Given** the connector is configured, **When** the behaviour of row `CONN-FAN-MANAGER-R002` (per-node read endpoint) is exercised, **Then** `tests/test_fleet_endpoints.py` rows R002.1 to R002.3 pass.
3. **Given** the connector is configured, **When** the behaviour of row `CONN-FAN-MANAGER-R003` (connector aggregation) is exercised, **Then** `tests/test_fleet_endpoints.py` rows R003.1 to R003.5 pass.

### Edge Cases

- If `CONN-FAN-MANAGER-R001` is not met, its proving test fails: ingest tools stay served.
- If `CONN-FAN-MANAGER-R002` is not met, its proving test fails: per-node read endpoint.
- If `CONN-FAN-MANAGER-R003` is not met, its proving test fails: connector aggregation.

## Requirements

- **FR-001**: Ingest tools stay served. Rows: `CONN-FAN-MANAGER-R001`.
- **FR-002**: Per-node read endpoint. Rows: `CONN-FAN-MANAGER-R002`.
- **FR-003**: Connector aggregation. Rows: `CONN-FAN-MANAGER-R003`.
- **FR-004**: Engine identity. Rows: `CONN-FAN-MANAGER-R004`.
- **FR-005**: Ingest connector name. Rows: `CONN-FAN-MANAGER-R005`.

## Success Criteria

- **SC-001**: `tests/test_served_surface_keeps_ingest.py` rows R001.1 to R001.5 pass. Rows: `CONN-FAN-MANAGER-R001`.
- **SC-002**: `tests/test_fleet_endpoints.py` rows R002.1 to R002.3 pass. Rows: `CONN-FAN-MANAGER-R002`.
- **SC-003**: `tests/test_fleet_endpoints.py` rows R003.1 to R003.5 pass. Rows: `CONN-FAN-MANAGER-R003`.
- **SC-004**: `tests/test_engine_identity.py::test_trend_ingest_signs_as_the_configured_principal_and_audience` must pass. Rows: `CONN-FAN-MANAGER-R004`.
- **SC-005**: `tests/test_ingest_connector_name.py::test_ingest_binding_uses_the_onboarded_connector_name` must pass. Rows: `CONN-FAN-MANAGER-R005`.

## Assumptions

- The external system is reachable with operator-supplied credentials.
- The SDK and engine contracts the rows cite are at the floors declared in `pyproject.toml`.

## Traceability

| Label | Rows | Design section | Test ID | Evidence |
|---|---|---|---|---|
| FR-001 | `CONN-FAN-MANAGER-R001` | [plan.md](plan.md) | T-001 | [test-spec.md](test-spec.md) |
| FR-002 | `CONN-FAN-MANAGER-R002` | [plan.md](plan.md) | T-002 | [test-spec.md](test-spec.md) |
| FR-003 | `CONN-FAN-MANAGER-R003` | [plan.md](plan.md) | T-003 | [test-spec.md](test-spec.md) |
| FR-004 | `CONN-FAN-MANAGER-R004` | [plan.md](plan.md) | T-004 | [test-spec.md](test-spec.md) |
| FR-005 | `CONN-FAN-MANAGER-R005` | [plan.md](plan.md) | T-005 | [test-spec.md](test-spec.md) |
