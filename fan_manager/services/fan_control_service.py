"""Fan-control application service (dependency-injected).

This service is the one deliberate dependency-injection seam in Fan Manager. It
composes:

  * a :class:`~fan_manager.fan_manager.CommandRunner` *adapter* (the shell-out to
    ``sensors``/``ipmitool``), and
  * a runtime ``config`` mapping (binary paths, resolved from env),

so the temperature read path (CONCEPT:FAN-001) and the fan-control path
(CONCEPT:FAN-002) can be driven without touching global module state or
monkeypatching :mod:`subprocess`. Tests and alternate backends inject their own
runner/config; production wires the real ``SubprocessCommandRunner`` and
env-derived config.
"""

from __future__ import annotations

from typing import Any

from fan_manager.fan_manager import (
    CommandRunner,
    SubprocessCommandRunner,
    auto_set_fan_speed,
    get_temp,
    set_fan,
)


class FanControlService:
    """Application service composing a command-runner adapter and runtime config.

    Args:
        runner: The injected :class:`CommandRunner` adapter used for all
            hardware shell-outs (CONCEPT:FAN-001 reads, CONCEPT:FAN-002 writes).
        config: Runtime configuration mapping (e.g. resolved binary paths).
    """

    def __init__(
        self,
        runner: CommandRunner | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self._runner: CommandRunner = runner or SubprocessCommandRunner()
        self._config: dict[str, Any] = config or {}

    @property
    def runner(self) -> CommandRunner:
        """The injected command-runner adapter."""
        return self._runner

    @property
    def config(self) -> dict[str, Any]:
        """The injected runtime configuration mapping."""
        return self._config

    def read_temperature(self) -> dict[str, Any]:
        """Read the current highest CPU core temperature (CONCEPT:FAN-001)."""
        return get_temp(runner=self._runner)

    def set_fan_level(self, fan_level: int) -> dict[str, Any]:
        """Set the fan to a fixed level 0-100 (CONCEPT:FAN-002)."""
        return set_fan(fan_level, runner=self._runner)

    def auto_adjust(self, **kwargs: Any) -> Any:
        """Run one temperature-driven fan-curve adjustment (CONCEPT:FAN-002)."""
        return auto_set_fan_speed(runner=self._runner, **kwargs)
