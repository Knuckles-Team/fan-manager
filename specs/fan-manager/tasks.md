# CONN-FAN-MANAGER — Implementation tasks

Governing spec: [spec.md](spec.md). Design: [plan.md](plan.md). Rows: [requirements.md](requirements.md).

- [x] `CONN-FAN-MANAGER-R001` — Ingest tools stay served. `tests/test_served_surface_keeps_ingest.py` rows R001.1 to R001.5 pass.
- [x] `CONN-FAN-MANAGER-R001.1` — Ingest actions served. `tests/test_served_surface_keeps_ingest.py::test_ingest_telemetry_actions_are_served_as_tools` must pass.
- [x] `CONN-FAN-MANAGER-R001.2` — Daemon loop is not a tool. `tests/test_served_surface_keeps_ingest.py::test_run_service_is_not_a_tool` must pass.
- [x] `CONN-FAN-MANAGER-R001.3` — Scion (SDK) floor. `tests/test_served_surface_keeps_ingest.py::test_sdk_floor_is_declared_for_the_split_surface` must pass.
- [x] `CONN-FAN-MANAGER-R001.4` — Wiring. `tests/test_served_surface_keeps_ingest.py::test_client_lists_ingest_tools_through_the_real_server` must reach that call.
- [x] `CONN-FAN-MANAGER-R001.5` — Hot-path proof. `tests/test_served_surface_keeps_ingest.py::test_client_lists_ingest_tools_through_the_real_server` must pass.
- [x] `CONN-FAN-MANAGER-R002` — Per-node read endpoint. `tests/test_fleet_endpoints.py` rows R002.1 to R002.3 pass.
- [x] `CONN-FAN-MANAGER-R002.1` — Reads served, writes refused. `tests/test_fleet_endpoints.py::test_node_endpoint_serves_reads_and_refuses_writes` must pass.
- [x] `CONN-FAN-MANAGER-R002.2` — Read operations only. `tests/test_fleet_endpoints.py::test_node_read_operations_are_reads_only` must pass.
- [x] `CONN-FAN-MANAGER-R002.3` — Bearer token. `tests/test_fleet_endpoints.py::test_node_endpoint_requires_the_token` must pass.
- [x] `CONN-FAN-MANAGER-R003` — Connector aggregation. `tests/test_fleet_endpoints.py` rows R003.1 to R003.5 pass.
- [x] `CONN-FAN-MANAGER-R003.1` — Temperature by node. `tests/test_fleet_endpoints.py::test_connector_aggregates_temperature_by_node` must pass.
- [x] `CONN-FAN-MANAGER-R003.2` — In-band IPMI reads by node. `tests/test_fleet_endpoints.py::test_connector_routes_inband_ipmi_reads` must pass.
- [x] `CONN-FAN-MANAGER-R003.3` — Writes stay guarded. `tests/test_fleet_endpoints.py::test_connector_never_fans_out_writes` must pass.
- [x] `CONN-FAN-MANAGER-R003.4` — Dead node is typed. `tests/test_fleet_endpoints.py::test_unreachable_node_is_reported_not_raised` must pass.
- [x] `CONN-FAN-MANAGER-R003.5` — Node names to endpoints. `tests/test_fleet_endpoints.py::test_hosts_map_through_the_url_template` must pass.
- [x] `CONN-FAN-MANAGER-R004` — Engine identity. `tests/test_engine_identity.py::test_trend_ingest_signs_as_the_configured_principal_and_audience` must pass.
- [x] `CONN-FAN-MANAGER-R005` — Ingest connector name. `tests/test_ingest_connector_name.py::test_ingest_binding_uses_the_onboarded_connector_name` must pass.
