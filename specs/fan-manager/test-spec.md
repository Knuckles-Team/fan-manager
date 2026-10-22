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

The tests run against the production server object. They need no vendor requests.
