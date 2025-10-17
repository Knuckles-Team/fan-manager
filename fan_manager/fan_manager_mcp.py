#!/usr/bin/env python
# coding: utf-8

import argparse
import sys
import logging
from typing import Dict, Any
from pydantic import Field
from fastmcp import FastMCP, Context
from fastmcp.server.auth.oidc_proxy import OIDCProxy
from fastmcp.server.auth import OAuthProxy, RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier, StaticTokenVerifier
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.middleware.timing import TimingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
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
    parser = argparse.ArgumentParser(description="Run fan manager MCP server.")
    parser.add_argument(
        "-t",
        "--transport",
        default="stdio",
        choices=["stdio", "http", "sse"],
        help="Transport method: 'stdio', 'http', or 'sse' [legacy] (default: stdio)",
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
        default=8000,
        help="Port number for HTTP transport (default: 8000)",
    )
    parser.add_argument(
        "--auth-type",
        default="none",
        choices=["none", "static", "jwt", "oauth-proxy", "oidc-proxy", "remote-oauth"],
        help="Authentication type for MCP server: 'none' (disabled), 'static' (internal), 'jwt' (external token verification), 'oauth-proxy', 'oidc-proxy', 'remote-oauth' (external) (default: none)",
    )
    # JWT/Token params
    parser.add_argument(
        "--token-jwks-uri", default=None, help="JWKS URI for JWT verification"
    )
    parser.add_argument(
        "--token-issuer", default=None, help="Issuer for JWT verification"
    )
    parser.add_argument(
        "--token-audience", default=None, help="Audience for JWT verification"
    )
    # OAuth Proxy params
    parser.add_argument(
        "--oauth-upstream-auth-endpoint",
        default=None,
        help="Upstream authorization endpoint for OAuth Proxy",
    )
    parser.add_argument(
        "--oauth-upstream-token-endpoint",
        default=None,
        help="Upstream token endpoint for OAuth Proxy",
    )
    parser.add_argument(
        "--oauth-upstream-client-id",
        default=None,
        help="Upstream client ID for OAuth Proxy",
    )
    parser.add_argument(
        "--oauth-upstream-client-secret",
        default=None,
        help="Upstream client secret for OAuth Proxy",
    )
    parser.add_argument(
        "--oauth-base-url", default=None, help="Base URL for OAuth Proxy"
    )
    # OIDC Proxy params
    parser.add_argument(
        "--oidc-config-url", default=None, help="OIDC configuration URL"
    )
    parser.add_argument("--oidc-client-id", default=None, help="OIDC client ID")
    parser.add_argument("--oidc-client-secret", default=None, help="OIDC client secret")
    parser.add_argument("--oidc-base-url", default=None, help="Base URL for OIDC Proxy")
    # Remote OAuth params
    parser.add_argument(
        "--remote-auth-servers",
        default=None,
        help="Comma-separated list of authorization servers for Remote OAuth",
    )
    parser.add_argument(
        "--remote-base-url", default=None, help="Base URL for Remote OAuth"
    )
    # Common
    parser.add_argument(
        "--allowed-client-redirect-uris",
        default=None,
        help="Comma-separated list of allowed client redirect URIs",
    )
    # Eunomia params
    parser.add_argument(
        "--eunomia-type",
        default="none",
        choices=["none", "embedded", "remote"],
        help="Eunomia authorization type: 'none' (disabled), 'embedded' (built-in), 'remote' (external) (default: none)",
    )
    parser.add_argument(
        "--eunomia-policy-file",
        default="mcp_policies.json",
        help="Policy file for embedded Eunomia (default: mcp_policies.json)",
    )
    parser.add_argument(
        "--eunomia-remote-url", default=None, help="URL for remote Eunomia server"
    )

    args = parser.parse_args()

    if args.port < 0 or args.port > 65535:
        print(f"Error: Port {args.port} is out of valid range (0-65535).")
        sys.exit(1)

    # Set auth based on type
    auth = None
    allowed_uris = (
        args.allowed_client_redirect_uris.split(",")
        if args.allowed_client_redirect_uris
        else None
    )

    if args.auth_type == "none":
        auth = None
    elif args.auth_type == "static":
        # Internal static tokens (hardcoded example)
        auth = StaticTokenVerifier(
            tokens={
                "test-token": {"client_id": "test-user", "scopes": ["read", "write"]},
                "admin-token": {"client_id": "admin", "scopes": ["admin"]},
            }
        )
    elif args.auth_type == "jwt":
        if not (args.token_jwks_uri and args.token_issuer and args.token_audience):
            print(
                "Error: jwt requires --token-jwks-uri, --token-issuer, --token-audience"
            )
            sys.exit(1)
        auth = JWTVerifier(
            jwks_uri=args.token_jwks_uri,
            issuer=args.token_issuer,
            audience=args.token_audience,
        )
    elif args.auth_type == "oauth-proxy":
        if not (
            args.oauth_upstream_auth_endpoint
            and args.oauth_upstream_token_endpoint
            and args.oauth_upstream_client_id
            and args.oauth_upstream_client_secret
            and args.oauth_base_url
            and args.token_jwks_uri
            and args.token_issuer
            and args.token_audience
        ):
            print(
                "Error: oauth-proxy requires --oauth-upstream-auth-endpoint, --oauth-upstream-token-endpoint, --oauth-upstream-client-id, --oauth-upstream-client-secret, --oauth-base-url, --token-jwks-uri, --token-issuer, --token-audience"
            )
            sys.exit(1)
        token_verifier = JWTVerifier(
            jwks_uri=args.token_jwks_uri,
            issuer=args.token_issuer,
            audience=args.token_audience,
        )
        auth = OAuthProxy(
            upstream_authorization_endpoint=args.oauth_upstream_auth_endpoint,
            upstream_token_endpoint=args.oauth_upstream_token_endpoint,
            upstream_client_id=args.oauth_upstream_client_id,
            upstream_client_secret=args.oauth_upstream_client_secret,
            token_verifier=token_verifier,
            base_url=args.oauth_base_url,
            allowed_client_redirect_uris=allowed_uris,
        )
    elif args.auth_type == "oidc-proxy":
        if not (
            args.oidc_config_url
            and args.oidc_client_id
            and args.oidc_client_secret
            and args.oidc_base_url
        ):
            print(
                "Error: oidc-proxy requires --oidc-config-url, --oidc-client-id, --oidc-client-secret, --oidc-base-url"
            )
            sys.exit(1)
        auth = OIDCProxy(
            config_url=args.oidc_config_url,
            client_id=args.oidc_client_id,
            client_secret=args.oidc_client_secret,
            base_url=args.oidc_base_url,
            allowed_client_redirect_uris=allowed_uris,
        )
    elif args.auth_type == "remote-oauth":
        if not (
            args.remote_auth_servers
            and args.remote_base_url
            and args.token_jwks_uri
            and args.token_issuer
            and args.token_audience
        ):
            print(
                "Error: remote-oauth requires --remote-auth-servers, --remote-base-url, --token-jwks-uri, --token-issuer, --token-audience"
            )
            sys.exit(1)
        auth_servers = [url.strip() for url in args.remote_auth_servers.split(",")]
        token_verifier = JWTVerifier(
            jwks_uri=args.token_jwks_uri,
            issuer=args.token_issuer,
            audience=args.token_audience,
        )
        auth = RemoteAuthProvider(
            token_verifier=token_verifier,
            authorization_servers=auth_servers,
            base_url=args.remote_base_url,
        )
    mcp.auth = auth
    if args.eunomia_type != "none":
        from eunomia_mcp import create_eunomia_middleware

        if args.eunomia_type == "embedded":
            if not args.eunomia_policy_file:
                print("Error: embedded Eunomia requires --eunomia-policy-file")
                sys.exit(1)
            middleware = create_eunomia_middleware(policy_file=args.eunomia_policy_file)
            mcp.add_middleware(middleware)
        elif args.eunomia_type == "remote":
            if not args.eunomia_remote_url:
                print("Error: remote Eunomia requires --eunomia-remote-url")
                sys.exit(1)
            middleware = create_eunomia_middleware(
                use_remote_eunomia=args.eunomia_remote_url
            )
            mcp.add_middleware(middleware)

    mcp.add_middleware(
        ErrorHandlingMiddleware(include_traceback=True, transform_errors=True)
    )
    mcp.add_middleware(
        RateLimitingMiddleware(max_requests_per_second=10.0, burst_capacity=20)
    )
    mcp.add_middleware(TimingMiddleware())
    mcp.add_middleware(LoggingMiddleware())

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        logger = logging.getLogger("FanManagerMCP")
        logger.error("Transport not supported")
        sys.exit(1)


if __name__ == "__main__":
    fan_manager_mcp()
