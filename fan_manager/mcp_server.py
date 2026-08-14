#!/usr/bin/python
"""Fan Manager MCP server entrypoint.

Registers action-routed dynamic tools (one per domain) and starts the FastMCP
server. Each domain is gated behind an environment toggle so the exposed tool
surface can be trimmed to fit an IDE/LLM context window.

Console script: ``fan-manager-mcp`` -> ``fan_manager.mcp_server:mcp_server``
"""

import logging
import sys
import warnings

warnings.filterwarnings("ignore", message=".*urllib3.*or chardet.*")
warnings.filterwarnings("ignore", message=".*urllib3.*or charset_normalizer.*")

from agent_utilities.core.config import load_config
from agent_utilities.mcp.server_factory import create_mcp_server
from agent_utilities.mcp.verbose_tools import register_tool_surface

from fan_manager.api_client import Api
from fan_manager.auth import get_client
from fan_manager.mcp import (
    register_fan_control_tools,
    register_ipmi_tools,
    register_kg_tools,
    register_temperature_tools,
)

__version__ = "2.1.0"
print(f"Fan Manager MCP v{__version__}", file=sys.stderr)

load_config()

logger = logging.getLogger("FanManagerMCP")

# (tag, env-toggle, registrar) — toggle names match the framework-derived
# ``<TAG>TOOL`` convention (``register_<tag>_tools`` -> ``<TAG>TOOL``).
TOOL_REGISTRY = [
    ("temperature", "TEMPERATURETOOL", register_temperature_tools),
    ("fan-control", "FAN_CONTROLTOOL", register_fan_control_tools),
    ("ipmi", "IPMITOOL", register_ipmi_tools),
    ("kg", "KGTOOL", register_kg_tools),
]


def get_mcp_instance():
    """Build the FastMCP server, register enabled tool domains, and return it.

    Registers the temperature (CONCEPT:FM-OS.governance.service-reads-temperature-through) and fan-control (CONCEPT:FM-OS.governance.service-writes-fan-level)
    tool domains, each gated behind its env toggle.
    """
    args, mcp, middlewares = create_mcp_server(
        name="Fan Manager",
        version=__version__,
        instructions=(
            "Fan Manager MCP Server - Read CPU/sensor temperatures and control "
            "Dell PowerEdge fan speed via IPMI."
        ),
    )

    registered_tags = register_tool_surface(
        mcp,
        client_cls=Api,
        get_client=get_client,
        service="fan-manager",
        tool_registry=TOOL_REGISTRY,
    )

    for mw in middlewares:
        mcp.add_middleware(mw)

    return mcp, args, middlewares, registered_tags


def mcp_server() -> None:
    """Console-script entrypoint: start the MCP server on the chosen transport.

    Serves the CONCEPT:FM-OS.governance.service-reads-temperature-through (temperature) and CONCEPT:FM-OS.governance.service-writes-fan-level (fan-control)
    tool domains over the selected transport.
    """
    mcp, args, middlewares, registered_tags = get_mcp_instance()
    print(f"fan-manager MCP v{__version__}", file=sys.stderr)
    print("\nStarting MCP Server", file=sys.stderr)
    print(f"  Transport: {args.transport.upper()}", file=sys.stderr)
    print(f"  Auth: {getattr(args, 'auth_type', 'none')}", file=sys.stderr)
    print(f"  Dynamic Tags Loaded: {len(set(registered_tags))}", file=sys.stderr)

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        logger.error("Invalid transport: %s", args.transport)
        sys.exit(1)


if __name__ == "__main__":
    mcp_server()
