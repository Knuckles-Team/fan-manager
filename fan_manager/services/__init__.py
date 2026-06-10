"""Service layer for Fan Manager.

A thin application/service layer that composes the injected command-runner
(adapter seam) with the core temperature (CONCEPT:FAN-001) and fan-control
(CONCEPT:FAN-002) callables. Kept deliberately small — Fan Manager is a tiny
local tool, so this is the single highest-value seam rather than a full
hexagonal split.
"""

from fan_manager.services.fan_control_service import FanControlService

__all__ = ["FanControlService"]
