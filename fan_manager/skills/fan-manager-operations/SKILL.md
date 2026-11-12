---
name: fan-manager-operations
skill_type: skill
description: >-
  Operate fan-manager through its governed MCP and Arbora capabilities, including fan manager automatic, fan manager control, fan manager temperature. Use when a request requires this provider's read, change, automation, ingestion, troubleshooting, or evidence workflows.
---

# Fan Manager Operations

Use the provider's governed MCP tools through Arbora delegation.

## Workflow

1. Establish the verified GraphSession and tenant before discovery or retrieval.
2. Discover the current condensed tool surface; never assume a stale tool name or schema.
3. Prefer read-only inspection first. For changes, present impact and use the provider's
   dry-run or preview mode when available.
4. Execute mutations as fenced WorkItems so retries remain idempotent and auditable.
5. Ingest source data only through the signed connector preset and ChangeEnvelope path.
6. Verify the durable result and its trace/evidence before reporting completion.

## Safety contract

- Never persist credentials, endpoints, raw personal identifiers, hostnames, or local paths.
- Resolve TLS trust and verification from environment/configuration; never hardcode bypasses.
- Treat unknown ACL, tenant, schema, or tool-contract state as a hard failure.
- Require explicit approval for destructive, externally visible, or irreversible actions.
- Keep runtime traces policy-scoped and privacy-sanitized.

## Specialized workflows

Read [the workflow catalog](references/catalog.md) only when the request needs a
provider-specific procedure, parameter map, script, or reference asset.

## Tools by task

Every served tool is named below under the task it serves. Pass each argument by name.

- **read-thermal-state**: Read CPU and BMC sensor temperatures, fans and voltages before changing anything. `fan_manager_get_temp`, `fan_manager_get_core_temp`, `fan_manager_ipmi_sensors_list`, `fan_manager_ipmi_sensors_full`, `fan_manager_ipmi_sensors_by_type`, `fan_manager_ipmi_sensors_records`
- **set-fan-level**: Pin the fans to a fixed level after reading the temperature. `fan_manager_get_temp`, `fan_manager_set_fan`
- **regulate-fans-automatically**: Set the fan speed from the current temperature on the configured curve. `fan_manager_get_temp`, `fan_manager_auto_set_fan_speed`
- **power-control-host**: Read the power state of a host and change it through the BMC. `fan_manager_ipmi_power_status`, `fan_manager_ipmi_power_on`, `fan_manager_ipmi_power_off`, `fan_manager_ipmi_power_cycle`, `fan_manager_ipmi_power_reset`, `fan_manager_ipmi_power_soft`
- **direct-chassis**: Identify a chassis by its LED and set its next boot device. `fan_manager_ipmi_chassis_identify`, `fan_manager_ipmi_chassis_set_boot_device`
- **review-event-log**: Read the BMC system event log and clear it once reviewed. `fan_manager_ipmi_sel_info`, `fan_manager_ipmi_sel_list`, `fan_manager_ipmi_sel_elist`, `fan_manager_ipmi_sel_clear`
- **configure-bmc-network-and-console**: Read and change the BMC network settings and the serial-over-LAN console. `fan_manager_ipmi_lan_print`, `fan_manager_ipmi_lan_set`, `fan_manager_ipmi_sol_info`, `fan_manager_ipmi_sol_deactivate`
- **manage-bmc-users**: List BMC users, rotate a password and enable or disable an account. `fan_manager_ipmi_user_list`, `fan_manager_ipmi_user_set_password`, `fan_manager_ipmi_user_enable`, `fan_manager_ipmi_user_disable`
- **maintain-bmc-controller**: Read the management controller, self-test it and reset it when needed. `fan_manager_ipmi_mc_info`, `fan_manager_ipmi_mc_selftest`, `fan_manager_ipmi_mc_reset_warm`, `fan_manager_ipmi_mc_reset_cold`, `fan_manager_ipmi_send_raw`
- **ingest-thermal-telemetry**: Push the current temperature and the sensor table into the knowledge graph. `fan_ingest_telemetry_temperature`, `fan_ingest_telemetry_sensors`
