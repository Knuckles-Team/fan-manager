# Provider workflow catalog

Load only the workflow relevant to the current request.

- [fan-manager-automatic](../../fan-manager-automatic/WORKFLOW.md): Use when you need automatic, temperature-driven fan speed control on a Dell PowerEdge server — continuously adjusts fans to a logarithmic curve between configured min/max temperature and fan-speed bounds (CONCEPT:FM-OS.governance.service-writes-fan-level).
- [fan-manager-control](../../fan-manager-control/WORKFLOW.md): Use when you need to manually set a fixed Dell PowerEdge fan speed (0-100) via IPMI — for testing cooling performance, capping acoustic noise, or pinning fans to a known level (CONCEPT:FM-OS.governance.service-writes-fan-level).
- [fan-manager-temperature](../../fan-manager-temperature/WORKFLOW.md): Use when you need to read the current CPU/core temperature of a Dell PowerEdge server via lm-sensors — to check whether the system is running hot or to drive thermal decisions (CONCEPT:FM-OS.governance.service-reads-temperature-through).
