"""Verify the action-routed MCP tools register and route correctly.

Routing is exercised by invoking each registered tool's underlying function
(``tool.fn``) with ``ctx=None`` — this avoids needing a live MCP session while
still validating the action dispatch. Hardware calls are mocked by conftest.
"""

import json

import pytest
from fastmcp import FastMCP

from fan_manager.mcp import register_fan_control_tools, register_temperature_tools


@pytest.fixture
def mcp():
    return FastMCP(name="test-fan-manager")


async def _tool_names(mcp: FastMCP) -> set[str]:
    tools = await mcp.list_tools()
    return {getattr(t, "name", t) for t in tools}


async def _tool_fn(mcp: FastMCP, name: str):
    tool = await mcp.get_tool(name)
    return tool.fn


@pytest.mark.asyncio
async def test_temperature_tool_registers(mcp):
    register_temperature_tools(mcp)
    assert "fan_manager_temperature" in await _tool_names(mcp)


@pytest.mark.asyncio
async def test_fan_control_tool_registers(mcp):
    register_fan_control_tools(mcp)
    assert "fan_manager_fan_control" in await _tool_names(mcp)


@pytest.mark.asyncio
async def test_temperature_get_routes(mcp):
    """The 'get' action returns a temperature envelope (sensors mocked)."""
    register_temperature_tools(mcp)
    fn = await _tool_fn(mcp, "fan_manager_temperature")
    result = await fn(action="get", params_json="{}", ctx=None)
    assert result["status"] == 200


@pytest.mark.asyncio
async def test_fan_control_set_routes(mcp):
    """The 'set' action returns a 200 envelope (ipmitool mocked)."""
    register_fan_control_tools(mcp)
    fn = await _tool_fn(mcp, "fan_manager_fan_control")
    result = await fn(
        action="set", params_json=json.dumps({"fan_level": 40}), ctx=None
    )
    assert result["status"] == 200


@pytest.mark.asyncio
async def test_unknown_action_raises(mcp):
    register_temperature_tools(mcp)
    fn = await _tool_fn(mcp, "fan_manager_temperature")
    with pytest.raises(ValueError):
        await fn(action="bogus", params_json="{}", ctx=None)
