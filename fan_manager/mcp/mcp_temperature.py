"""MCP tools for temperature operations.

CONCEPT:FAN-001 — Temperature (tag ``temperature``)

Action-routed dynamic tool registration. A single tool per domain accepts an
``action`` and a ``params_json`` payload and routes to the real callables in
``fan_manager.fan_manager``.
"""

import json
from typing import Any

from fastmcp import Context, FastMCP
from pydantic import Field

from fan_manager.fan_manager import get_core_temp, get_temp


def register_temperature_tools(mcp: FastMCP):
    @mcp.tool(tags={"temperature"})
    async def fan_manager_temperature(
        action: str = Field(
            default="get",
            description="Action to perform. Must be one of: 'get', 'get_core'",
        ),
        params_json: str = Field(
            default="{}",
            description="JSON string of parameters to pass to the action. "
            "For 'get_core' supply {'cpus': [...], 'sensors': {...}}.",
        ),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> Any:
        """Read CPU/sensor temperature (CONCEPT:FAN-001).

        Action-routed methods:
          - ``get``: read the highest current CPU core temperature via ``sensors -j``.
          - ``get_core``: compute the highest core temperature from a supplied
            ``cpus`` list and ``sensors`` mapping (no shell-out).
        """
        if ctx:
            await ctx.info("Reading temperature...")

        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}

        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        if action == "get":
            return get_temp()
        if action == "get_core":
            return get_core_temp(
                cpus=kwargs.get("cpus", ["coretemp-isa-0000", "coretemp-isa-0001"]),
                sensors=kwargs.get("sensors", {}),
            )
        raise ValueError(f"Unknown action: {action}")
