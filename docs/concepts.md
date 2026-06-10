# Concept Registry — fan-manager

> **Prefix**: `CONCEPT:FAN-*`
> **Version**: 1.1.0
> **Bridge**: [`ECO-4.0`](https://github.com/Knuckles-Team/agent-utilities/blob/main/docs/concepts.md) (Unified Toolkit Ingestion)

---

## Project-Specific Concepts

| Concept ID | Name | Tag | Description |
|------------|------|-----|-------------|
| `CONCEPT:FAN-001` | Temperature | `temperature` | MCP tool domain `temperature` — read CPU/sensor temperatures via `lm-sensors`. Action-routed dynamic tool registration. |
| `CONCEPT:FAN-002` | Fan Control | `fan-control` | MCP tool domain `fan-control` — set fixed or temperature-driven fan speed via IPMI (`ipmitool`). Action-routed dynamic tool registration. |

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
| `OS-5.3` | Guardrail Engine | agent-utilities |
| `OS-5.4` | Audit Logging | agent-utilities |
| `KG-2.0` | Knowledge Graph Core | agent-utilities |

## Synergy with agent-utilities

This project integrates with `agent-utilities` via the `ECO-4.0` (Unified
Toolkit Ingestion) bridge. The `fan_manager` MCP server registers its tools with
the agent-utilities FastMCP middleware, enabling automatic discovery, telemetry,
and Knowledge Graph ingestion of all `CONCEPT:FAN-*` concepts.
