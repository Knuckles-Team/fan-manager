# CONN-FAN-MANAGER-CONNECTOR-CONTENT — Design and implementation plan

Governing spec: [spec.md](spec.md).

## Architecture

`pyproject.toml` declares `fan-manager-mcp` as the connector identity. `create_mcp_server` resolves the packaged content of `fan_manager` from it.
