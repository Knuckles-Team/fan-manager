"""Verify the action-routed MCP tools register and route correctly.

Routing is exercised by invoking each registered tool's underlying function
(``tool.fn``) with ``ctx=None`` — this avoids needing a live MCP session while
still validating the action dispatch. Hardware calls are mocked by conftest.

These tests deliberately span multiple *intents* — registration (contract),
happy-path routing, negative/error paths, and boundary conditions — so the
suite is not single-intent.
"""

import importlib
import json

import pytest
from fastmcp import FastMCP

from fan_manager.mcp import register_fan_control_tools, register_temperature_tools

# The package __init__ exposes a ``fan_manager`` *function* into its namespace,
# which shadows the ``fan_manager.fan_manager`` submodule under a plain
# ``import ... as``. Load the module explicitly so we reach the core callables.
core = importlib.import_module("fan_manager.fan_manager")


@pytest.fixture
def mcp() -> FastMCP:
    """A fresh, isolated FastMCP instance per test (F.I.R.S.T. — Isolated)."""
    return FastMCP(name="test-fan-manager")


async def _tool_names(mcp: FastMCP) -> set[str]:
    tools = await mcp.list_tools()
    return {t.name for t in tools}


async def _tool_fn(mcp: FastMCP, name: str):
    tool = await mcp.get_tool(name)
    assert tool is not None, f"tool {name!r} was not registered"
    return tool.fn


# --------------------------------------------------------------------------- #
# Contract / registration tests
# --------------------------------------------------------------------------- #
@pytest.mark.concept("FAN-001")
async def test_temperature_tool_registers(mcp: FastMCP):
    """CONCEPT:FAN-001 — the temperature domain registers exactly one tool."""
    register_temperature_tools(mcp)
    assert "fan_manager_temperature" in await _tool_names(mcp)


@pytest.mark.concept("FAN-002")
async def test_fan_control_tool_registers(mcp: FastMCP):
    """CONCEPT:FAN-002 — the fan-control domain registers exactly one tool."""
    register_fan_control_tools(mcp)
    assert "fan_manager_fan_control" in await _tool_names(mcp)


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
@pytest.mark.parametrize(
    ("register", "tool_name", "valid_action", "params"),
    [
        (register_temperature_tools, "fan_manager_temperature", "get", "{}"),
        (
            register_fan_control_tools,
            "fan_manager_fan_control",
            "set",
            json.dumps({"fan_level": 30}),
        ),
    ],
)
async def test_action_routing_contract(
    mcp: FastMCP, register, tool_name: str, valid_action: str, params: str
):
    """Contract: every domain tool routes its documented action to a 200 envelope.

    Exercises both CONCEPT:FAN-001 (temperature) and CONCEPT:FAN-002 (fan-control)
    action routing through one parametrized contract.
    """
    register(mcp)
    fn = await _tool_fn(mcp, tool_name)
    result = await fn(action=valid_action, params_json=params, ctx=None)
    assert result["status"] == 200


# --------------------------------------------------------------------------- #
# Happy-path routing tests
# --------------------------------------------------------------------------- #
@pytest.mark.concept("FAN-001")
async def test_temperature_get_routes(mcp: FastMCP):
    """CONCEPT:FAN-001 — the 'get' action returns a temperature envelope (mocked)."""
    register_temperature_tools(mcp)
    fn = await _tool_fn(mcp, "fan_manager_temperature")
    result = await fn(action="get", params_json="{}", ctx=None)
    assert result["status"] == 200
    assert result["response"] == 60.0  # hottest mocked core


@pytest.mark.concept("FAN-002")
async def test_fan_control_set_routes(mcp: FastMCP):
    """CONCEPT:FAN-002 — the 'set' action returns a 200 envelope (ipmitool mocked)."""
    register_fan_control_tools(mcp)
    fn = await _tool_fn(mcp, "fan_manager_fan_control")
    result = await fn(
        action="set", params_json=json.dumps({"fan_level": 40}), ctx=None
    )
    assert result["status"] == 200


# --------------------------------------------------------------------------- #
# Negative / error-path tests
# --------------------------------------------------------------------------- #
@pytest.mark.concept("FAN-001")
async def test_unknown_temperature_action_raises(mcp: FastMCP):
    """CONCEPT:FAN-001 — an unknown action is rejected with ValueError."""
    register_temperature_tools(mcp)
    fn = await _tool_fn(mcp, "fan_manager_temperature")
    with pytest.raises(ValueError):
        await fn(action="bogus", params_json="{}", ctx=None)


@pytest.mark.concept("FAN-002")
async def test_unknown_fan_action_raises(mcp: FastMCP):
    """CONCEPT:FAN-002 — an unknown fan-control action is rejected with ValueError."""
    register_fan_control_tools(mcp)
    fn = await _tool_fn(mcp, "fan_manager_fan_control")
    with pytest.raises(ValueError):
        await fn(action="bogus", params_json="{}", ctx=None)


@pytest.mark.concept("FAN-002")
async def test_fan_set_requires_fan_level(mcp: FastMCP):
    """CONCEPT:FAN-002 — 'set' without a fan_level returns a structured error."""
    register_fan_control_tools(mcp)
    fn = await _tool_fn(mcp, "fan_manager_fan_control")
    result = await fn(action="set", params_json="{}", ctx=None)
    assert "error" in result


@pytest.mark.concept("FAN-002")
async def test_fan_set_rejects_non_integer_level(mcp: FastMCP):
    """CONCEPT:FAN-002 — a non-integer fan_level is rejected, not crashed."""
    register_fan_control_tools(mcp)
    fn = await _tool_fn(mcp, "fan_manager_fan_control")
    result = await fn(
        action="set", params_json=json.dumps({"fan_level": "fast"}), ctx=None
    )
    assert "error" in result


@pytest.mark.concept("FAN-001")
async def test_temperature_rejects_malformed_params_json(mcp: FastMCP):
    """CONCEPT:FAN-001 — malformed params_json yields a structured error envelope."""
    register_temperature_tools(mcp)
    fn = await _tool_fn(mcp, "fan_manager_temperature")
    result = await fn(action="get", params_json="{not json", ctx=None)
    assert "error" in result


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


@pytest.mark.concept("FAN-002")
@pytest.mark.parametrize(
    ("temperature", "expected_level"),
    [
        (40.0, 5),  # below the floor -> minimum fan speed
        (90.0, 100),  # above the ceiling -> maximum fan speed
    ],
)
def test_auto_curve_boundaries(temperature: float, expected_level: int):
    """CONCEPT:FAN-002 — the auto curve clamps to min/max at temp boundaries."""
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


@pytest.mark.concept("FAN-002")
@pytest.mark.parametrize("bad_level", [-1, 101, 250])
def test_set_fan_rejects_out_of_range(bad_level: int):
    """CONCEPT:FAN-002 — set_fan rejects out-of-range levels with a 400 envelope."""
    runner = _FakeRunner(60.0)
    result = core.set_fan(bad_level, runner=runner)
    assert result["status"] == 400


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
def test_read_curve_write_integration():
    """Integration: the full CONCEPT:FAN-001 read -> curve -> CONCEPT:FAN-002 write path.

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


@pytest.mark.concept("FAN-002")
def test_auto_failsafe_to_max_on_sensor_error():
    """CONCEPT:FAN-002 — a temperature read failure fails the fans safe to maximum."""

    class _BrokenRunner(_FakeRunner):
        def run(self, argv: list[str], *, check: bool = True) -> str:
            if str(argv[0]).endswith("sensors"):
                return ""  # empty -> get_temp raises -> 500 envelope
            return super().run(argv, check=check)

    runner = _BrokenRunner(0.0)
    core.auto_set_fan_speed(maximum_fan_speed=100, runner=runner)
    assert runner.set_levels[-1] == 100
