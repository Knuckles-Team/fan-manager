# CONN-FAN-MANAGER — Implementation plan

Governing spec: [spec.md](spec.md). Rows: [requirements.md](requirements.md).

## Summary

`fan_manager/mcp/mcp_kg.py` defines `fan_ingest_telemetry`, which routes an `action` of `temperature` or `sensors`. The shared SDK's `register_tool_surface` splits it into one tool per action. The connector adds no splitting code. The connector depends only on the shared SDK. The shared SDK owns tool naming and registration. The connector owns the IPMI operations, the fan-control logic, and the telemetry ingest actions.

## Technical Context

- **Language/Version**: Python 3.14 (floor 3.12)
- **Primary Dependencies**: scion-sdk, fastmcp
- **Storage**: N/A; the connector stores nothing
- **Testing**: pytest; the proof level each row names
- **Target Platform**: Linux containers
- **Project Type**: connector (MCP server)
- **Performance Goals**: N/A
- **Constraints**: one tool per API operation; shared capabilities come from the SDK
- **Scale/Scope**: 18 rows

## Constitution Check

- One owner per concept: pass. The connector owns one external system's calls, mappings and tools only.
- Connectors depend on the SDK and are called through arbora: pass.
- No ratchets: pass. The rows add no suppression.

## Project Structure

```text
pyproject.toml  existing
fan_manager/node_api.py  existing
fan_manager/fleet.py  existing
fan_manager/kg_ingest.py  existing
```

## Phase 0: Research

No unknowns. Each row names the code it touches.

## Phase 1: Design

### Interfaces and data model

The served set holds 39 tools: the temperature tools, the fan-control tools, the IPMI tools, and the two ingest tools.
The package requires `scion-sdk[mcp]>=0.3.10,<1.0.0`. An older shared SDK drops `fan_ingest_telemetry` from the served surface.

### Node endpoints and aggregation (R002, R003)

Problem: the daemon set reads IPMI on each node, but it exposes no port. The connector Deployment has no BMC device, so every
in-band read in its pod fails.

Decision: each daemon pod serves a read-only HTTP endpoint (`fan_manager/node_api.py`) on `FAN_MANAGER_NODE_API_PORT`,
started by the `fan-manager` CLI in a background thread. The daemon pods use the host network, so each endpoint listens on its node's own address.
The connector keeps `FAN_MANAGER_HOSTS` as the node names (the same names the derivation pass uses) and adds
`FAN_MANAGER_NODE_URL_TEMPLATE`, which maps a name to its endpoint. `fan_manager/fleet.py` runs the read on every node in
parallel. A headless Service over host-network daemon pods gives no per-pod name, so it adds no endpoint the connector
could address; the node address is the per-node endpoint.

- Read tools keep their names and schemas. The served tool count stays 39, so the pack does not change.
- `fan_manager_get_temp` and every IPMI read called without `host` return `{"response": {<node>: <answer>}, "nodes", "nodes_ok"}`.
- The node endpoint serves `GET` only. Its operation set names no write. Writes need an explicit out-of-band `host` and
  BMC credentials, as before.
- `FAN_MANAGER_NODE_API_TOKEN`, when set on both sides, is required as a bearer token. Host-network pods are not covered
  by a network policy, so the token is the access control for the node port.

Alternative rejected: run the MCP server itself as the daemon set, with one arbora registration per node. That needs one
served server and one pack per node, and it gives no single cross-node answer.

### Live integration path

Entry point: `fan_manager.mcp_server:get_mcp_instance`, run by the `fan-manager-mcp` console script.
It calls `create_mcp_server`, then `register_tool_surface` at `fan_manager/mcp_server.py:69`.

### Quality and release gates

Run `pytest tests/test_served_surface_keeps_ingest.py` and `pipelines-hook spec-standard`.

### Risks, alternatives, and decisions

An SDK below 0.3.10 serves no ingest tools and ignores the engine audience. `R001.3` guards the floor, and `R001.1` guards the served names.

## Phase 2: Task approach

`tasks.md` holds one task line per row, producer first.

## Complexity Tracking

None. The constitution check passed.

## Build contract

The repository pre-commit hooks apply: `ruff-format`, `connector-standard`, `secrets`, `tests-fast`. Each row names its proving test. No suppression and no duplicate implementation.

## Production caller chain

1. `CONN-FAN-MANAGER-R001.1`: the fan-manager-mcp console script (scion_sdk.cli:serve) loads fan_manager:connector (fan_manager/__init__.py:90), whose tool_registry TOOL_REGISTRY (fan_manager/mcp_server.py) registers register_kg_tools (fan_manager/mcp/mcp_kg.py:26), defining fan_ingest_telemetry at mcp_kg.py:28.
2. `CONN-FAN-MANAGER-R001.2`: fan_manager:connector (fan_manager/__init__.py:90) passes api=_OperationApi (fan_manager/mcp_server.py:33) to Connector, so the SDK surface built for the fan-manager-mcp console script has no run_service method; the CLI fan-manager entry point fan_manager.fan_manager:fan_manager (fan_manager/fan_manager.py:501) runs the loop.
3. `CONN-FAN-MANAGER-R001.3`: the dependency pin in pyproject.toml (dependencies list) is resolved at install time, and scion_sdk.cli:serve behind the fan-manager-mcp console script relies on the SDK split surface it provides.
4. `CONN-FAN-MANAGER-R001.4`: the fan-manager-mcp console script (scion_sdk.cli:serve) loads fan_manager:connector (fan_manager/__init__.py:90), whose tool_registry=tuple(TOOL_REGISTRY) from fan_manager/mcp_server.py names register_temperature_tools, register_fan_control_tools and register_kg_tools; the SDK registers them through register_tool_surface.
5. `CONN-FAN-MANAGER-R001.5`: the fan-manager-mcp console script (scion_sdk.cli:serve) builds the server from fan_manager:connector (fan_manager/__init__.py:90); an MCP client lists tools over that server, as the test does through scion_sdk.connector.build_server("fan_manager").
6. `CONN-FAN-MANAGER-R002.1`: the fan-manager console script (fan_manager.fan_manager:fan_manager, fan_manager/fan_manager.py:501) calls start_from_env (fan_manager/node_api.py:138) at fan_manager.py:584, which starts make_server (node_api.py:123) with _Handler.do_GET (node_api.py:98) and _refuse (node_api.py:117) for other methods.
7. `CONN-FAN-MANAGER-R002.2`: the fan-manager console script (fan_manager/fan_manager.py:501) starts the node endpoint through start_from_env (fan_manager/node_api.py:138); _Handler.do_GET (node_api.py:98) dispatches only names found in READ_OPERATIONS (node_api.py:42).
8. `CONN-FAN-MANAGER-R002.3`: the fan-manager console script (fan_manager/fan_manager.py:501) starts the node endpoint through start_from_env (fan_manager/node_api.py:138), which passes FAN_MANAGER_NODE_API_TOKEN to make_server; _Handler.do_GET (node_api.py:98) answers 401 when _authorized (node_api.py:92) fails, after answering /health.
9. `CONN-FAN-MANAGER-R003.1`: the fan-manager-mcp tool fan_manager_get_temp (action-routed in fan_manager/mcp/mcp_temperature.py:54) calls Api.get_temp (fan_manager/api_client.py:60), which calls fleet.read_all (fan_manager/fleet.py:71) when fleet.enabled (fleet.py:42).
10. `CONN-FAN-MANAGER-R003.2`: the fan_manager_ipmi_* tools registered through verbose_targets in fan_manager:connector (fan_manager/__init__.py:90) call IpmiApi methods such as power_status (fan_manager/ipmi_api.py:45) and sensors reads, which call fleet.read_all (fan_manager/fleet.py:71) when host is None and fleet.enabled.
11. `CONN-FAN-MANAGER-R003.3`: IpmiApi write methods such as power_on (fan_manager/ipmi_api.py:55), reached through the fan_manager_ipmi_* tools of fan_manager:connector, call _write_guard (ipmi_api.py:21) before ipmi.power; no write path calls fleet.read_all.
12. `CONN-FAN-MANAGER-R003.4`: Api.get_temp (fan_manager/api_client.py:60) and the IpmiApi reads call fleet.read_all (fan_manager/fleet.py:71), which uses _fetch (fleet.py:47) per node.
13. `CONN-FAN-MANAGER-R003.5`: fleet.enabled (fan_manager/fleet.py:42) is called by Api.get_temp (fan_manager/api_client.py:65) and IpmiApi reads, and calls node_endpoints (fleet.py:26) to turn FAN_MANAGER_HOSTS into URLs.
14. `CONN-FAN-MANAGER-R004`: the fan-manager console script (fan_manager.fan_manager:fan_manager, fan_manager/fan_manager.py:501) runs run_service, which calls ingest_thermal_trend (fan_manager/kg_ingest.py:235) through asyncio.run at fan_manager.py:75.
15. `CONN-FAN-MANAGER-R005`: ingest_thermal_trend (fan_manager/kg_ingest.py:235), called from run_service in fan_manager/fan_manager.py:75 and from the fan_ingest_telemetry tool, writes through the module-level STREAM (kg_ingest.py:26).

## Cross-repo seams

none
