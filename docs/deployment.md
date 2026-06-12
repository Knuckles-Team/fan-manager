# Deployment

<!-- BEGIN GENERATED: deployment-options -->
## Deployment Options

`fan-manager` exposes its MCP server (console script `fan-manager-mcp`) four ways. Pick the row that
matches where the server runs relative to your MCP client, then copy the matching
`mcp_config.json` below. Add the service-connection environment variables documented in the **Configuration** section.

| # | Option | Transport | Where it runs | `mcp_config.json` key |
|---|--------|-----------|---------------|------------------------|
| 1 | stdio | `stdio` | client launches a subprocess | `command` |
| 2 | Streamable-HTTP (local) | `streamable-http` | a local network port | `command` or `url` |
| 3 | Local container / uv | `stdio` or `streamable-http` | Docker / Podman / uv on this host | `command` or `url` |
| 4 | Remote URL | `streamable-http` | a remote host behind Caddy | `url` |

### 1. stdio (local subprocess)

The client launches the server over stdio via `uvx` — best for local IDEs
(Cursor, Claude Desktop, VS Code):

```json
{
  "mcpServers": {
    "fan-manager-mcp": {
      "command": "uvx",
      "args": ["--from", "fan-manager", "fan-manager-mcp"]
    }
  }
}
```

### 2. Streamable-HTTP (local process)

Run the server as a long-lived HTTP process:

```bash
uvx --from fan-manager fan-manager-mcp --transport streamable-http --host 0.0.0.0 --port 8000
curl -s http://localhost:8000/health        # {"status":"OK"}
```

Then either let the client launch it:

```json
{
  "mcpServers": {
    "fan-manager-mcp": {
      "command": "uvx",
      "args": ["--from", "fan-manager", "fan-manager-mcp", "--transport", "streamable-http", "--port", "8000"],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "0.0.0.0",
        "PORT": "8000"
      }
    }
  }
}
```

…or connect to the already-running process by URL:

```json
{
  "mcpServers": {
    "fan-manager-mcp": { "url": "http://localhost:8000/mcp" }
  }
}
```

### 3. Local container / uv

**(a) Launch a container directly from `mcp_config.json`** (stdio over the container —
no ports to manage). Swap `docker` for `podman` for a daemonless runtime:

```json
{
  "mcpServers": {
    "fan-manager-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "TRANSPORT=stdio",
        "knucklessg1/fan-manager:latest"
      ]
    }
  }
}
```

**(b) Run a local streamable-http container, then connect by URL:**

```bash
docker run -d --name fan-manager-mcp -p 8000:8000 \
  -e TRANSPORT=streamable-http \
  -e PORT=8000 \
  knucklessg1/fan-manager:latest
# or, from a clone of this repo:
docker compose -f docker/mcp.compose.yml up -d
```

```json
{
  "mcpServers": {
    "fan-manager-mcp": { "url": "http://localhost:8000/mcp" }
  }
}
```

**(c) From a local checkout with `uv`:**

```bash
uv run fan-manager-mcp --transport streamable-http --port 8000
```

### 4. Remote URL (deployed behind Caddy)

When the server is deployed remotely (e.g. as a Docker service) and published through
Caddy on the internal `*.arpa` zone, connect with the `"url"` key — no local process or
image required:

```json
{
  "mcpServers": {
    "fan-manager-mcp": { "url": "http://fan-manager-mcp.arpa/mcp" }
  }
}
```

Caddy reverse-proxies `http://fan-manager-mcp.arpa` to the container's `:8000`
streamable-http listener; `http://fan-manager-mcp.arpa/health` returns
`{"status":"OK"}` when the service is live.
<!-- END GENERATED: deployment-options -->

## MCP server

```bash
fan-manager-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

## Agent server

```bash
fan-manager-agent --provider openai --model-id gpt-4o
```

## Docker

The container must reach the host IPMI device:

```bash
docker run -d \
  --name fan-manager-mcp \
  --device /dev/ipmi0 \
  -p 8000:8000 \
  -e TRANSPORT=streamable-http \
  -e PORT=8000 \
  knucklessg1/fan-manager:latest
```

## Docker Compose

`docker/mcp.compose.yml` runs the MCP server; `docker/agent.compose.yml` runs the
MCP server plus the agent (Web UI on port 9017). Copy `.env.example` to `.env`
first.

```bash
cp .env.example .env
docker compose -f docker/agent.compose.yml up -d
```

> Add `privileged: true` (or a `devices:` entry for `/dev/ipmi0`) to the
> `fan-manager-mcp` service so it can drive the BMC from inside the container.

## Environment configuration

See [`.env.example`](https://github.com/Knuckles-Team/fan-manager/blob/main/.env.example)
for the full set of MCP, telemetry, Eunomia, and tool-toggle variables.
