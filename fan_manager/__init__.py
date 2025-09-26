#!/usr/bin/env python
# coding: utf-8

from fan_manager.fan_manager_mcp import fan_manager_mcp
from fan_manager.fan_manager import (
    fan_manager,
    setup_logging,
    get_core_temp,
    get_temp,
    set_fan,
    auto_set_fan_speed,
)

"""
fan-manager

Manager your Dell PowerEdge Fan Speed with this handy tool!
Support MCP Server
"""

__all__ = [
    "fan_manager",
    "fan_manager_mcp",
    "setup_logging",
    "get_core_temp",
    "get_temp",
    "set_fan",
    "auto_set_fan_speed",
]
