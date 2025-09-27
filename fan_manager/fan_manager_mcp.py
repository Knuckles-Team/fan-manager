#!/usr/bin/env python
# coding: utf-8

import argparse
import sys
import logging
from typing import Dict, Any
from fastmcp import FastMCP, Context
from pydantic import Field
from fan_manager.fan_manager import (
    get_temp,
    set_fan,
    setup_logging,
    auto_set_fan_speed,
)

# Initialize logging for MCP server
setup_logging(is_mcp_server=True, log_file="fan_manager_mcp.log")

mcp = FastMCP(name="FanManagerServer")


@mcp.tool(
    annotations={
        "title": "Get CPU Temperature",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    tags={"fan_management", "temperature"},
)
async def get_temperature(
    ctx: Context = Field(
        description="MCP context for progress reporting.", default=None
    ),
) -> Dict[str, Any]:
    """
    Get the current CPU temperature.
    Returns a dictionary with the temperature, command, and status.
    """
    logger = logging.getLogger("FanManagerMCP")
    logger.debug("Fetching CPU temperature")

    try:
        if ctx:
            await ctx.report_progress(progress=50, total=100)
            logger.debug("Reported progress: 50/100")
        result = get_temp()
        if ctx:
            await ctx.report_progress(progress=100, total=100)
            logger.debug("Reported progress: 100/100")
        logger.info(f"Temperature result: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to get temperature: {str(e)}")
        return {
            "response": None,
            "command": "sensors -j",
            "status": 500,
            "error": str(e),
        }


@mcp.tool(
    annotations={
        "title": "Set Fan Speed",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    tags={"fan_management", "control"},
)
async def set_fan_speed(
    fan_level: int = Field(description="Fan speed level (0-100)", ge=0, le=100),
    ctx: Context = Field(
        description="MCP context for progress reporting.", default=None
    ),
) -> Dict[str, Any]:
    """
    Set the fan speed to the specified level.
    Returns a dictionary with the response, command, and status.
    """
    logger = logging.getLogger("FanManagerMCP")
    logger.debug(f"Setting fan level to {fan_level}")

    try:
        if ctx:
            await ctx.report_progress(progress=50, total=100)
            logger.debug("Reported progress: 50/100")
        result = set_fan(fan_level)
        if ctx:
            await ctx.report_progress(progress=100, total=100)
            logger.debug("Reported progress: 100/100")
        logger.info(f"Set fan result: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to set fan level: {str(e)}")
        return {
            "response": None,
            "command": f"ipmitool raw 0x30 0x30 0x02 0xff {hex(fan_level)}",
            "status": 500,
            "error": str(e),
        }


@mcp.tool(
    annotations={
        "title": "Automatic Fan Speed Adjustment",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    tags={"fan_management", "control", "automatic"},
)
async def automatic_fan_speed(
    minimum_fan_speed: float = Field(
        description="Minimum fan speed (0-100)", default=5, ge=0, le=100
    ),
    maximum_fan_speed: float = Field(
        description="Maximum fan speed (0-100)", default=100, ge=0, le=100
    ),
    minimum_temperature: float = Field(
        description="Minimum temperature for fan speed adjustment (40-90)",
        default=50,
        ge=40,
        le=90,
    ),
    maximum_temperature: float = Field(
        description="Maximum temperature for fan speed adjustment (40-90)",
        default=80,
        ge=40,
        le=90,
    ),
    temperature_power: int = Field(
        description="Temperature power intensity for scaling (0-10)",
        default=5,
        ge=0,
        le=10,
    ),
    ctx: Context = Field(
        description="MCP context for progress reporting.", default=None
    ),
) -> Dict[str, Any]:
    """
    Automatically adjust fan speed based on current CPU temperature.
    Returns a dictionary with the response, command, and status.
    """
    logger = logging.getLogger("FanManagerMCP")
    logger.debug(
        f"Starting automatic fan speed adjustment with params: "
        f"min_fan={minimum_fan_speed}, max_fan={maximum_fan_speed}, "
        f"min_temp={minimum_temperature}, max_temp={maximum_temperature}, "
        f"power={temperature_power}"
    )

    try:
        if ctx:
            await ctx.report_progress(progress=50, total=100)
            logger.debug("Reported progress: 50/100")
        result = auto_set_fan_speed(
            minimum_fan_speed=minimum_fan_speed,
            maximum_fan_speed=maximum_fan_speed,
            minimum_temperature=minimum_temperature,
            maximum_temperature=maximum_temperature,
            temperature_power=temperature_power,
        )
        if ctx:
            await ctx.report_progress(progress=100, total=100)
            logger.debug("Reported progress: 100/100")
        logger.info(f"Automatic fan speed result: {result}")
        return {"response": result, "command": "auto_set_fan_speed", "status": 200}
    except Exception as e:
        logger.error(f"Failed to adjust fan speed automatically: {str(e)}")
        return {
            "response": None,
            "command": "auto_set_fan_speed",
            "status": 500,
            "error": str(e),
        }


def fan_manager_mcp():
    logger = logging.getLogger("FanManagerMCP")
    logger.debug("Starting fan manager MCP server")

    parser = argparse.ArgumentParser(description="Run fan manager MCP server.")
    parser.add_argument(
        "-t",
        "--transport",
        default="stdio",
        choices=["stdio", "http", "sse"],
        help="Transport method: 'stdio', 'http', or 'sse' (default: stdio)",
    )
    parser.add_argument(
        "-s",
        "--host",
        default="0.0.0.0",
        help="Host address for HTTP transport (default: 0.0.0.0)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8030,
        help="Port number for HTTP transport (default: 8030)",
    )

    args = parser.parse_args()

    if args.port < 0 or args.port > 65535:
        logger.error(f"Port {args.port} is out of valid range (0-65535)")
        sys.exit(1)

    try:
        if args.transport == "stdio":
            mcp.run(transport="stdio")
        elif args.transport == "http":
            mcp.run(transport="http", host=args.host, port=args.port)
        elif args.transport == "sse":
            mcp.run(transport="sse", host=args.host, port=args.port)
        else:
            logger.error("Transport not supported")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    fan_manager_mcp()


def fan_manager_mcp():
    logger = logging.getLogger("FanManagerMCP")
    logger.debug("Starting fan manager MCP server")

    parser = argparse.ArgumentParser(description="Run fan manager MCP server.")
    parser.add_argument(
        "-t",
        "--transport",
        default="stdio",
        choices=["stdio", "http", "sse"],
        help="Transport method: 'stdio', 'http', or 'sse' (default: stdio)",
    )
    parser.add_argument(
        "-s",
        "--host",
        default="0.0.0.0",
        help="Host address for HTTP transport (default: 0.0.0.0)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8030,
        help="Port number for HTTP transport (default: 8030)",
    )

    args = parser.parse_args()

    if args.port < 0 or args.port > 65535:
        logger.error(f"Port {args.port} is out of valid range (0-65535)")
        sys.exit(1)

    try:
        if args.transport == "stdio":
            mcp.run(transport="stdio")
        elif args.transport == "http":
            mcp.run(transport="http", host=args.host, port=args.port)
        elif args.transport == "sse":
            mcp.run(transport="sse", host=args.host, port=args.port)
        else:
            logger.error("Transport not supported")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start MCP server: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    fan_manager_mcp()
