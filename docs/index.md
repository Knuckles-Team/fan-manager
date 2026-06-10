# fan-manager

Dell PowerEdge **Fan Controller + MCP Server + A2A Agent** for the
agent-utilities ecosystem — a local, action-routed connector for temperature
monitoring and IPMI fan control.

!!! info "Official documentation"
    This site is the canonical reference for `fan-manager`, maintained alongside
    every release.

[![PyPI](https://img.shields.io/pypi/v/fan-manager)](https://pypi.org/project/fan-manager/)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
[![License](https://img.shields.io/pypi/l/fan-manager)](https://github.com/Knuckles-Team/fan-manager/blob/main/LICENSE)
[![GitHub](https://img.shields.io/badge/source-GitHub-181717?logo=github)](https://github.com/Knuckles-Team/fan-manager)

## Overview

`fan-manager` controls Dell PowerEdge fan speed based on CPU temperature. It
provides:

- **`Api`** — a local-command facade (`fan_manager.api_client.Api`) wrapping the
  real callables (`get_temp`, `set_fan`, `auto_set_fan_speed`, `run_service`).
- **Action-routed MCP tools** — two consolidated, togglable tool modules
  (`temperature`, `fan-control`) that minimize token overhead in LLM contexts.
- **An A2A agent server** — a Pydantic-AI graph agent (console script
  `fan-manager-agent`) that calls the MCP tool surface and exposes an AG-UI.

Fan Manager is a **local** tool: there are no remote credentials. It requires
`ipmitool` and `lm-sensors` on the host and privileges to issue raw IPMI commands.

## Explore the documentation

<div class="grid cards" markdown>

- :material-rocket-launch: **[Installation](installation.md)** — pip, source, extras, and the prebuilt Docker image.
- :material-server-network: **[Deployment](deployment.md)** — run the MCP and agent servers, Docker Compose, env config.
- :material-console: **[Usage](usage.md)** — the MCP tools, the `Api` facade, and the CLI.
- :material-sitemap: **[Overview](overview.md)** — the action-routed tool surface and architecture.
- :material-tag-multiple: **[Concepts](concepts.md)** — the `CONCEPT:FAN-*` registry.

</div>

## Quick start

```bash
pip install "fan-manager[mcp]"
fan-manager-mcp                   # stdio MCP server (default transport)
```

Run the classic CLI service:

```bash
fan-manager --intensity 5 --cold 50 --warm 80 --slow 5 --fast 100 --poll-rate 24
```
