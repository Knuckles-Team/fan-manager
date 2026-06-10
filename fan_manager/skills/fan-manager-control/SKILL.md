---
name: fan-manager-control
description: Use when you need to manually set a fixed Dell PowerEdge fan speed (0-100) via IPMI — for testing cooling performance, capping acoustic noise, or pinning fans to a known level (CONCEPT:FAN-002).
---

## Overview

Set the Dell PowerEdge fan speed manually to a fixed level (CONCEPT:FAN-002).
This enables manual BMC fan control via `ipmitool` raw commands and applies the
requested level directly, bypassing the automatic temperature curve.

## Tools

- `set_fan_speed`: Set the fan speed to a specific level (0-100). Levels outside
  that range are rejected with a structured error envelope.

## Usage

Use this skill when you need to explicitly set the fan speed — for example, to
test cooling performance at a known fan level, strictly control noise, or
temporarily override automatic control. For load-responsive cooling, use the
`fan-manager-automatic` skill instead.

## Safety

- Requires `ipmitool` on the host and BMC raw-command access.
- Fan levels are validated to the 0-100 range before any command is issued.
- Manual control persists until automatic control or a reboot resets it.
