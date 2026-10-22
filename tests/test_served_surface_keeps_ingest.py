"""The served surface keeps the telemetry ingest operations as their own tools.

``fan_ingest_telemetry`` routes an ``action`` (temperature, sensors). The SDK
(>= 0.3.8) splits it into one tool per action; an older SDK drops it from the
served surface. ``run_service`` is intentionally not a tool (the endless daemon
loop runs as the CLI service).
"""

import sys

sys.argv = ["fan-manager"]

from agent_connector_sdk.mcp.tool_surface import registered_tools

from fan_manager.mcp_server import get_mcp_instance


def test_ingest_telemetry_actions_are_served_as_tools():
    mcp = get_mcp_instance()[0]
    names = set(registered_tools(mcp))
    assert {"fan_ingest_telemetry_temperature", "fan_ingest_telemetry_sensors"} <= names


def test_run_service_is_not_a_tool():
    mcp = get_mcp_instance()[0]
    assert not [n for n in registered_tools(mcp) if "run_service" in n]
