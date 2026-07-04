# Concept Registry — fan-manager

> **Prefix**: `CONCEPT:FAN-*`
> **Version**: 1.1.0
> **Bridge**: [`ECO-4.0`](https://github.com/Knuckles-Team/agent-utilities/blob/main/docs/concepts.md) (Unified Toolkit Ingestion)

---

## Project-Specific Concepts

| Concept ID | Name | Tag | Description |
|------------|------|-----|-------------|
| `CONCEPT:FM-OS.governance.service-reads-temperature-through` | Temperature | `temperature` | MCP tool domain `temperature` — read CPU/sensor temperatures via `lm-sensors`. Action-routed dynamic tool registration. |
| `CONCEPT:FM-OS.governance.service-writes-fan-level` | Fan Control | `fan-control` | MCP tool domain `fan-control` — set fixed or temperature-driven fan speed via IPMI (`ipmitool`). Action-routed dynamic tool registration. |
| `CONCEPT:FM-OS.governance.power-chassis` | Power & Chassis | `ipmi-power` | Chassis power + boot control (status/on/off/cycle/reset/soft/identify/bootdev) over IPMI, in-band or out-of-band (`lanplus`). |
| `CONCEPT:FM-OS.governance.sensors` | Sensors / SDR | `ipmi-sensors` | Read BMC sensors and the Sensor Data Repository (`sdr list`/`sensor list`/`sdr type <T>`). |
| `CONCEPT:FM-OS.governance.event-log` | System Event Log | `ipmi-sel` | Read/clear the BMC System Event Log (`sel list/elist/info/clear`) — the hardware-event history. |
| `CONCEPT:FM-OS.governance.serial-over-lan` | Serial-over-LAN | `ipmi-console` | SoL console status/teardown (`sol info/deactivate`); live `sol activate` recipe surfaced for interactive use. |
| `CONCEPT:FM-OS.config.bmc-config-lan-user` | BMC Configuration | `ipmi-bmc` | BMC LAN (`lan print/set`), user (`user list/set_password/enable/disable`), and management-controller (`mc info/reset/selftest`) ops. |
| `CONCEPT:FM-OS.governance.raw` | Raw IPMI | `ipmi-raw` | Send raw/vendor IPMI command bytes (`raw 0x.. ..`) for advanced control. |

## Cross-Project References (from agent-utilities)

> These are **external** concepts owned by the [`agent-utilities`](https://github.com/Knuckles-Team/agent-utilities)
> project, not project-specific `CONCEPT:FAN-*` concepts. They are listed here as
> bare IDs (without the `CONCEPT:` marker prefix) so traceability tooling treats
> them as external bridges rather than orphaned local concepts.

| External Concept ID | Name | Origin |
|---------------------|------|--------|
| `ECO-4.0` | Unified Toolkit Ingestion | agent-utilities |
| `ORCH-1.2` | Confidence-Gated Router | agent-utilities |
| `OS-5.1` | Prompt Injection Defense | agent-utilities |
| `OS-5.2` | Cognitive Scheduler | agent-utilities |
| `AU-OS.governance.reactive-multi-axis-budget` | Guardrail Engine | agent-utilities |
| `AU-OS.governance.wasm-micro-agent-sandbox` | Audit Logging | agent-utilities |
| `KG-2.0` | Knowledge Graph Core | agent-utilities |

## Synergy with agent-utilities

This project integrates with `agent-utilities` via the `ECO-4.0` (Unified
Toolkit Ingestion) bridge. The `fan_manager` MCP server registers its tools with
the agent-utilities FastMCP middleware, enabling automatic discovery, telemetry,
and Knowledge Graph ingestion of all `CONCEPT:FAN-*` concepts.
