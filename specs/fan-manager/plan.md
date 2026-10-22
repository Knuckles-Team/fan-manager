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

## Node endpoints and aggregation (R002, R003)

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

## Live integration path

Entry point: `fan_manager.mcp_server:get_mcp_instance`, run by the `fan-manager-mcp` console script.
It calls `create_mcp_server`, then `register_tool_surface` at `fan_manager/mcp_server.py:69`.

## Quality and release gates

Run `pytest tests/test_served_surface_keeps_ingest.py` and `pipelines-hook spec-standard`.

## Risks, alternatives, and decisions

An SDK below 0.3.8 serves no ingest tools. `R001.3` guards the floor, and `R001.1` guards the served names.
