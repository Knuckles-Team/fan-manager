---
name: fan-manager-development
skill_type: skill
description: >-
  Develop and release the fan-manager connector. Use this skill for changes to
  its local hardware facade, MCP tools, typed telemetry ingestion, packaged
  skills, or the standard release gates.
domain: development
license: MIT
tags: [fan-manager, dell, ipmi, sensors, mcp, knowledge-graph, rapid-delivery]
metadata:
  author: Knuckles-Team
  version: '1.0.0'
---

# Fan Manager development

Use this skill from a fan-manager checkout before changing the connector. Read
`AGENTS.md` first: it defines the local hardware boundary, worktree discipline,
quality gates, version/lock policy, and release ownership.

## Repository and runtime map

- `fan_manager/fan_manager.py` owns the local `sensors -j` temperature path,
  bounded 0-100 fan writes, automatic fan curve, and the injected
  `CommandRunner` seam. Fixed argv with `shell=False` is the hardware boundary.
- `fan_manager/api_client.py` is the thin `Api` facade over
  `FanControlService`; `fan_manager/services/fan_control_service.py` owns
  dependency-injected temperature and fan-control calls.
- `fan_manager/mcp_server.py` builds the MCP surface. Domain registrars in
  `fan_manager/mcp/mcp_temperature.py`,
  `fan_manager/mcp/mcp_fan_control.py`, and `fan_manager/mcp/mcp_kg.py`
  expose one action-routed tool per domain through `TOOL_REGISTRY`.
- `fan_manager/connector_sources.py` declares the live `fan-sensors` source;
  `fan_manager/kg_ingest.py` maps telemetry to typed `ManagedHost`,
  `FanController`, `TemperatureReading`, `FanSpeedSetting`, and
  `SensorReading` nodes through the SDK ingest stream.
- Packaged content lives below `fan_manager/skills/`, `prompts/`, and
  `ontology/`. `pyproject.toml` must continue to include `skills/**` in
  setuptools package data.

## Local and security contract

Fan Manager is a local hardware connector. `fan_manager/auth.py` returns the
local `Api` facade and resolves only `IPMITOOL_PATH` and `SENSORS_PATH`; it does
not accept a remote URL or credentials. Preserve this boundary when editing
code or documentation.

The runtime may read `FAN_MANAGER_HOST`, `FAN_MANAGER_HOSTS`,
`FAN_MANAGER_NODE_API_BIND`, `FAN_MANAGER_NODE_API_PORT`,
`FAN_MANAGER_NODE_API_TOKEN`, `FAN_MANAGER_NODE_URL_TEMPLATE`,
`FAN_MANAGER_KG_INGEST`, `FAN_MANAGER_KG_AGGREGATE_S`,
`FAN_MANAGER_POLICY_FILE`, `FAN_MANAGER_POLICY_REFRESH`,
`FAN_MANAGER_CURVE`, and `FAN_MANAGER_NOTIFY_URL`. Treat values as runtime
configuration, never as secrets to embed in this skill. Keep node reads
read-only and require one explicit out-of-band target for write operations.
The MCP domains are gated by `TEMPERATURETOOL`, `FAN_CONTROLTOOL`, and
`KGTOOL`; preserve the inherited `MCP_TOOL_MODE` surface and the existing
`scion_sdk` registration path.

## Rapid delivery: the 5-minute contract

Specs are already designed. Deliver one small, reviewable slice and bind it to
`PIPE-CONNSPEC-R120.4` in the focused test and commit trailer.

1. Start from an immutable `origin/main` fan-manager revision in a private real
   worktree. Read the owning spec row in the central pipelines repository and
   do not edit central status, runtime manifests, or deployment files here.
2. Find and reuse the existing facade, registrar, source declaration, and
   SDK-ingest seam before adding code. Keep local sensor/BMC commands fixed,
   validate fan levels before execution, and preserve fail-safe maximum fans on
   an automatic-control temperature failure.
3. For MCP changes, test registration and action routing through the public
   FastMCP surface. Keep unknown actions and malformed JSON on their existing
   structured/error paths; do not broaden tools or bypass the domain toggles.
4. For ingestion changes, preserve source IDs and typed node names from
   `connector_sources.py`/`kg_ingest.py`. Never add a local graph client or
   direct database write.
5. For packaged content, add the focused package-content test in `tests/` and
   verify `pyproject.toml` still includes `skills/**`. If the public package
   content changes, use the repository's established patch-version release
   procedure, update `CHANGELOG.md`, and refresh `uv.lock` in the same change.
6. Run the focused test plus the configured pre-commit commit and push stages
   against the frozen range. Inspect the built wheel/sdist when content is
   released; Pages, container rendering, and publication are separate hosted
   gates and cannot be inferred from a local test.

## Focused validation

```bash
uv run --locked --extra test pytest -q tests/test_fan_manager_development_skill.py
uvx pre-commit run --all-files
uv build --wheel --sdist
```

Run hardware-facing tests only with the injected runner or existing mocks. Do
not call a real BMC, persist tokens, or claim package/Pages/container
publication from a local checkout. Record the exact source SHA, focused result,
pre-commit result, and any hosted evidence in the delivery receipt.

## Publication references

The standard callers are `.github/workflows/pipeline.yml` with
`python_pipeline.yml@main` and `connector: true`,
`container_pipeline.yml@main` with `render_connector: true`, and
`pages.yml` with `pages_pipeline.yml@main`. Keep public-first version guards,
source provenance, and the package-data boundary intact; a development-skill
change alone does not prove a Pages or image release.
