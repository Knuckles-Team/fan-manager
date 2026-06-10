---
name: fan-manager-temperature
description: Use when you need to read the current CPU/core temperature of a Dell PowerEdge server via lm-sensors — to check whether the system is running hot or to drive thermal decisions (CONCEPT:FAN-001).
---

## Overview

Read the current CPU temperature of a Dell PowerEdge server via `lm-sensors`
(`sensors -j`) and surface the hottest core (CONCEPT:FAN-001). This is the read
side of the thermal-management loop; pair it with the control or automatic
skills to act on the reading.

## Tools

- `get_temperature`: Returns the current highest CPU core temperature as a
  structured envelope (`response`, `command`, `status`).

## Usage

Use this skill to check if the system is running hot, to monitor thermal status
over time, or as the input to a fan-speed decision. It performs no fan changes —
it is read-only.

## Safety

- Requires `lm-sensors` installed on the host.
- Read-only: this skill never issues BMC/fan commands.
