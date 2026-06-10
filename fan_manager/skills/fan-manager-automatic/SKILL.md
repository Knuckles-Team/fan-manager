---
name: fan-manager-automatic
description: Use when you need automatic, temperature-driven fan speed control on a Dell PowerEdge server — continuously adjusts fans to a logarithmic curve between configured min/max temperature and fan-speed bounds (CONCEPT:FAN-002).
---

## Overview

Automatically adjust Dell PowerEdge fan speed based on the current CPU
temperature (CONCEPT:FAN-001 read → CONCEPT:FAN-002 write). The speed follows a
logarithmic curve between the configured minimum/maximum temperature and
minimum/maximum fan-speed bounds. On a temperature read failure the fans fail
safe to maximum.

## Tools

- `automatic_fan_speed`: Adjusts fan speed based on the current temperature and
  configured thresholds (`minimum_temperature`, `maximum_temperature`,
  `minimum_fan_speed`, `maximum_fan_speed`, `temperature_power`).

## Usage

Use this skill to enable dynamic cooling that responds to system load — for
example, to keep a rack quiet at idle while still ramping fans under sustained
CPU load. Prefer this over manual control when you want hands-off thermal
management.

## Safety

- Requires `ipmitool` and `lm-sensors` on the host and BMC raw-command access.
- Fan levels are always clamped to the 0-100 range.
- A failed temperature read defaults the fans to the configured maximum.
