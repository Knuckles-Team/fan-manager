"""Local-command facade for Fan Manager.

There is no REST/GraphQL API here — Fan Manager wraps local commands
(``ipmitool`` for fan control, ``sensors -j`` for temperature). This module
re-exports the real callables from :mod:`fan_manager.fan_manager` and exposes a
thin :class:`Api` object so consumers can use a uniform client surface
(``Api().get_temp()``, ``Api().set_fan(...)``) matching the ecosystem golden.

The :class:`Api` composes a dependency-injected
:class:`~fan_manager.services.FanControlService`, so a caller can substitute the
command-runner adapter (and config) without monkeypatching :mod:`subprocess`.
"""

from typing import Any

from fan_manager.fan_manager import (
    CommandRunner,
    auto_set_fan_speed,
    get_core_temp,
    get_temp,
    run_service,
    set_fan,
)
from fan_manager.services import FanControlService

__all__ = [
    "Api",
    "get_temp",
    "get_core_temp",
    "set_fan",
    "auto_set_fan_speed",
    "run_service",
]


class Api:
    """Thin facade over the local fan-control commands.

    Methods mirror the module-level callables so the client can be used the same
    way as a networked API client elsewhere in the ecosystem. A
    :class:`FanControlService` is composed via dependency injection so the
    underlying command-runner adapter can be swapped for tests/alternate
    backends.

    Args:
        runner: Optional injected :class:`CommandRunner` adapter.
        config: Optional runtime configuration mapping.
    """

    def __init__(
        self,
        runner: CommandRunner | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self._service: FanControlService = FanControlService(
            runner=runner, config=config
        )

    def get_temp(self) -> dict[str, Any]:
        """Return the current highest CPU core temperature (CONCEPT:FAN-001)."""
        return self._service.read_temperature()

    def get_core_temp(self, cpus: list, sensors: dict) -> dict[str, Any]:
        """Return the highest core temperature from a sensors mapping (CONCEPT:FAN-001)."""
        return get_core_temp(cpus=cpus, sensors=sensors)

    def set_fan(self, fan_level: int) -> dict[str, Any]:
        """Set the fan to a fixed level (0-100) (CONCEPT:FAN-002)."""
        return self._service.set_fan_level(fan_level)

    def auto_set_fan_speed(
        self,
        minimum_fan_speed: float = 5,
        maximum_fan_speed: float = 100,
        minimum_temperature: float = 50,
        maximum_temperature: float = 80,
        temperature_power: int = 5,
    ) -> Any:
        """Adjust fan speed automatically from the current temperature (CONCEPT:FAN-002)."""
        return self._service.auto_adjust(
            minimum_fan_speed=minimum_fan_speed,
            maximum_fan_speed=maximum_fan_speed,
            minimum_temperature=minimum_temperature,
            maximum_temperature=maximum_temperature,
            temperature_power=temperature_power,
        )

    def run_service(self, **kwargs: Any) -> Any:
        """Run the continuous fan-management service loop (CONCEPT:FAN-002)."""
        return run_service(runner=self._service.runner, **kwargs)
