"""Optional FastMCP middlewares for Fan Manager.

These mirror the ecosystem delegation/JWT logging middlewares. Fan Manager is a
local tool with no remote auth by default, so these are inert unless OIDC
delegation is explicitly enabled. They are provided for interface parity and are
not registered automatically.
"""

import os
import threading

from agent_utilities.base_utilities import get_logger, to_boolean
from fastmcp.server.middleware import Middleware, MiddlewareContext

logger = get_logger(__name__)
local = threading.local()


def delegation_enabled() -> bool:
    """Return whether OIDC delegation is enabled via env."""
    return to_boolean(os.getenv("ENABLE_DELEGATION", "False"))


class UserTokenMiddleware(Middleware):
    """Extract a Bearer token from inbound requests for OIDC delegation."""

    def __init__(self, enable_delegation: bool | None = None):
        self.enable_delegation = (
            delegation_enabled() if enable_delegation is None else enable_delegation
        )

    async def on_request(self, context: MiddlewareContext, call_next):
        """Extract and stash a Bearer token for OIDC delegation when enabled."""
        logger.debug(f"Delegation enabled: {self.enable_delegation}")
        if self.enable_delegation:
            headers = getattr(context.message, "headers", {}) or {}
            auth = headers.get("Authorization")
            if auth and auth.startswith("Bearer "):
                token = auth.split(" ")[1]
                local.user_token = token
                local.user_claims = None
                if hasattr(context, "auth") and hasattr(context.auth, "claims"):
                    local.user_claims = context.auth.claims
                    logger.info(
                        "Stored JWT claims for delegation",
                        extra={"subject": context.auth.claims.get("sub")},
                    )
                logger.info("Extracted Bearer token for delegation")
            else:
                logger.error("Missing or invalid Authorization header")
                raise ValueError("Missing or invalid Authorization header")
        return await call_next(context)


class JWTClaimsLoggingMiddleware(Middleware):
    """Log JWT claims on responses when present."""

    async def on_response(self, context: MiddlewareContext, call_next):
        """Log JWT claims on the response when present (audit trail)."""
        response = await call_next(context)
        if hasattr(context, "auth") and hasattr(context.auth, "claims"):
            logger.info(
                "JWT Authentication Success",
                extra={
                    "subject": context.auth.claims.get("sub"),
                    "client_id": context.auth.claims.get("client_id"),
                    "scopes": context.auth.claims.get("scope"),
                },
            )
        return response
