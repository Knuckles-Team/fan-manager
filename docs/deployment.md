# Deployment

<!-- BEGIN GENERATED: deployment-options -->
## Deployment Options

`fan-manager` supports local stdio, a loopback-only development listener, a
least-privilege stdio container, and a remote authenticated HTTPS boundary.
Provider endpoint, credential, selector, identity, and trust material are supplied
at runtime through `AgentConfig`; none is stored in this repository.

### Installed stdio process

```json
{
  "mcpServers": {
    "fan-manager": {
      "command": "fan-manager-mcp",
      "args": [],
      "env": {"MCP_TOOL_MODE": "intent"}
    }
  }
}
```

### Loopback development listener

```bash
fan-manager-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

Do not expose this listener beyond loopback. Network deployments require direct TLS
or an explicitly trusted TLS-terminating ingress, configured authentication, exact
`MCP_ALLOWED_HOSTS`, and an exact trusted-proxy CIDR policy.

### Least-privilege local container

```bash
docker run -i --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --pids-limit=256 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  -e TRANSPORT=stdio \
  registry.example.invalid/fan-manager@sha256:<digest> fan-manager-mcp
```

The operator projects the selected AgentConfig profile into the process at runtime;
the image remains immutable and contains no environment connection profile.

### Remote authenticated HTTPS endpoint

```json
{
  "mcpServers": {
    "fan-manager": {"url": "https://service.example.invalid/mcp"}
  }
}
```

Store the real remote URL, outbound identity reference, and TLS-profile reference in
`AgentConfig`, not in MCP client JSON or documentation.
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
  example/fan-manager@sha256:<digest>
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
