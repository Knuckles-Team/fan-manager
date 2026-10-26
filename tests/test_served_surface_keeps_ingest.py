"""The served surface keeps the telemetry ingest operations as their own tools.

``fan_ingest_telemetry`` routes an ``action`` (temperature, sensors). The SDK
(>= 0.3.8) splits it into one tool per action; an older SDK drops it from the
served surface. ``run_service`` is intentionally not a tool (the endless daemon
loop runs as the CLI service).
"""

import sys

import pytest

sys.argv = ["fan-manager"]

from agent_connector_sdk.mcp.tool_surface import registered_tools

from agent_connector_sdk.connector import build_server


@pytest.mark.spec("CONN-FAN-MANAGER-R001.1")
def test_ingest_telemetry_actions_are_served_as_tools():
    mcp = build_server("fan_manager", command_args=[])[1]
    names = set(registered_tools(mcp))
    assert {"fan_ingest_telemetry_temperature", "fan_ingest_telemetry_sensors"} <= names


@pytest.mark.spec("CONN-FAN-MANAGER-R001.2")
def test_run_service_is_not_a_tool():
    mcp = build_server("fan_manager", command_args=[])[1]
    assert not [n for n in registered_tools(mcp) if "run_service" in n]


@pytest.mark.spec("CONN-FAN-MANAGER-R001.3")
def test_sdk_floor_is_declared_for_the_split_surface():
    import tomllib
    from pathlib import Path

    project = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()
    )["project"]
    assert "scion-sdk[mcp]>=0.5.4,<0.6.0" in project["dependencies"]


@pytest.mark.spec("CONN-FAN-MANAGER-R001.4")
@pytest.mark.spec("CONN-FAN-MANAGER-R001.5")
def test_client_lists_ingest_tools_through_the_real_server():
    import asyncio

    from fastmcp import Client

    mcp = build_server("fan_manager", command_args=[])[1]

    async def listed() -> set[str]:
        async with Client(mcp) as client:
            return {tool.name for tool in await client.list_tools()}

    names = asyncio.run(listed())
    assert {"fan_ingest_telemetry_temperature", "fan_ingest_telemetry_sensors"} <= names
    assert len(names) == 39
