#!/usr/bin/python
"""Fan Manager MCP server entrypoint.

Registers action-routed dynamic tools (one per domain) and starts the FastMCP
server. Each domain is gated behind an environment toggle so the exposed tool
surface can be trimmed to fit an IDE/LLM context window.

Console script: ``fan-manager-mcp`` -> ``fan_manager.mcp_server:mcp_server``
"""

import logging
import warnings

warnings.filterwarnings("ignore", message=".*urllib3.*or chardet.*")
warnings.filterwarnings("ignore", message=".*urllib3.*or charset_normalizer.*")

from scion_sdk.config import load_config

from fan_manager.api_client import Api
from fan_manager.mcp import (
    register_fan_control_tools,
    register_kg_tools,
    register_temperature_tools,
)

load_config()

logger = logging.getLogger("FanManagerMCP")


# (tag, env-toggle, registrar) — toggle names match the framework-derived
# ``<TAG>TOOL`` convention (``register_<tag>_tools`` -> ``<TAG>TOOL``).
class _OperationApi(Api):
    """``Api`` without ``run_service``: the endless daemon loop is not a tool."""

    run_service = None  # type: ignore[assignment]


TOOL_REGISTRY = [
    ("temperature", "TEMPERATURETOOL", register_temperature_tools),
    ("fan-control", "FAN_CONTROLTOOL", register_fan_control_tools),
    ("kg", "KGTOOL", register_kg_tools),
]
