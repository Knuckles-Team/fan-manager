"""MCP tool registration modules for fan-manager.

Each domain has its own module with a ``register_*_tools`` function that
attaches an action-routed dynamic tool to the FastMCP server.
"""

from fan_manager.mcp.mcp_fan_control import register_fan_control_tools
from fan_manager.mcp.mcp_temperature import register_temperature_tools

__all__ = [
    "register_temperature_tools",
    "register_fan_control_tools",
]
