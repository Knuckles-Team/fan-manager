# CONN-FAN-MANAGER — Quickstart

The shortest path that shows the served behaviour working.

- `CONN-FAN-MANAGER-R001`: run `pytest tests/test_served_surface_keeps_ingest.py`.
- `CONN-FAN-MANAGER-R001.1`: run `pytest tests/test_served_surface_keeps_ingest.py::test_ingest_telemetry_actions_are_served_as_tools`.
- `CONN-FAN-MANAGER-R001.2`: run `pytest tests/test_served_surface_keeps_ingest.py::test_run_service_is_not_a_tool`.
- `CONN-FAN-MANAGER-R001.5`: run `pytest tests/test_served_surface_keeps_ingest.py::test_client_lists_ingest_tools_through_the_real_server`.
- `CONN-FAN-MANAGER-R002.1`: run `pytest tests/test_fleet_endpoints.py::test_node_endpoint_serves_reads_and_refuses_writes`.
