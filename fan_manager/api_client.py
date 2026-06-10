"""Local-command facade for Fan Manager.

There is no REST/GraphQL API here — Fan Manager wraps local commands
(``ipmitool`` for fan control, ``sensors -j`` for temperature). This module
re-exports the real callables from :mod:`fan_manager.fan_manager` and exposes a
thin :class:`Api` object so consumers can use a uniform client surface
(``Api().get_temp()``, ``Api().set_fan(...)``) matching the ecosystem golden.
"""

from typing import Any

from fan_manager.fan_manager import (
    auto_set_fan_speed,
    get_core_temp,
    get_temp,
    run_service,
    set_fan,
)

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
    way as a networked API client elsewhere in the ecosystem.
    """

    __slots__ = ()

    @staticmethod
    def get_temp() -> dict[str, Any]:
        """Return the current highest CPU core temperature."""
        return get_temp()

    @staticmethod
    def get_core_temp(cpus: list, sensors: dict) -> dict[str, Any]:
        """Return the highest core temperature from a sensors mapping."""
        return get_core_temp(cpus=cpus, sensors=sensors)

    @staticmethod
    def set_fan(fan_level: int) -> dict[str, Any]:
        """Set the fan to a fixed level (0-100)."""
        return set_fan(fan_level=fan_level)

    @staticmethod
    def auto_set_fan_speed(
        minimum_fan_speed: float = 5,
        maximum_fan_speed: float = 100,
        minimum_temperature: float = 50,
        maximum_temperature: float = 80,
        temperature_power: int = 5,
    ) -> Any:
        """Adjust fan speed automatically from the current temperature."""
        return auto_set_fan_speed(
            minimum_fan_speed=minimum_fan_speed,
            maximum_fan_speed=maximum_fan_speed,
            minimum_temperature=minimum_temperature,
            maximum_temperature=maximum_temperature,
            temperature_power=temperature_power,
        )

    @staticmethod
    def run_service(**kwargs: Any) -> Any:
        """Run the continuous fan-management service loop."""
        return run_service(**kwargs)
