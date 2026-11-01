# CONN-FAN-MANAGER-CONNECTOR-CONTENT — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-FAN-MANAGER-CONNECTOR-CONTENT-R001` | **Default content.** `pyproject.toml` declares `fan-manager-mcp` as the single `scion_sdk.connector` entry point. The server lists the packaged `skill://` and `ontology://` resources and the packaged prompts with no `content=` argument. Proving test: `tests/test_default_content_surfaces.py`. Caller chain: the fan-manager-mcp console script (scion_sdk.cli:serve) loads the scion_sdk.connector entry point fan_manager:connector (fan_manager/__init__.py:90), whose SDK build_server serves the packaged skills, ontology and prompts as resources and prompts. Shape: no content= argument is passed to Connector in fan_manager/__init__.py; the SDK default content publishes fan_manager/skills, fan_manager/ontology/fan.ttl and fan_manager/prompts/thermal_specialist.json, and the test reuses the build_server and Client pattern of tests/test_served_surface_keeps_ingest.py. | `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. Planned test: `tests/test_default_content_surfaces.py::test_default_content_surfaces`. |
