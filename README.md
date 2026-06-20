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

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `fan_manager_fan_control` | `FAN-CONTROLTOOL` | Control Dell PowerEdge fan speed via IPMI (CONCEPT:FAN-002). |
| `fan_manager_temperature` | `TEMPERATURETOOL` | Read CPU/sensor temperature (CONCEPT:FAN-001). |

_2 action-routed tools (default `MCP_TOOL_MODE=condensed`). Each is enabled unless its toggle is set false; set `MCP_TOOL_MODE=verbose` (or `both`) for the 1:1 per-operation surface. Auto-generated — do not edit._
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

#### stdio Transport (Recommended for local IDEs e.g., Cursor, Claude Desktop)

```json
{
  "mcpServers": {
    "fan-manager": {
      "command": "uvx",
      "args": ["--from", "fan-manager", "fan-manager-mcp"],
      "env": {
        "TEMPERATURETOOL": "True",
        "FANCONTROLTOOL": "True"
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
      "args": ["--from", "fan-manager", "fan-manager-mcp"],
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
  knucklessg1/fan-manager:latest
```

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
| `FANCONTROLTOOL` | `True` | Tool toggle | Register the `fan-control` tool domain (`CONCEPT:FAN-002`). |
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

```bash
# Using uv (highly recommended)
uv pip install fan-manager[all]

# Using standard pip
python -m pip install fan-manager[all]
```

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
