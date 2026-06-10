# Deployment

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
