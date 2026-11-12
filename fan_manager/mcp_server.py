#!/usr/bin/python
"""Fan Manager MCP server entrypoint.

Registers the telemetry ingest tools; the SDK serves one typed tool per Api and
IpmiApi method and starts the FastMCP server.

Console script: ``fan-manager-mcp`` -> ``fan_manager.mcp_server:mcp_server``
"""

import logging
import warnings

warnings.filterwarnings("ignore", message=".*urllib3.*or chardet.*")
warnings.filterwarnings("ignore", message=".*urllib3.*or charset_normalizer.*")

from scion_sdk.config import load_config

from fan_manager.mcp import register_kg_tools

load_config()

logger = logging.getLogger("FanManagerMCP")


# (tag, env-toggle, registrar) — toggle names match the framework-derived
# ``<TAG>TOOL`` convention (``register_<tag>_tools`` -> ``<TAG>TOOL``).
TOOL_REGISTRY = [
    ("kg", "KGTOOL", register_kg_tools),
]
