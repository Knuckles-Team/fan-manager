# CONN-FAN-MANAGER — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-FAN-MANAGER-R001` | **Ingest tools stay served.** The server must serve `fan_ingest_telemetry` as one tool per action on the SDK split surface. | `tests/test_served_surface_keeps_ingest.py` rows R001.1 to R001.5 pass. |
| `CONN-FAN-MANAGER-R001.1` | **Ingest actions served.** The served set must contain `fan_ingest_telemetry_temperature` and `fan_ingest_telemetry_sensors`. | `tests/test_served_surface_keeps_ingest.py::test_ingest_telemetry_actions_are_served_as_tools` must pass. |
| `CONN-FAN-MANAGER-R001.2` | **Daemon loop is not a tool.** The served set must not contain a tool for `run_service`, because the daemon loop runs as the CLI service. | `tests/test_served_surface_keeps_ingest.py::test_run_service_is_not_a_tool` must pass. |
| `CONN-FAN-MANAGER-R001.3` | **SDK floor.** The package must require `agent-connector-sdk[mcp]>=0.3.8,<1.0.0` in `pyproject.toml`, because older releases drop the ingest tools. | `tests/test_served_surface_keeps_ingest.py::test_sdk_floor_is_declared_for_the_split_surface` must pass. |
| `CONN-FAN-MANAGER-R001.4` | **Wiring.** `fan_manager/mcp_server.py:69` must call `register_tool_surface` with the temperature, fan-control, and knowledge-graph tool registries. | `tests/test_served_surface_keeps_ingest.py::test_client_lists_ingest_tools_through_the_real_server` must reach that call. |
| `CONN-FAN-MANAGER-R001.5` | **Hot-path proof.** An MCP client connected to the production server object must list 39 tools, including both ingest tools. | `tests/test_served_surface_keeps_ingest.py::test_client_lists_ingest_tools_through_the_real_server` must pass. |
