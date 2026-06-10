"""Tests for the dependency-injected FanControlService and Api facade.

These exercise the DI seam directly: a fake CommandRunner is injected so the
service/facade can be driven with no real hardware present.
"""

import json

import pytest

from fan_manager.api_client import Api
from fan_manager.services import FanControlService


class _FakeRunner:
    """Injectable CommandRunner returning a fixed temperature (no hardware)."""

    def __init__(self, temp: float = 60.0):
        self._temp = temp
        self.set_levels: list[int] = []

    def which(self, name: str) -> str:
        return f"/usr/bin/{name}"

    def run(self, argv: list[str], *, check: bool = True) -> str:
        if str(argv[0]).endswith("sensors"):
            return json.dumps(
                {"coretemp-isa-0000": {"Core 0": {"temp1_input": self._temp}}}
            )
        if len(argv) >= 7 and argv[4] == "0x02":
            self.set_levels.append(int(argv[6], 16))
        return ""


@pytest.mark.concept("FAN-001")
def test_service_reads_temperature_via_injected_runner():
    """CONCEPT:FAN-001 — the service reads temperature through the injected runner."""
    svc = FanControlService(runner=_FakeRunner(57.0), config={})
    result = svc.read_temperature()
    assert result["status"] == 200
    assert result["response"] == 57.0


@pytest.mark.concept("FAN-002")
def test_service_sets_fan_via_injected_runner():
    """CONCEPT:FAN-002 — the service writes a fan level through the injected runner."""
    runner = _FakeRunner()
    svc = FanControlService(runner=runner, config={})
    result = svc.set_fan_level(42)
    assert result["status"] == 200
    assert runner.set_levels[-1] == 42


@pytest.mark.concept("FAN-002")
def test_service_exposes_injected_dependencies():
    """The service surfaces its injected runner/config (DI contract)."""
    runner = _FakeRunner()
    config = {"ipmitool": "ipmitool"}
    svc = FanControlService(runner=runner, config=config)
    assert svc.runner is runner
    assert svc.config == config


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
def test_api_facade_composes_service_with_di():
    """CONCEPT:FAN-001/CONCEPT:FAN-002 — the Api facade routes through the DI service."""
    runner = _FakeRunner(62.0)
    api = Api(runner=runner, config={})
    assert api.get_temp()["response"] == 62.0
    assert api.set_fan(30)["status"] == 200
    assert runner.set_levels[-1] == 30
