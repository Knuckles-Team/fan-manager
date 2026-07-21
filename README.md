# Fan Manager
## CLI | MCP | Agent

![PyPI - Version](https://img.shields.io/pypi/v/fan-manager)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
![PyPI - Downloads](https://img.shields.io/pypi/dd/fan-manager)
![GitHub Repo stars](https://img.shields.io/github/stars/Knuckles-Team/fan-manager)
![GitHub forks](https://img.shields.io/github/forks/Knuckles-Team/fan-manager)
![GitHub contributors](https://img.shields.io/github/contributors/Knuckles-Team/fan-manager)
![PyPI - License](https://img.shields.io/pypi/l/fan-manager)
![GitHub](https://img.shields.io/github/license/Knuckles-Team/fan-manager)
![GitHub last commit (by committer)](https://img.shields.io/github/last-commit/Knuckles-Team/fan-manager)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Knuckles-Team/fan-manager)
![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed/Knuckles-Team/fan-manager)
![GitHub issues](https://img.shields.io/github/issues/Knuckles-Team/fan-manager)
![GitHub top language](https://img.shields.io/github/languages/top/Knuckles-Team/fan-manager)
![GitHub language count](https://img.shields.io/github/languages/count/Knuckles-Team/fan-manager)
![GitHub repo size](https://img.shields.io/github/repo-size/Knuckles-Team/fan-manager)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/fan-manager)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/fan-manager)

*Version: 1.7.0*

> **Documentation** — Installation, deployment, and usage across the CLI and MCP
> interfaces, plus the integrated A2A agent server, are maintained in the
> [official documentation](https://knuckles-team.github.io/fan-manager/).

---

## Overview

**Fan Manager** controls the fan speed of Dell PowerEdge servers based on CPU
temperature. It is a **local** tool: it reads temperatures via `lm-sensors`
(`sensors -j`) and drives the server's BMC via `ipmitool` raw commands. It ships
as a CLI, a Model Context Protocol (MCP) server, and an integrated A2A agent for
the [`agent-utilities`](https://github.com/Knuckles-Team/agent-utilities) ecosystem.

Because fan control happens against the local host, **no service URL or token is
required** — the connector degrades to a no-op/local config for authentication.

---

## Key Features

- **Temperature-Driven Curve:** Logarithmic CPU-temperature-to-fan-speed scaling with configurable min/max bounds and intensity.
- **Consolidated Action-Routed MCP Tools:** Two togglable tool modules (`temperature`, `fan-control`) minimize token overhead in LLM contexts.
- **Fail-Safe Defaults:** On a temperature read error during automatic control, the fans default to maximum.
- **Integrated Agent:** Built-in Pydantic AI agent supporting the Agent Control Protocol (ACP) and Web UI (AG-UI).

---

## CLI

The classic continuous service that polls temperature and adjusts the fans:

```bash
fan-manager --intensity 5 --cold 50 --warm 80 --slow 5 --fast 100 --poll-rate 24
```

| Flag | Meaning |
|------|---------|
| `-i, --intensity` | Temperature power intensity (scales logarithmically, 0-10) |
| `-c, --cold` | Minimum temperature for fan scaling (°C) |
| `-w, --warm` | Maximum temperature for fan scaling (°C) |
| `-s, --slow` | Minimum fan speed (0-100) |
| `-f, --fast` | Maximum fan speed (0-100) |
| `-p, --poll-rate` | Temperature poll rate in seconds |

> Requires `ipmitool` and `lm-sensors` installed on the host, and privileges to
> issue raw IPMI commands to the BMC.

---

## MCP

This server uses dynamic Action-Routed tools to optimize token overhead and
maximize IDE compatibility.

### Available MCP Tools

_Auto-generated from the live MCP server — do not edit by hand._

<!-- MCP-TOOLS-TABLE:START -->

#### Condensed action-routed tools (`MCP_TOOL_MODE=condensed`)

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `fan_ingest_telemetry` | `KGTOOL` | Ingest live thermal telemetry into epistemic-graph as typed nodes. |
| `fan_manager_bmc` | `IPMITOOL` | BMC configuration: LAN, users, and management-controller ops (CONCEPT:FM-OS.config.bmc-config-lan-user). |
| `fan_manager_fan_control` | `FAN_CONTROLTOOL` | Control Dell PowerEdge fan speed via IPMI (CONCEPT:FM-OS.governance.service-writes-fan-level). |
| `fan_manager_power` | `IPMITOOL` | Chassis power + boot control over IPMI (CONCEPT:FM-OS.governance.power-chassis). DESTRUCTIVE for |
| `fan_manager_raw` | `IPMITOOL` | Send a raw IPMI command (CONCEPT:FM-OS.governance.raw). Advanced/vendor commands. |
| `fan_manager_sel` | `IPMITOOL` | System Event Log — the BMC's hardware-event history (CONCEPT:FM-OS.governance.event-log). |
| `fan_manager_sensors` | `IPMITOOL` | Read BMC sensors / SDR (CONCEPT:FM-OS.governance.sensors). |
| `fan_manager_sol` | `IPMITOOL` | Serial-over-LAN console status/teardown (CONCEPT:FM-OS.governance.serial-over-lan). A live |
| `fan_manager_temperature` | `TEMPERATURETOOL` | Read CPU/sensor temperature (CONCEPT:FM-OS.governance.service-reads-temperature-through). |

#### Verbose 1:1 API-mapped tools (`MCP_TOOL_MODE=verbose` or `both`)

<details>
<summary>5 per-operation tools — one per public API method (click to expand)</summary>

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `fan_manager_auto_set_fan_speed` | `APITOOL` | Adjust fan speed automatically from the current temperature (CONCEPT:FM-OS.governance.service-writes-fan-level). |
| `fan_manager_get_core_temp` | `APITOOL` | Return the highest core temperature from a sensors mapping (CONCEPT:FM-OS.governance.service-reads-temperature-through). |
| `fan_manager_get_temp` | `APITOOL` | Return the current highest CPU core temperature (CONCEPT:FM-OS.governance.service-reads-temperature-through). |
| `fan_manager_run_service` | `APITOOL` | Run the continuous fan-management service loop (CONCEPT:FM-OS.governance.service-writes-fan-level). |
| `fan_manager_set_fan` | `APITOOL` | Set the fan to a fixed level (0-100) (CONCEPT:FM-OS.governance.service-writes-fan-level). |

</details>

_9 action-routed tool(s) · 5 verbose 1:1 tool(s). Each is enabled unless its `<DOMAIN>TOOL` toggle is set false; `MCP_TOOL_MODE` selects the surface (**`intent` default** — the six verb-tools, granular set loaded on demand · `condensed` action-routed · `verbose` 1:1 · `both`). Auto-generated — do not edit._
<!-- MCP-TOOLS-TABLE:END -->

### Dynamic Tool Selection & Visibility

This MCP server supports dynamic toolset selection and visibility filtering at
runtime, so you can restrict the exposed tools and avoid blowing up the LLM's
context window. Configure filtering via:

- **CLI Arguments:** `--tools` / `--toolsets` (and `--disabled-tools` / `--disabled-toolsets`).
- **Environment Variables:** `MCP_ENABLED_TOOLS` / `MCP_DISABLED_TOOLS`, `MCP_ENABLED_TAGS` / `MCP_DISABLED_TAGS`.
- **HTTP Headers:** `x-mcp-enabled-tools` / `x-mcp-disabled-tags`, etc.
- **Query Parameters:** `?tools=tool1,tool2` or `?tags=fan-control`.

---

### MCP Configuration Examples

<!-- MCP-CONFIG-EXAMPLES:START -->

> **Install the connector-focused `[mcp]` extra.** Examples use `fan-manager[mcp]` to add
> FastMCP / FastAPI through `agent-utilities[mcp]`; the required Agent Utilities core
> still carries `epistemic-graph[full]`. The `[agent-runtime]` extra additionally
> enables model orchestration.

#### stdio Transport (local IDEs — Cursor, Claude Desktop, VS Code)

```json
{
  "mcpServers": {
    "fan-manager-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "fan-manager[mcp]",
        "fan-manager-mcp"
      ],
      "env": {
        "MCP_TOOL_MODE": "intent",
        "ENABLE_DELEGATION": "False",
        "FAN_CONTROLTOOL": "True",
        "FAN_MANAGER_HOSTS": "r510,r710,r820,rw710",
        "FAN_MANAGER_KG_AGGREGATE_S": "3600",
        "FAN_MANAGER_KG_INGEST": "true",
        "FAN_MANAGER_POLICY_FILE": "/policy/fan-policy.json",
        "FAN_MANAGER_POLICY_REFRESH": "20",
        "IPMITOOL": "True",
        "IPMITOOL_PATH": "ipmitool",
        "KGTOOL": "True",
        "SENSORS_PATH": "sensors",
        "TEMPERATURETOOL": "True"
      }
    }
  }
}
```

Runtime references require an alias-aware launcher such as GraphOS. Other
launchers must omit those entries and inject the resolved values through their
own runtime secret boundary.

#### Streamable-HTTP Transport (networked / production)

```json
{
  "mcpServers": {
    "fan-manager-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "fan-manager[mcp]",
        "fan-manager-mcp",
        "--transport",
        "streamable-http",
        "--port",
        "8000"
      ],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "127.0.0.1",
        "PORT": "8000",
        "MCP_TOOL_MODE": "intent",
        "ENABLE_DELEGATION": "False",
        "FAN_CONTROLTOOL": "True",
        "FAN_MANAGER_HOSTS": "r510,r710,r820,rw710",
        "FAN_MANAGER_KG_AGGREGATE_S": "3600",
        "FAN_MANAGER_KG_INGEST": "true",
        "FAN_MANAGER_POLICY_FILE": "/policy/fan-policy.json",
        "FAN_MANAGER_POLICY_REFRESH": "20",
        "IPMITOOL": "True",
        "IPMITOOL_PATH": "ipmitool",
        "KGTOOL": "True",
        "SENSORS_PATH": "sensors",
        "TEMPERATURETOOL": "True"
      }
    }
  }
}
```

Alternatively, connect to a pre-deployed Streamable-HTTP instance by `url`:

```json
{
  "mcpServers": {
    "fan-manager-mcp": {
      "url": "http://localhost:8000/fan-manager-mcp/mcp"
    }
  }
}
```

Run a reviewed container image as a least-privilege stdio child (no
listener or published port):

```bash
docker run -i --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --pids-limit=256 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  -e TRANSPORT=stdio \
  -e MCP_TOOL_MODE=intent \
  -e ENABLE_DELEGATION=False \
  -e FAN_CONTROLTOOL=True \
  -e FAN_MANAGER_HOSTS=r510,r710,r820,rw710 \
  -e FAN_MANAGER_KG_AGGREGATE_S=3600 \
  -e FAN_MANAGER_KG_INGEST=true \
  -e FAN_MANAGER_POLICY_FILE=/policy/fan-policy.json \
  -e FAN_MANAGER_POLICY_REFRESH=20 \
  -e IPMITOOL=True \
  -e IPMITOOL_PATH=ipmitool \
  -e KGTOOL=True \
  -e SENSORS_PATH=sensors \
  -e TEMPERATURETOOL=True \
  registry.example.invalid/fan-manager@sha256:<digest> fan-manager-mcp
```

For containerized network HTTP, supply an authenticated TLS ingress (or
direct server TLS), exact `MCP_ALLOWED_HOSTS`, and an exact trusted-proxy
CIDR policy through the operator-owned deployment profile. The generator
does not emit an unauthenticated non-loopback listener.

_Auto-generated from the code-read env surface (`MCP_TOOL_MODE` + package vars) — do not edit._
<!-- MCP-CONFIG-EXAMPLES:END -->

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`fan-manager` can run as a local stdio process or container, or behind a remote
network boundary. The
[Deployment guide](https://knuckles-team.github.io/fan-manager/deployment/) carries
the detailed transport contract.

- **Local container** — launch a reviewed immutable image as a least-privilege
  stdio child with no listener or published port.
- **Remote URL** — connect through an operator-supplied authenticated HTTPS
  ingress. Keep its URL, outbound identity references, trust profile, and exact
  `MCP_ALLOWED_HOSTS` in `AgentConfig`.
<!-- END GENERATED: additional-deployment-options -->

## Agent

This repository features a fully integrated Pydantic AI Graph Agent. It
communicates over the **Agent Control Protocol (ACP)** and interacts with the
**Agent Web UI (AG-UI)** and Terminal interface.

### Running the Agent CLI

```bash
fan-manager-agent --provider openai --model-id gpt-4o
```

### Docker Compose Orchestration

The `docker/agent.compose.yml` configures the Agent, Web UI, and Terminal
Interface alongside the MCP server. See
[docs/deployment.md](docs/deployment.md) for the full Compose stack.

---

## Environment Variables

<!-- ENV-VARS-TABLE:START -->

#### Package environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` |  |
| `PORT` | `8000` |  |
| `TRANSPORT` | `stdio` | options: stdio, streamable-http, sse |
| `AUTH_TYPE` | `none` | auth strategy for the agent-utilities MCP factory |
| `FASTMCP_LOG_LEVEL` | `INFO` |  |
| `TEMPERATURETOOL` | `True` | register the temperature tool domain |
| `FAN_CONTROLTOOL` | `True` | register the fan-control tool domain |
| `IPMITOOL` | `True` | register the full IPMI/BMC tool domain |
| `KGTOOL` | `True` | register the native KG ingestion tool (fan_ingest_telemetry) |
| `FAN_MANAGER_KG_INGEST` | `true` | default-on best-effort thermal-sample ingestion in the control loop |
| `FAN_MANAGER_KG_AGGREGATE_S` | `3600` | window (s) over which samples distill to ONE :ThermalTrend node |
| `FAN_MANAGER_HOST` | — | optional host/BMC label stamped on ingested :ManagedHost provenance |
| `FAN_MANAGER_HOSTS` | `r510,r710,r820,rw710` | hosts the derivation pass learns/recommends over |
| `FAN_MANAGER_CURVE` | — | JSON override of the "current" curve, e.g. {"cold":55,"warm":80,"slow":10,"fast":100,"poll":24} |
| `FAN_MANAGER_NOTIFY_URL` | — | best-effort webhook for thermal-anomaly notifications (e.g. the alert-bridge) |
| `FAN_MANAGER_POLICY_FILE` | `/policy/fan-policy.json` | mounted JSON of approved per-host policies the control loop applies |
| `FAN_MANAGER_POLICY_REFRESH` | `20` | re-read the approved policy every N control-loop ticks (0 = never) |
| `IPMITOOL_PATH` | `ipmitool` | Fan Manager drives the host's BMC and lm-sensors locally. |
| `SENSORS_PATH` | `sensors` |  |
| `ENABLE_OTEL` | `True` |  |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:8080/api/public/otel` |  |
| `OTEL_EXPORTER_OTLP_PUBLIC_KEY_REF` | `secret://telemetry/otlp-public-key` |  |
| `OTEL_EXPORTER_OTLP_SECRET_KEY_REF` | `secret://telemetry/otlp-secret-key` |  |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` |  |
| `ENABLE_DELEGATION` | `False` | OIDC Bearer-token delegation (inert by default — Fan Manager is a local tool). |
| `EUNOMIA_TYPE` | `none` | options: none, embedded, remote |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` |  |
| `EUNOMIA_REMOTE_URL` | `http://eunomia-server:8000` |  |

#### Inherited agent-utilities variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `MCP_TOOL_MODE` | `intent` | Tool surface: `intent` \| `condensed` \| `verbose` \| `both` |
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `MCP_CLIENT_AUTH` | — | Outbound MCP child auth: `oidc-client-credentials` \| `basic` \| `none` |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET_REF` | `secret://identity/oidc-client-secret` | Runtime secret reference for the OIDC service account |
| `MCP_BASIC_AUTH_USERNAME` | — | HTTP Basic username (`MCP_CLIENT_AUTH=basic`) |
| `MCP_BASIC_AUTH_PASSWORD_REF` | `secret://identity/mcp-basic-password` | Runtime secret reference for HTTP Basic auth (`MCP_CLIENT_AUTH=basic`) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | `openai` | LLM provider for the agent |
| `MODEL_ID` | `gpt-4o` | Model id for the agent |
| `ENABLE_WEB_UI` | `True` | Serve the AG-UI web interface |

_28 package + 16 inherited variable(s). Auto-generated from `.env.example` + the shared agent-utilities set — do not edit._
<!-- ENV-VARS-TABLE:END -->


Fan Manager reads the following environment variables (all optional — every one
has a safe default). They can be set in the process environment, in a `.env`
file (auto-loaded), or in the MCP client's `env` block. See
[`.env.example`](.env.example) for a ready-to-copy template.

| Variable | Default | Scope | Description |
|----------|---------|-------|-------------|
| `HOST` | `0.0.0.0` | MCP server | Bind address for `streamable-http`/`sse` transports. |
| `PORT` | `8000` | MCP server | Bind port for `streamable-http`/`sse` transports. |
| `TRANSPORT` | `stdio` | MCP server | Transport: `stdio`, `streamable-http`, or `sse`. |
| `AUTH_TYPE` | `none` | MCP server | Auth strategy passed to the `agent-utilities` MCP factory (`none` for this local tool). |
| `FASTMCP_LOG_LEVEL` | `INFO` | MCP server | Log verbosity for the underlying FastMCP server. |
| `TEMPERATURETOOL` | `True` | Tool toggle | Register the `temperature` tool domain (`CONCEPT:FM-OS.governance.service-reads-temperature-through`). |
| `FAN_CONTROLTOOL` | `True` | Tool toggle | Register the `fan-control` tool domain (`CONCEPT:FM-OS.governance.service-writes-fan-level`). |
| `IPMITOOL` | `True` | Tool toggle | Register the full IPMI/BMC tool domain (`CONCEPT:FM-OS.governance.power-chassis..008`). |
| `IPMITOOL_PATH` | `ipmitool` | Local tooling | Path/name of the `ipmitool` binary used to drive the BMC. |
| `SENSORS_PATH` | `sensors` | Local tooling | Path/name of the `lm-sensors` binary used to read temperatures. |
| `ENABLE_OTEL` | `True` | Observability | Enable OpenTelemetry/logfire instrumentation for the agent. |
| `ENABLE_DELEGATION` | `False` | Security | Enable OIDC Bearer-token delegation middleware (inert by default — Fan Manager is a local tool). |
| `EUNOMIA_TYPE` | `none` | Security | Eunomia policy mode: `none`, `embedded`, or `remote`. |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` | Security | Path to the Eunomia policy file when `EUNOMIA_TYPE` is set. |

> **Build-time only (not application config):** `UV_COMPILE_BYTECODE`, `NO_COLOR`,
> and `TERM` are consumed by the build/runtime environment (Docker image build,
> terminal rendering) and are not read by the application code.

---

## Security & Governance

Built directly upon the enterprise-ready
[`agent-utilities`](https://github.com/Knuckles-Team/agent-utilities) core,
standard security parameters are fully supported:

### Access Control & Policy Enforcement
- **Eunomia Policies:** Fine-grained, policy-driven tool authorization (`none`, `embedded`, or `remote`).
- **OIDC Token Delegation:** Optional RFC 8693 token exchange (inert by default — Fan Manager is a local tool).

### Runtime Security Grid
| Feature | Functionality | Enablement |
|---------|---------------|------------|
| **Tool Guard** | Sensitivity inspection with human-in-the-loop validation | Enabled by default |
| **Prompt Injection Defense** | Input scanning, repetition monitoring, and recursive loop blocks | Enabled by default |
| **Context Safety Guard** | Stuck-loop detectors and contextual overflow preemptive alerts | Enabled by default |

---

## Installation

Pick the extra that matches what you want to run:

| Extra | Installs | Use when |
|-------|----------|----------|
| `fan-manager[mcp]` | Connector-focused MCP server (`agent-utilities[mcp]` — FastMCP/FastAPI + `epistemic-graph[full]`) | You only run the **MCP server** (smallest install / image) |
| `fan-manager[agent]` | Agent runtime (`agent-utilities[agent-runtime,logfire]` — model orchestration + `epistemic-graph[full]`) | You run the **integrated agent** |
| `fan-manager[all]` | Everything (`mcp` + `agent` + `logfire`) | Development / both surfaces |

```bash
# Connector-focused MCP server (includes the shared graph engine)
uv pip install "fan-manager[mcp]"

# Agent runtime (adds model orchestration to the shared graph engine)
uv pip install "fan-manager[agent]"

# Everything (development)
uv pip install "fan-manager[all]"      # or: python -m pip install "fan-manager[all]"
```

### Container images (`:mcp` vs `:agent`)

One multi-stage `docker/Dockerfile` builds two right-sized images, selected by `--target`:

| Image tag | Build target | Contents | Entrypoint |
|-----------|--------------|----------|------------|
| `example/fan-manager:mcp` | `--target mcp` | `fan-manager[mcp]` — **connector-focused**, includes `epistemic-graph[full]`; no model-orchestration stack | `fan-manager-mcp` |
| `example/fan-manager@sha256:<digest>` | `--target agent` (default) | `fan-manager[agent]` — **agent runtime**, model orchestration + `epistemic-graph[full]` | `fan-manager-agent` |

```bash
docker build --target mcp   -t example/fan-manager:mcp    docker/   # connector-focused MCP server
docker build --target agent -t example/fan-manager:agent-local docker/   # agent runtime
```

`docker/mcp.compose.yml` runs the connector-focused `:mcp` server; `docker/agent.compose.yml` runs the
agent (`immutable agent digest`) with a co-located `:mcp` sidecar.

### Knowledge-graph database (`epistemic-graph`)

Both `[mcp]` and `[agent]` carry the **epistemic-graph** engine through the required
Agent Utilities core dependency (`epistemic-graph[full]`). The `[mcp]` extra keeps
the server connector-focused; `[agent]` additionally enables model orchestration. Local
deployments can use the bundled engine. For production or shared state, run
**epistemic-graph as a dedicated database service** and configure the runtime to use it.
Deployment recipes (single-node + Raft HA), connection configuration, and architecture
diagrams are documented in the
[epistemic-graph deployment guide](https://knuckles-team.github.io/epistemic-graph/deployment/).

---

## Documentation

The complete documentation is published as the
[official documentation site](https://knuckles-team.github.io/fan-manager/).

| Page | Contents |
|---|---|
| [Installation](https://knuckles-team.github.io/fan-manager/installation/) | pip, source, extras, prebuilt Docker image |
| [Deployment](https://knuckles-team.github.io/fan-manager/deployment/) | run the MCP and agent servers, Compose, env config |
| [Usage](https://knuckles-team.github.io/fan-manager/usage/) | the MCP tools, the `Api` facade, the CLI |
| [Overview](https://knuckles-team.github.io/fan-manager/overview/) | the action-routed tool surface and architecture |
| [Concepts](https://knuckles-team.github.io/fan-manager/concepts/) | concept registry (`CONCEPT:FAN-*`) |

---

## Contribute

Contributions are welcome! Please ensure code quality by executing local checks
before submitting pull requests:
- Format code using `ruff format .`
- Lint code using `ruff check .`
- Validate type-safety with `mypy .`
- Execute test suites using `pytest`


<!-- BEGIN agent-utilities-deployment (generated; do not edit between markers) -->

## Deploy with `agent-utilities-deployment`

Provision this package with the consolidated **`agent-utilities-deployment`**
workflow. It selects an installed-package, editable-source, or immutable-container
path; records only runtime secret and TLS-profile references in `AgentConfig`; and
runs doctor, registration, policy, observability, and rollback gates. Ask your agent
to **"deploy `fan-manager` with agent-utilities-deployment"**.

| Install mode | Command |
|------|---------|
| Installed package | `uv tool install "fan-manager[mcp]"`, then run `fan-manager-mcp` |
| Editable source | `uv pip install -e ".[agent]"`, then run `fan-manager-mcp` |
| Immutable container | deploy `registry.example.invalid/fan-manager@sha256:<digest>` through the operator-selected orchestrator |

The repository embeds no deployment profile, credential value, certificate path, or
environment-specific endpoint. Supply those at runtime through `AgentConfig` and the
configured secret provider.

<!-- END agent-utilities-deployment -->

<!-- GOVERNED-CAPABILITY:START -->
## Governed capability contract

This package ships a compact canonical skill surface with specialist procedures
kept as referenced workflows. The current MCP tools, skill metadata,
`connector_manifest.yml`, ontology, mappings, shapes, fixtures, migrations,
tool-schema fingerprints, and certification metadata form one versioned
capability contract. Validate them together; do not rely on stale tool names or
historical per-task skill wrappers.

Runtime endpoints, credentials, certificate trust, tenant identity, retention,
and observability policy are deployment inputs and are never packaged values.
See [Configuration, trust, and privacy](docs/configuration.md) before enabling a
network transport, connector ingestion, GraphOS delegation, or trace export.
<!-- GOVERNED-CAPABILITY:END -->
