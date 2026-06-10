"""Fan Manager authentication module.

Fan Manager is a **local** tool: it drives the host's BMC through ``ipmitool``
and reads temperatures via ``sensors -j``. There is no remote service URL or
API token to authenticate against, so this module deliberately degrades to a
no-op/local config.

It keeps the same *shape* as the ecosystem golden (a ``get_client`` factory) so
the MCP server and downstream tooling can depend on it uniformly. The returned
"client" is simply the local-command facade (:class:`fan_manager.api_client.Api`).
"""

import os
from typing import Any

from agent_utilities.base_utilities import get_logger

from fan_manager.api_client import Api

logger = get_logger(__name__)


def get_client(config: dict | None = None) -> Api:
    """Return the local fan-manager command facade.

    No credentials are required — fan control happens against the local host's
    BMC/sensors. ``config`` is accepted for interface parity with networked
    connectors but is otherwise unused.
    """
    logger.debug("Using local command facade for Fan Manager (no remote auth).")
    return Api()


def get_config() -> dict[str, Any]:
    """Return the resolved local runtime configuration (env-driven, no secrets)."""
    return {
        "ipmitool": os.getenv("IPMITOOL_PATH", "ipmitool"),
        "sensors": os.getenv("SENSORS_PATH", "sensors"),
    }
