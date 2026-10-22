# CONN-FAN-MANAGER — Test specification

Governing spec: [spec.md](spec.md).

| Requirement | Level | Proving test |
|---|---|---|
| `CONN-FAN-MANAGER-R001` | Unit | `tests/test_served_surface_keeps_ingest.py` rows R001.1 to R001.5 pass. |
| `CONN-FAN-MANAGER-R001.1` | Unit | `tests/test_served_surface_keeps_ingest.py::test_ingest_telemetry_actions_are_served_as_tools` must pass. |
| `CONN-FAN-MANAGER-R001.2` | Unit | `tests/test_served_surface_keeps_ingest.py::test_run_service_is_not_a_tool` must pass. |
| `CONN-FAN-MANAGER-R001.3` | Unit | `tests/test_served_surface_keeps_ingest.py::test_sdk_floor_is_declared_for_the_split_surface` must pass. |
| `CONN-FAN-MANAGER-R001.4` | Integration | `tests/test_served_surface_keeps_ingest.py::test_client_lists_ingest_tools_through_the_real_server` must reach that call. |
| `CONN-FAN-MANAGER-R001.5` | Integration | `tests/test_served_surface_keeps_ingest.py::test_client_lists_ingest_tools_through_the_real_server` must pass. |
| `CONN-FAN-MANAGER-R002` | Unit | `tests/test_fleet_endpoints.py` rows R002.1 to R002.3 pass. |
| `CONN-FAN-MANAGER-R002.1` | Integration | `tests/test_fleet_endpoints.py::test_node_endpoint_serves_reads_and_refuses_writes` must pass. |
| `CONN-FAN-MANAGER-R002.2` | Unit | `tests/test_fleet_endpoints.py::test_node_read_operations_are_reads_only` must pass. |
| `CONN-FAN-MANAGER-R002.3` | Integration | `tests/test_fleet_endpoints.py::test_node_endpoint_requires_the_token` must pass. |
| `CONN-FAN-MANAGER-R003` | Unit | `tests/test_fleet_endpoints.py` rows R003.1 to R003.5 pass. |
| `CONN-FAN-MANAGER-R003.1` | Integration | `tests/test_fleet_endpoints.py::test_connector_aggregates_temperature_by_node` must pass. |
| `CONN-FAN-MANAGER-R003.2` | Integration | `tests/test_fleet_endpoints.py::test_connector_routes_inband_ipmi_reads` must pass. |
| `CONN-FAN-MANAGER-R003.3` | Unit | `tests/test_fleet_endpoints.py::test_connector_never_fans_out_writes` must pass. |
| `CONN-FAN-MANAGER-R003.4` | Unit | `tests/test_fleet_endpoints.py::test_unreachable_node_is_reported_not_raised` must pass. |
| `CONN-FAN-MANAGER-R003.5` | Unit | `tests/test_fleet_endpoints.py::test_hosts_map_through_the_url_template` must pass. |
| `CONN-FAN-MANAGER-R004` | Unit | `tests/test_engine_identity.py::test_trend_ingest_signs_as_the_configured_principal_and_audience` must pass. |
| `CONN-FAN-MANAGER-R005` | Unit | `tests/test_ingest_connector_name.py::test_ingest_binding_uses_the_onboarded_connector_name` must pass. |

The tests run against the production server object. They need no vendor requests.
