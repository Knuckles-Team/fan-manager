"""MCP tools for full IPMI/BMC control (CONCEPT:FAN-003..FAN-008).

Action-routed tools over ``fan_manager.ipmi``. Every tool's ``params_json`` may
carry an out-of-band target — ``{"host": "10.0.0.113", "user": "root",
"password": "..."}`` — to drive a remote iDRAC over ``lanplus``; omit it to run
in-band against the local ``/dev/ipmi0``. (Creds live in OpenBao ``apps/idrac``.)
"""

import json
from typing import Any

from fastmcp import Context, FastMCP
from pydantic import Field

from fan_manager import ipmi


def _parse(
    params_json: str,
) -> tuple[dict[str, Any], dict[str, Any] | None, str | None]:
    try:
        kwargs = json.loads(params_json or "{}")
    except Exception as e:  # noqa: BLE001
        return {}, None, f"Invalid params_json: {e}"
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    target = None
    if kwargs.get("host"):
        target = {
            "host": kwargs["host"],
            "user": kwargs.get("user", "root"),
            "password": kwargs.get("password", ""),
        }
    return kwargs, target, None


def register_ipmi_tools(mcp: FastMCP):
    @mcp.tool(tags={"ipmi-power"})
    async def fan_manager_power(
        action: str = Field(
            description="status | on | off | cycle | reset | soft | identify | bootdev"
        ),
        params_json: str = Field(
            default="{}",
            description="Optional target {host,user,password}; "
            "for 'bootdev' add {'bootdev':'pxe|disk|cdrom|bios'}.",
        ),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> Any:
        """Chassis power + boot control over IPMI (CONCEPT:FAN-003). DESTRUCTIVE for
        off/cycle/reset — confirm the target first."""
        kwargs, target, err = _parse(params_json)
        if err:
            return {"error": err}
        if action in {"status", "on", "off", "cycle", "reset", "soft"}:
            return ipmi.power(action, target=target)
        if action in {"identify", "bootdev"}:
            return ipmi.chassis(action, target=target, bootdev=kwargs.get("bootdev"))
        return {"error": f"Unknown action: {action}"}

    @mcp.tool(tags={"ipmi-sensors"})
    async def fan_manager_sensors(
        action: str = Field(default="list", description="list | full | type"),
        params_json: str = Field(
            default="{}",
            description="Optional target; for 'type' add "
            "{'sensor_type':'Temperature|Fan|Drive Slot|...'}.",
        ),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> Any:
        """Read BMC sensors / SDR (CONCEPT:FAN-004)."""
        kwargs, target, err = _parse(params_json)
        if err:
            return {"error": err}
        return ipmi.sensors(
            action, target=target, sensor_type=kwargs.get("sensor_type")
        )

    @mcp.tool(tags={"ipmi-sel"})
    async def fan_manager_sel(
        action: str = Field(default="list", description="list | elist | info | clear"),
        params_json: str = Field(
            default="{}", description="Optional target {host,user,password}."
        ),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> Any:
        """System Event Log — the BMC's hardware-event history (CONCEPT:FAN-005).
        'clear' is destructive."""
        _, target, err = _parse(params_json)
        if err:
            return {"error": err}
        return ipmi.sel(action, target=target)

    @mcp.tool(tags={"ipmi-console"})
    async def fan_manager_sol(
        action: str = Field(default="info", description="info | deactivate"),
        params_json: str = Field(
            default="{}", description="Optional target {host,user,password}."
        ),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> Any:
        """Serial-over-LAN console status/teardown (CONCEPT:FAN-006). A live
        interactive console must use `ipmitool -I lanplus -H <bmc> -U root -P <pw> sol activate`."""
        _, target, err = _parse(params_json)
        if err:
            return {"error": err}
        return ipmi.sol(action, target=target)

    @mcp.tool(tags={"ipmi-bmc"})
    async def fan_manager_bmc(
        action: str = Field(
            description="lan_print | lan_set | user_list | user_set_password | "
            "user_enable | user_disable | mc_info | mc_reset_cold | mc_reset_warm | selftest"
        ),
        params_json: str = Field(
            default="{}",
            description="Optional target; lan_set needs "
            "{'param','value'} (e.g. param=ipaddr value=10.0.0.110); user_* "
            "need {'user_id'} and set_password needs {'password'}.",
        ),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> Any:
        """BMC configuration: LAN, users, and management-controller ops (CONCEPT:FAN-007)."""
        kwargs, target, err = _parse(params_json)
        if err:
            return {"error": err}
        if action == "lan_print":
            return ipmi.lan("print", target=target)
        if action == "lan_set":
            return ipmi.lan(
                "set",
                target=target,
                param=kwargs.get("param"),
                value=kwargs.get("value"),
            )
        if action == "user_list":
            return ipmi.user("list", target=target)
        if action in {"user_set_password", "user_enable", "user_disable"}:
            sub = action.replace("user_", "")
            return ipmi.user(
                sub,
                target=target,
                user_id=kwargs.get("user_id"),
                password=kwargs.get("password"),
            )
        if action in {"mc_info", "mc_reset_cold", "mc_reset_warm", "selftest"}:
            return ipmi.mc(
                action.replace("mc_", "") if action.startswith("mc_") else action,
                target=target,
            )
        return {"error": f"Unknown action: {action}"}

    @mcp.tool(tags={"ipmi-raw"})
    async def fan_manager_raw(
        params_json: str = Field(
            default="{}",
            description="{'data':'0x30 0x30 0x01 0x00'} and "
            "optional target {host,user,password}.",
        ),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> Any:
        """Send a raw IPMI command (CONCEPT:FAN-008). Advanced/vendor commands."""
        kwargs, target, err = _parse(params_json)
        if err:
            return {"error": err}
        if not kwargs.get("data"):
            return {"error": "raw requires 'data' (space-separated hex bytes)"}
        return ipmi.raw(kwargs["data"], target=target)
