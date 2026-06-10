# Installation

## Requirements

Fan Manager is a **local** tool that drives the host's BMC and reads sensors.
The host must have:

- Python `>=3.11,<3.15`
- [`ipmitool`](https://github.com/ipmitool/ipmitool) (fan control via raw IPMI)
- [`lm-sensors`](https://github.com/lm-sensors/lm-sensors) (`sensors -j` for temperatures)
- Privileges to issue raw IPMI commands to the BMC (root / `--privileged` container)

```bash
sudo apt-get install -y ipmitool lm-sensors
```

## PyPI

```bash
# Using uv (recommended)
uv pip install "fan-manager[all]"

# Using pip
python -m pip install "fan-manager[all]"
```

### Extras

| Extra | Installs | Use |
|-------|----------|-----|
| `mcp` | `agent-utilities[mcp]` | MCP server (`fan-manager-mcp`) |
| `agent` | `agent-utilities[agent,logfire]` | A2A agent (`fan-manager-agent`) |
| `all` | `fan-manager[mcp,agent]` | Everything |
| `test` | pytest stack | Running the test suite |

## From source

```bash
git clone https://github.com/Knuckles-Team/fan-manager
pip install -e ".[all]"
```

## Docker

```bash
docker pull knucklessg1/fan-manager:latest
```

The container needs access to the host IPMI device — run with `--privileged` or
`--device /dev/ipmi0`.
