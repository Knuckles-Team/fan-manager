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

*Version: 1.5.0*

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

#### Condensed action-routed tools (default — `MCP_TOOL_MODE=condensed`)

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `fan_manager_fan_control` | `FAN_CONTROLTOOL` | Control Dell PowerEdge fan speed via IPMI (CONCEPT:FAN-002). |
| `fan_manager_temperature` | `TEMPERATURETOOL` | Read CPU/sensor temperature (CONCEPT:FAN-001). |

#### Verbose 1:1 API-mapped tools (`MCP_TOOL_MODE=verbose` or `both`)

<details>
<summary>5 per-operation tools — one per public API method (click to expand)</summary>

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `fan_manager_auto_set_fan_speed` | `APITOOL` | Adjust fan speed automatically from the current temperature (CONCEPT:FAN-002). |
| `fan_manager_get_core_temp` | `APITOOL` | Return the highest core temperature from a sensors mapping (CONCEPT:FAN-001). |
| `fan_manager_get_temp` | `APITOOL` | Return the current highest CPU core temperature (CONCEPT:FAN-001). |
| `fan_manager_run_service` | `APITOOL` | Run the continuous fan-management service loop (CONCEPT:FAN-002). |
| `fan_manager_set_fan` | `APITOOL` | Set the fan to a fixed level (0-100) (CONCEPT:FAN-002). |

</details>

_2 action-routed tool(s) (default) · 5 verbose 1:1 tool(s). Each is enabled unless its `<DOMAIN>TOOL` toggle is set false; `MCP_TOOL_MODE` selects the surface (`condensed` default · `verbose` 1:1 · `both`). Auto-generated — do not edit._
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

> **Install the slim `[mcp]` extra.** All examples below install
> `fan-manager[mcp]` — the MCP-server extra that pulls only the FastMCP /
> FastAPI tooling (`agent-utilities[mcp]`). It deliberately **excludes** the heavy
> agent runtime (the epistemic-graph engine, `pydantic-ai`, `dspy`, `llama-index`,
> `tree-sitter`), so `uvx`/container installs are dramatically smaller and faster.
> Use the full `[agent]` extra only when you need the integrated Pydantic AI agent
> (see [Installation](#installation)).

#### stdio Transport (Recommended for local IDEs e.g., Cursor, Claude Desktop)

```json
{
  "mcpServers": {
    "fan-manager": {
      "command": "uvx",
      "args": ["--from", "fan-manager[mcp]", "fan-manager-mcp"],
      "env": {
        "MCP_TOOL_MODE": "condensed",
        "TEMPERATURETOOL": "True",
        "FAN_CONTROLTOOL": "True"
      }
    }
  }
}
```

#### Streamable-HTTP Transport (Recommended for production deployments)

```json
{
  "mcpServers": {
    "fan-manager": {
      "command": "uvx",
      "args": ["--from", "fan-manager[mcp]", "fan-manager-mcp"],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "0.0.0.0",
        "PORT": "8000"
      }
    }
  }
}
```

Connect to a pre-deployed remote or local Streamable-HTTP instance:

```json
{
  "mcpServers": {
    "fan-manager": {
      "url": "http://localhost:8000/fan-manager/mcp"
    }
  }
}
```

Deploying the Streamable-HTTP server via Docker:

```bash
docker run -d \
  --name fan-manager-mcp \
  --privileged \
  -p 8000:8000 \
  -e TRANSPORT=streamable-http \
  -e PORT=8000 \
  knucklessg1/fan-manager:mcp
```

> The `:mcp` tag is the **slim MCP-server image** (built from
> `docker/Dockerfile --target mcp`, installing `fan-manager[mcp]`). The default
> `:latest` tag is the **full agent image** (`--target agent`, `fan-manager[agent]`)
> which also bundles the Pydantic AI agent and the epistemic-graph engine. See
> [Container images](#container-images-mcp-vs-agent).

> The container needs access to the host's IPMI device (`--privileged` or
> `--device /dev/ipmi0`) to drive the BMC.

---

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`fan-manager` can also run as a **local container** (Docker / Podman / `uv`) or be
consumed from a **remote deployment**. The
[Deployment guide](https://knuckles-team.github.io/fan-manager/deployment/) has full, copy-paste
`mcp_config.json` for all four transports — **stdio**, **streamable-http**,
**local container / uv**, and **remote URL**:

- **Local container / uv** — launch the server from `mcp_config.json` via `uvx`,
  `docker run`, or `podman run`, or point at a local streamable-http container by `url`.
- **Remote URL** — connect to a server deployed behind Caddy at
  `http://fan-manager-mcp.arpa/mcp` using the `"url"` key.
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
| `TEMPERATURETOOL` | `True` | register the temperature tool domain (CONCEPT:FAN-001) |
| `FAN_CONTROLTOOL` | `True` | register the fan-control tool domain (CONCEPT:FAN-002) |
| `IPMITOOL_PATH` | `ipmitool` | Fan Manager drives the host's BMC and lm-sensors locally. |
| `SENSORS_PATH` | `sensors` |  |
| `ENABLE_OTEL` | `True` |  |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:8080/api/public/otel` |  |
| `OTEL_EXPORTER_OTLP_PUBLIC_KEY` | `pk-...` |  |
| `OTEL_EXPORTER_OTLP_SECRET_KEY` | `sk-...` |  |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` |  |
| `ENABLE_DELEGATION` | `False` | OIDC Bearer-token delegation (inert by default — Fan Manager is a local tool). |
| `EUNOMIA_TYPE` | `none` | options: none, embedded, remote |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` |  |
| `EUNOMIA_REMOTE_URL` | `http://eunomia-server:8000` |  |

#### Inherited agent-utilities variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `MCP_TOOL_MODE` | `condensed` | Tool surface: `condensed` | `verbose` | `both` |
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `MCP_CLIENT_AUTH` | — | Outbound MCP auth (`oidc-client-credentials` for fleet calls) |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET` | — | OIDC client secret (service-account auth) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | `openai` | LLM provider for the agent |
| `MODEL_ID` | `gpt-4o` | Model id for the agent |
| `ENABLE_WEB_UI` | `True` | Serve the AG-UI web interface |

_18 package + 14 inherited variable(s). Auto-generated from `.env.example` + the shared agent-utilities set — do not edit._
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
| `TEMPERATURETOOL` | `True` | Tool toggle | Register the `temperature` tool domain (`CONCEPT:FAN-001`). |
| `FAN_CONTROLTOOL` | `True` | Tool toggle | Register the `fan-control` tool domain (`CONCEPT:FAN-002`). |
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
| `fan-manager[mcp]` | Slim MCP server only (`agent-utilities[mcp]` — FastMCP/FastAPI) | You only run the **MCP server** (smallest install / image) |
| `fan-manager[agent]` | Full agent runtime (`agent-utilities[agent,logfire]` — Pydantic AI + the epistemic-graph engine) | You run the **integrated agent** |
| `fan-manager[all]` | Everything (`mcp` + `agent` + `logfire`) | Development / both surfaces |

```bash
# MCP server only (recommended for tool hosting — slim deps)
uv pip install "fan-manager[mcp]"

# Full agent runtime (Pydantic AI + epistemic-graph engine)
uv pip install "fan-manager[agent]"

# Everything (development)
uv pip install "fan-manager[all]"      # or: python -m pip install "fan-manager[all]"
```

### Container images (`:mcp` vs `:agent`)

One multi-stage `docker/Dockerfile` builds two right-sized images, selected by `--target`:

| Image tag | Build target | Contents | Entrypoint |
|-----------|--------------|----------|------------|
| `knucklessg1/fan-manager:mcp` | `--target mcp` | `fan-manager[mcp]` — **slim**, no engine/`pydantic-ai`/`dspy`/`llama-index`/`tree-sitter` | `fan-manager-mcp` |
| `knucklessg1/fan-manager:latest` | `--target agent` (default) | `fan-manager[agent]` — **full** agent runtime + epistemic-graph engine | `fan-manager-agent` |

```bash
docker build --target mcp   -t knucklessg1/fan-manager:mcp    docker/   # slim MCP server
docker build --target agent -t knucklessg1/fan-manager:latest docker/   # full agent
```

`docker/mcp.compose.yml` runs the slim `:mcp` server; `docker/agent.compose.yml` runs the
agent (`:latest`) with a co-located `:mcp` sidecar.

### Knowledge-graph database (`epistemic-graph`)

The **full agent** (`[agent]` / `:latest`) embeds the **epistemic-graph** engine (pulled in
transitively via `agent-utilities[agent]`). For production — or to share one knowledge graph
across multiple agents — run **epistemic-graph as its own database container** and point the
agent at it instead of embedding it. Deployment recipes (single-node + Raft HA), connection
config, and the full database architecture (with diagrams) are documented in the
[epistemic-graph deployment guide](https://knuckles-team.github.io/epistemic-graph/deployment/).
The slim `[mcp]` server does **not** require the database.

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


<!-- BEGIN agent-os-genesis-deploy (generated; do not edit between markers) -->

## Deploy with `agent-os-genesis`

This package can be provisioned for you — skill-guided — by the **`agent-os-genesis`**
universal skill (its *single-package deploy mode*): it picks your install method, seeds
secrets to OpenBao/Vault (or `.env`), trusts your enterprise CA, registers the MCP
server, and verifies it — the same machinery that stands up the whole Agent OS, narrowed
to just this package. Ask your agent to **"deploy `fan-manager` with agent-os-genesis"**.

| Install mode | Command |
|------|---------|
| Bare-metal, prod (PyPI) | `uvx fan-manager-mcp` · or `uv tool install fan-manager` |
| Bare-metal, dev (editable) | `uv pip install -e ".[all]"` · or `pip install -e ".[all]"` |
| Container, prod | deploy `knucklessg1/fan-manager:latest` via docker-compose / swarm / podman / podman-compose / kubernetes |
| Container, dev (editable) | deploy `docker/compose.dev.yml` (source-mounted at `/src`; edits live on restart) |

Secrets are read-existing + seeded via `vault_sync` — you are only prompted for what's missing.

<!-- END agent-os-genesis-deploy -->
