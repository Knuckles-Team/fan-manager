"""Verify the typed MCP tools register and that the local-command facade works.

The temperature and fan-control operations are served as one typed tool per
``Api`` method (``fan_manager_get_temp``, ``fan_manager_set_fan``, ...); only the
telemetry ingest tools are written by hand. Hardware calls are mocked by conftest.

These tests span registration (contract), happy-path calls, negative paths and
boundary conditions, so the suite is not single-intent.
"""

import importlib
import inspect
import json

import pytest
from fastmcp import FastMCP

from fan_manager.api_client import Api
from fan_manager.mcp import register_kg_tools

# The package __init__ exposes a ``fan_manager`` *function* into its namespace,
# which shadows the ``fan_manager.fan_manager`` submodule under a plain
# ``import ... as``. Load the module explicitly so we reach the core callables.
core = importlib.import_module("fan_manager.fan_manager")


@pytest.fixture
def mcp() -> FastMCP:
    """A fresh, isolated FastMCP instance per test (F.I.R.S.T. - Isolated)."""
    return FastMCP(name="test-fan-manager")


async def _tool_names(mcp: FastMCP) -> set[str]:
    tools = await mcp.list_tools()
    return {t.name for t in tools}


# --------------------------------------------------------------------------- #
# Contract / registration tests
# --------------------------------------------------------------------------- #
async def test_ingest_tools_are_typed_and_unrouted(mcp: FastMCP):
    """The hand-written ingest tools are two typed tools; none takes an action."""
    register_kg_tools(mcp)
    assert await _tool_names(mcp) == {
        "fan_ingest_telemetry_temperature",
        "fan_ingest_telemetry_sensors",
    }
    for tool in await mcp.list_tools():
        assert "action" not in tool.parameters.get("properties", {})


@pytest.mark.concept("FM-OS.governance.service-reads-temperature-through")
@pytest.mark.concept("FM-OS.governance.service-writes-fan-level")
def test_api_operations_are_the_served_temperature_and_fan_tools():
    """The operations the SDK serves as tools are the public ``Api`` methods."""
    methods = {
        name
        for name, member in inspect.getmembers(Api, inspect.isfunction)
        if not name.startswith("_")
    }
    assert {"get_temp", "get_core_temp", "set_fan", "auto_set_fan_speed"} <= methods


# --------------------------------------------------------------------------- #
# Happy-path and negative-path tests
# --------------------------------------------------------------------------- #
@pytest.mark.concept("FM-OS.governance.service-reads-temperature-through")
def test_get_temp_returns_hottest_core():
    """CONCEPT:FM-OS.governance.service-reads-temperature-through - get_temp returns a 200 envelope (mocked)."""
    result = Api().get_temp()
    assert result["status"] == 200
    assert result["response"] == 60.0  # hottest mocked core


@pytest.mark.concept("FM-OS.governance.service-writes-fan-level")
def test_set_fan_returns_200():
    """CONCEPT:FM-OS.governance.service-writes-fan-level - set_fan returns a 200 envelope (ipmitool mocked)."""
    assert Api().set_fan(fan_level=40)["status"] == 200


# --------------------------------------------------------------------------- #
# Boundary tests — fan curve at min/max temperature
# --------------------------------------------------------------------------- #
class _FakeRunner:
    """An injectable CommandRunner that returns a fixed temperature (no hardware)."""

    def __init__(self, temp: float):
        self._temp = temp
        self.set_levels: list[int] = []

    def which(self, name: str) -> str:
        return f"/usr/bin/{name}"

    def run(self, argv: list[str], *, check: bool = True) -> str:
        executable = str(argv[0])
        if executable.endswith("sensors"):
            return json.dumps(
                {"coretemp-isa-0000": {"Core 0": {"temp1_input": self._temp}}}
            )
        # ipmitool "raw ... 0x02 0xff 0x<level>" — capture the requested level.
        if len(argv) >= 7 and argv[4] == "0x02":
            self.set_levels.append(int(argv[6], 16))
        return ""


@pytest.mark.concept("FM-OS.governance.service-writes-fan-level")
@pytest.mark.parametrize(
    ("temperature", "expected_level"),
    [
        (40.0, 5),  # below the floor -> minimum fan speed
        (90.0, 100),  # above the ceiling -> maximum fan speed
    ],
)
def test_auto_curve_boundaries(temperature: float, expected_level: int):
    """CONCEPT:FM-OS.governance.service-writes-fan-level — the auto curve clamps to min/max at temp boundaries."""
    runner = _FakeRunner(temperature)
    core.auto_set_fan_speed(
        minimum_fan_speed=5,
        maximum_fan_speed=100,
        minimum_temperature=50,
        maximum_temperature=80,
        temperature_power=5,
        runner=runner,
    )
    assert runner.set_levels[-1] == expected_level


@pytest.mark.concept("FM-OS.governance.service-writes-fan-level")
@pytest.mark.parametrize("bad_level", [-1, 101, 250])
def test_set_fan_rejects_out_of_range(bad_level: int):
    """CONCEPT:FM-OS.governance.service-writes-fan-level — set_fan rejects out-of-range levels with a 400 envelope."""
    runner = _FakeRunner(60.0)
    result = core.set_fan(bad_level, runner=runner)
    assert result["status"] == 400


@pytest.mark.concept("FM-OS.governance.service-reads-temperature-through")
@pytest.mark.concept("FM-OS.governance.service-writes-fan-level")
def test_read_curve_write_integration():
    """Integration: the full CONCEPT:FM-OS.governance.service-reads-temperature-through read -> curve -> CONCEPT:FM-OS.governance.service-writes-fan-level write path.

    Drives ``auto_set_fan_speed`` end-to-end through a single injected runner so a
    real ``sensors``-derived temperature flows into the curve and out to an
    ``ipmitool`` fan-level write — the same chain the CLI/agent exercise live.
    """
    runner = _FakeRunner(65.0)  # mid-range temperature
    core.auto_set_fan_speed(
        minimum_fan_speed=5,
        maximum_fan_speed=100,
        minimum_temperature=50,
        maximum_temperature=80,
        temperature_power=5,
        runner=runner,
    )
    assert runner.set_levels, "expected a fan-level write to reach the BMC"
    assert 5 <= runner.set_levels[-1] <= 100


@pytest.mark.concept("FM-OS.governance.service-writes-fan-level")
def test_auto_failsafe_to_max_on_sensor_error():
    """CONCEPT:FM-OS.governance.service-writes-fan-level — a temperature read failure fails the fans safe to maximum."""

    class _BrokenRunner(_FakeRunner):
        def run(self, argv: list[str], *, check: bool = True) -> str:
            if str(argv[0]).endswith("sensors"):
                return ""  # empty -> get_temp raises -> 500 envelope
            return super().run(argv, check=check)

    runner = _BrokenRunner(0.0)
    core.auto_set_fan_speed(maximum_fan_speed=100, runner=runner)
    assert runner.set_levels[-1] == 100
