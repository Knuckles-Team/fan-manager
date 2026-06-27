# Usage

## CLI

The classic continuous service polls temperature and adjusts the fans:

```bash
fan-manager --intensity 5 --cold 50 --warm 80 --slow 5 --fast 100 --poll-rate 24
```

| Flag | Meaning |
|------|---------|
| `-i, --intensity` | Temperature power intensity (logarithmic, 0-10) |
| `-c, --cold` | Minimum temperature for fan scaling (°C) |
| `-w, --warm` | Maximum temperature for fan scaling (°C) |
| `-s, --slow` | Minimum fan speed (0-100) |
| `-f, --fast` | Maximum fan speed (0-100) |
| `-p, --poll-rate` | Temperature poll rate (seconds) |

## The `Api` facade

```python
from fan_manager.api_client import Api

api = Api()
api.get_temp()                 # {"response": 64.0, "command": "sensors -j", "status": 200}
api.set_fan(fan_level=40)      # set fans to 40%
api.auto_set_fan_speed(minimum_fan_speed=5, maximum_fan_speed=100)
```

## MCP tools

The MCP server exposes two action-routed tools:

### `fan_manager_temperature` (`CONCEPT:FAN-001`)

```json
{ "action": "get" }
```

```json
{ "action": "get_core", "params_json": "{\"cpus\": [\"coretemp-isa-0000\"], \"sensors\": {}}" }
```

### `fan_manager_fan_control` (`CONCEPT:FAN-002`)

```json
{ "action": "set", "params_json": "{\"fan_level\": 40}" }
```

```json
{ "action": "auto", "params_json": "{\"minimum_fan_speed\": 5, \"maximum_fan_speed\": 100, \"minimum_temperature\": 50, \"maximum_temperature\": 80, \"temperature_power\": 5}" }
```

### Toggling tools

| Env Var | Default | Effect |
|---------|---------|--------|
| `TEMPERATURETOOL` | `True` | Registers the `temperature` tool |
| `FAN_CONTROLTOOL` | `True` | Registers the `fan-control` tool |

## Running the MCP server

```bash
fan-manager-mcp                                              # stdio (default)
fan-manager-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```
