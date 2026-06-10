"""MCP tools for fan control operations.

CONCEPT:FAN-002 — Fan Control (tag ``fan-control``)

Action-routed dynamic tool registration. A single tool per domain accepts an
``action`` and a ``params_json`` payload and routes to the real callables in
``fan_manager.fan_manager``.
"""

import json
from typing import Any

from fastmcp import Context, FastMCP
from pydantic import Field

from fan_manager.fan_manager import auto_set_fan_speed, set_fan


def register_fan_control_tools(mcp: FastMCP):
    @mcp.tool(tags={"fan-control"})
    async def fan_manager_fan_control(
        action: str = Field(
            description="Action to perform. Must be one of: 'set', 'auto'",
        ),
        params_json: str = Field(
            default="{}",
            description="JSON string of parameters to pass to the action. "
            "For 'set' supply {'fan_level': 0-100}. For 'auto' supply optional "
            "{'minimum_fan_speed', 'maximum_fan_speed', 'minimum_temperature', "
            "'maximum_temperature', 'temperature_power'}.",
        ),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> Any:
        """Control Dell PowerEdge fan speed via IPMI (CONCEPT:FAN-002).

        Action-routed methods:
          - ``set``: set the fan to a fixed level (0-100) using ``ipmitool``.
          - ``auto``: read the current temperature and set the fan speed using a
            logarithmic temperature-to-speed curve.
        """
        if ctx:
            await ctx.info("Adjusting fan speed...")

        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}

        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        if action == "set":
            raw_level = kwargs.get("fan_level")
            if raw_level is None:
                return {"error": "The 'set' action requires a 'fan_level' (0-100)."}
            try:
                fan_level = int(raw_level)
            except (TypeError, ValueError):
                return {
                    "error": f"Invalid 'fan_level': {raw_level!r} is not an integer."
                }
            return set_fan(fan_level=fan_level)
        if action == "auto":
            result = auto_set_fan_speed(
                minimum_fan_speed=kwargs.get("minimum_fan_speed", 5),
                maximum_fan_speed=kwargs.get("maximum_fan_speed", 100),
                minimum_temperature=kwargs.get("minimum_temperature", 50),
                maximum_temperature=kwargs.get("maximum_temperature", 80),
                temperature_power=kwargs.get("temperature_power", 5),
            )
            return {"response": result, "command": "auto_set_fan_speed", "status": 200}
        raise ValueError(f"Unknown action: {action}")
