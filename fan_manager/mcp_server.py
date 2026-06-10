#!/usr/bin/python
"""Fan Manager MCP server entrypoint.

Registers action-routed dynamic tools (one per domain) and starts the FastMCP
server. Each domain is gated behind an environment toggle so the exposed tool
surface can be trimmed to fit an IDE/LLM context window.

Console script: ``fan-manager-mcp`` -> ``fan_manager.mcp_server:mcp_server``
"""

import logging
import os
import sys
import warnings

warnings.filterwarnings("ignore", message=".*urllib3.*or chardet.*")
warnings.filterwarnings("ignore", message=".*urllib3.*or charset_normalizer.*")

from agent_utilities.base_utilities import to_boolean
from agent_utilities.mcp_utilities import create_mcp_server
from dotenv import find_dotenv, load_dotenv

from fan_manager.mcp import (
    register_fan_control_tools,
    register_temperature_tools,
)

__version__ = "1.1.0"
print(f"Fan Manager MCP v{__version__}", file=sys.stderr)

load_dotenv(find_dotenv(), override=False)

logger = logging.getLogger("FanManagerMCP")


def get_mcp_instance():
    """Build the FastMCP server, register enabled tool domains, and return it."""
    args, mcp, middlewares = create_mcp_server(
        name="Fan Manager",
        version=__version__,
        instructions=(
            "Fan Manager MCP Server - Read CPU/sensor temperatures and control "
            "Dell PowerEdge fan speed via IPMI."
        ),
    )

    registered_tags: list[str] = []

    DEFAULT_TEMPERATURETOOL = to_boolean(os.getenv("TEMPERATURETOOL", "True"))
    if DEFAULT_TEMPERATURETOOL:
        register_temperature_tools(mcp)
        registered_tags.append("temperature")

    DEFAULT_FANCONTROLTOOL = to_boolean(os.getenv("FANCONTROLTOOL", "True"))
    if DEFAULT_FANCONTROLTOOL:
        register_fan_control_tools(mcp)
        registered_tags.append("fan-control")

    for mw in middlewares:
        mcp.add_middleware(mw)

    return mcp, args, middlewares, registered_tags


def mcp_server() -> None:
    """Console-script entrypoint: start the MCP server on the chosen transport."""
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
