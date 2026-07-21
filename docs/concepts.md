# Concept Registry — fan-manager

> **Prefix**: `CONCEPT:FM-OS.*` (OKF-CIS: `<SLUG>-<PILLAR>.<domain>.<concept>`)
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
| `CONCEPT:FM-OS.control.baseline-learning` | Baseline Learning | `kg-control` | Distill a host's `:ThermalTrend` history into a `:ThermalBaseline` (temp p50/p95, idle/load envelope, thermal inertia). Pure percentile + least-squares stats, no ML. |
| `CONCEPT:FM-OS.control.policy-derivation` | Policy Derivation | `kg-control` | Recommend a per-host `:FanControlPolicy` from a baseline — quieter where there's headroom, earlier ramp where there isn't — bounded by the safety ceiling; report-only unless envelope-approved. |
| `CONCEPT:FM-OS.control.anomaly-detection` | Anomaly Detection | `kg-control` | Flag a host drifting off its baseline (above-baseline / cooling-saturated) via z-score → `:ThermalAnomaly` into the alert/remediation loop. |
| `CONCEPT:FM-OS.control.ambient-correlation` | Ambient Correlation | `kg-control` | Collapse simultaneous multi-host spikes into one `ambient` cause (rack/room cooling) instead of N independent alerts. |
| `CONCEPT:FM-OS.control.policy-source-seam` | Policy Source Seam | `kg-control` | The control loop's ONLY write path to fan behaviour: `load_fan_policy` overlays an approved, clamped `:FanControlPolicy` (mounted JSON/ConfigMap) on the CLI curve, hot-reloaded each refresh. |

## Cross-Project References (from agent-utilities)

> These are **external** concepts owned by the [`agent-utilities`](https://github.com/Knuckles-Team/agent-utilities)
> project, not project-specific `CONCEPT:FM-OS.*` concepts. They are listed here as
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
| `AU-KG.ingest.enterprise-source-extractor` | Enterprise Source Extractor (native KG ingestion) | agent-utilities |
| `KG-2.0` | Knowledge Graph Core | agent-utilities |

## Synergy with agent-utilities

This project integrates with `agent-utilities` via the `ECO-4.0` (Unified
Toolkit Ingestion) bridge. The `fan_manager` MCP server registers its tools with
the agent-utilities FastMCP middleware, enabling automatic discovery, telemetry,
and Knowledge Graph ingestion of all `CONCEPT:FM-OS.*` concepts.
