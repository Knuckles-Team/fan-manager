"""MCP tool registration for fan-manager.

The temperature, fan-control and IPMI operations are served by the SDK as one
typed tool per ``Api`` / ``IpmiApi`` method. Only the telemetry ingest tools,
which are not client-method wrappers, are registered here.
"""

from fan_manager.mcp.mcp_kg import register_kg_tools

__all__ = ["register_kg_tools"]
