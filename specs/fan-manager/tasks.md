# CONN-FAN-MANAGER — Implementation tasks

Governing spec: [spec.md](spec.md). Design: [plan.md](plan.md). Rows: [requirements.md](requirements.md).

- [x] `CONN-FAN-MANAGER-R001` — Ingest tools stay served. `tests/test_served_surface_keeps_ingest.py` rows R001.1 to R001.5 pass.
- [x] `CONN-FAN-MANAGER-R001.1` — Ingest actions served. `tests/test_served_surface_keeps_ingest.py::test_ingest_telemetry_actions_are_served_as_tools` must pass.
- [x] `CONN-FAN-MANAGER-R001.2` — Daemon loop is not a tool. `tests/test_served_surface_keeps_ingest.py::test_run_service_is_not_a_tool` must pass.
- [x] `CONN-FAN-MANAGER-R001.3` — SDK floor. `tests/test_served_surface_keeps_ingest.py::test_sdk_floor_is_declared_for_the_split_surface` must pass.
- [x] `CONN-FAN-MANAGER-R001.4` — Wiring. `tests/test_served_surface_keeps_ingest.py::test_client_lists_ingest_tools_through_the_real_server` must reach that call.
- [x] `CONN-FAN-MANAGER-R001.5` — Hot-path proof. `tests/test_served_surface_keeps_ingest.py::test_client_lists_ingest_tools_through_the_real_server` must pass.
