#!/usr/bin/env python

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from typing import Any, Protocol, runtime_checkable

# --- per-process (= per-host DaemonSet pod) fan-mode + thermal-trend state ---
_FAN_MODE = "manual"  # flips to "idrac-auto" if the BMC rejects raw manual control
_thermal_buf: list = []  # (ts, temp, fan_level) rolling window, distilled periodically
_thermal_last_flush = [0.0]  # mutable single-cell so the closure can update it


def _kg_record_thermal_sample(temperature: Any, fan_level: int) -> None:
    """Best-effort thermal telemetry into epistemic-graph — as DECAYING TRENDS, not every ping.

    CONCEPT:AU-KG.ingest.enterprise-source-extractor. Samples accumulate in a small in-memory
    window and are distilled to ONE :ServerThermalTrend reading per FAN_MANAGER_KG_AGGREGATE_S
    (default 1h): min/max/avg temp + avg fan + sample count, related to the host. The
    high-resolution stream stays in Prometheus; the KG keeps lightweight long-term patterns so
    the DB never bloats. Default-on; disable with ``FAN_MANAGER_KG_INGEST=false``. Fully guarded
    — a missing/unreachable KG is a silent no-op that never disturbs the control loop.
    """
    if os.getenv("FAN_MANAGER_KG_INGEST", "true").strip().lower() in {
        "0",
        "false",
        "no",
    }:
        return
    import time

    try:
        temp_val = float(temperature) if temperature is not None else None
    except (TypeError, ValueError):
        temp_val = None
    now = time.time()
    _thermal_buf.append((now, temp_val, fan_level))
    agg_s = int(os.getenv("FAN_MANAGER_KG_AGGREGATE_S", "3600"))
    # Accumulate; only distill when the window elapses (or a hard cap guards memory).
    if now - _thermal_last_flush[0] < agg_s and len(_thermal_buf) < 5000:
        return
    temps = [t for _, t, _ in _thermal_buf if t is not None]
    fans = [f for _, _, f in _thermal_buf]
    n = len(_thermal_buf)
    _thermal_buf.clear()
    _thermal_last_flush[0] = now
    if not temps:
        return
    trend = {
        "min_temp": min(temps),
        "max_temp": max(temps),
        "avg_temp": round(sum(temps) / len(temps), 1),
        "avg_fan": round(sum(fans) / len(fans), 1) if fans else None,
        "fan_mode": _FAN_MODE,
        "samples": n,
        "window_s": agg_s,
    }
    logger = logging.getLogger("FanManager")
    try:
        from fan_manager.kg_ingest import ingest_thermal_trend

        # Clean, numeric :ThermalTrend node so the derivation loop (fan_manager.kg_control)
        # can read min/avg/max °C + avg fan straight back for baseline learning.
        ingest_thermal_trend(trend, host=os.getenv("FAN_MANAGER_HOST") or None)
        logger.info(
            "KG thermal trend: avg=%s max=%s min=%s avg_fan=%s mode=%s over %d samples",
            trend["avg_temp"],
            trend["max_temp"],
            trend["min_temp"],
            trend["avg_fan"],
            _FAN_MODE,
            n,
        )
    except Exception as e:  # noqa: BLE001 — ingestion is best-effort, never fatal
        logger.debug("KG trend ingest skipped: %s", e)


@runtime_checkable
class CommandRunner(Protocol):
    """Seam for resolving and executing the local ``sensors``/``ipmitool`` binaries.

    Fan Manager shells out to hardware tools (CONCEPT:FM-OS.governance.service-reads-temperature-through reads temperature
    via ``sensors``; CONCEPT:FM-OS.governance.service-writes-fan-level drives the BMC via ``ipmitool``). Injecting
    this runner lets callers and tests substitute the shell-out without globally
    monkeypatching :mod:`subprocess`, keeping the dependency-injection seam
    explicit and the tests hermetic.
    """

    def which(self, name: str) -> str | None:
        """Resolve an executable on ``PATH`` (``None`` if absent)."""
        ...

    def run(self, argv: list[str], *, check: bool = True) -> str:
        """Run a fixed argv with ``shell=False`` and return captured stdout."""
        ...


class SubprocessCommandRunner:
    """Default :class:`CommandRunner` backed by ``shutil.which``/``subprocess.run``.

    Uses fixed argv with ``shell=False`` and resolves binaries via
    ``shutil.which`` so no user input ever reaches a command line.
    """

    def which(self, name: str) -> str | None:
        return shutil.which(name)

    def run(self, argv: list[str], *, check: bool = True) -> str:
        # Fixed argv, shell=False: no user input reaches the command line.
        completed = subprocess.run(  # nosec B603 - fixed argv, no shell, no user input
            argv,
            capture_output=True,
            text=True,
            check=check,
        )
        return completed.stdout


# Module-level default runner. Callers may pass their own ``CommandRunner`` to
# the temperature/fan functions for testing or alternate execution backends.
_DEFAULT_RUNNER: CommandRunner = SubprocessCommandRunner()


def setup_logging(
    is_mcp_server: bool = False, log_file: str = "fan_manager.log"
) -> None:
    """
    Configure logging for the fan manager application.

    Bootstraps the logging used across the CONCEPT:FM-OS.governance.service-reads-temperature-through temperature read path
    and the CONCEPT:FM-OS.governance.service-writes-fan-level fan-control path.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(
                log_file if not is_mcp_server else "fan_manager_mcp.log"
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )


def get_core_temp(cpus: list, sensors: dict) -> dict[str, Any]:
    """
    Get the highest core temperature from the specified CPUs (CONCEPT:FM-OS.governance.service-reads-temperature-through).

    Pure computation over a supplied ``sensors`` mapping (no shell-out).
    Returns a dictionary with response, command, and status.
    """
    logger = logging.getLogger("FanManager")
    highest_temp = 0.0
    highest_core = 0
    highest_cpu = ""
    cores = 0
    command = "sensors -j"

    try:
        for cpu in cpus:
            if cpu in sensors:
                for key in sensors[cpu].keys():
                    if "Core" in key:
                        cores += 1
                        for temp_key in sensors[cpu][key].keys():
                            if "_input" in temp_key:
                                temp_cpu = sensors[cpu][key][temp_key]
                                if temp_cpu > highest_temp:
                                    highest_temp = temp_cpu
                                    highest_core = cores
                                    highest_cpu = cpu
        logger.info(
            f"Highest CPU: {highest_cpu}, Core: {highest_core}, Temperature: {highest_temp}"
        )
        return {"response": highest_temp, "command": command, "status": 200}
    except Exception as e:
        logger.error(f"Failed to get core temperature: {str(e)}")
        return {"response": None, "command": command, "status": 500, "error": str(e)}


def get_temp(runner: CommandRunner | None = None) -> dict[str, Any]:
    """
    Get the current CPU temperature (CONCEPT:FM-OS.governance.service-reads-temperature-through).

    Reads the host's sensors via the injected :class:`CommandRunner` (defaulting
    to a real ``sensors -j`` shell-out) and returns the hottest core temperature.
    Returns a dictionary with response, command, and status.
    """
    runner = runner or _DEFAULT_RUNNER
    logger = logging.getLogger("FanManager")
    command = "sensors -j"
    try:
        sensors_bin = runner.which("sensors")
        if sensors_bin is None:
            raise RuntimeError("'sensors' executable not found on PATH")
        sensors_output = runner.run([sensors_bin, "-j"], check=True)
        if not sensors_output.strip():
            raise RuntimeError("No output from 'sensors -j' command")
        sensors = json.loads(sensors_output)
        cpus = ["coretemp-isa-0000", "coretemp-isa-0001"]
        temp_result = get_core_temp(cpus, sensors)
        if temp_result["status"] != 200:
            raise RuntimeError(
                temp_result.get("error", "Failed to get core temperature")
            )
        temp_cpu = temp_result["response"]
        logger.info(f"Current Temperature: {temp_cpu}")
        return {"response": temp_cpu, "command": command, "status": 200}
    except Exception as e:
        logger.error(f"Failed to get temperature: {str(e)}")
        return {"response": None, "command": command, "status": 500, "error": str(e)}


def set_fan(fan_level: int, runner: CommandRunner | None = None) -> dict[str, Any]:
    """
    Set the fan speed to the specified level (CONCEPT:FM-OS.governance.service-writes-fan-level).

    Validates ``fan_level`` (0-100) and drives the BMC through the injected
    :class:`CommandRunner` (defaulting to ``ipmitool`` raw commands).
    Returns a dictionary with response, command, and status.
    """
    runner = runner or _DEFAULT_RUNNER
    logger = logging.getLogger("FanManager")
    cmd2_str = "ipmitool raw"
    global _FAN_MODE
    try:
        if not (0 <= fan_level <= 100):
            raise ValueError(f"Fan level {fan_level} is out of range (0-100)")
        ipmitool_bin = runner.which("ipmitool")
        if ipmitool_bin is None:
            raise RuntimeError("'ipmitool' executable not found on PATH")
        # The BMC already told us it won't accept raw manual control here — iDRAC's automatic
        # fan curve owns cooling. Don't hammer it every cycle; just report the mode.
        if _FAN_MODE == "idrac-auto":
            return {
                "response": None,
                "command": "idrac-auto (bmc-managed)",
                "status": 200,
                "mode": "idrac-auto",
            }
        # fan_level is validated to be an int in [0, 100] above; hex() yields a
        # safe "0x.." token. argv is fixed and shell=False, so no injection is possible.
        cmd1 = [
            ipmitool_bin,
            "raw",
            "0x30",
            "0x30",
            "0x01",
            "0x00",
        ]  # enable manual control
        cmd2 = [ipmitool_bin, "raw", "0x30", "0x30", "0x02", "0xff", hex(fan_level)]
        cmd2_str = " ".join(cmd2)
        runner.run(cmd1, check=True)
        runner.run(cmd2, check=True)
        logger.info(f"Set fan level to {fan_level}")
        return {
            "response": None,
            "command": f"{' '.join(cmd1)}; {cmd2_str}",
            "status": 200,
        }
    except ValueError as e:
        logger.error(f"Invalid fan level: {str(e)}")
        return {
            "response": None,
            "command": cmd2_str,
            "status": 400,
            "error": str(e),
        }
    except Exception as e:
        # SMART fallback: some BMC firmware (e.g. the R510's older iDRAC) rejects the raw
        # manual-control command. Rather than erroring EVERY cycle, enable iDRAC AUTOMATIC
        # fan management ONCE and stop retrying raw control on this host — safe + quiet.
        try:
            auto_bin = runner.which("ipmitool") or "ipmitool"
            runner.run([auto_bin, "raw", "0x30", "0x30", "0x01", "0x01"], check=True)
            _FAN_MODE = "idrac-auto"
            logger.warning(
                "BMC rejected raw manual fan control (%s) — enabled iDRAC AUTOMATIC fan "
                "management; not retrying raw control on this host.",
                e,
            )
            return {
                "response": None,
                "command": "0x30 0x30 0x01 0x01",
                "status": 200,
                "mode": "idrac-auto",
            }
        except Exception as e2:
            logger.error(f"Failed to set fan level and to enable iDRAC-auto: {e2}")
            return {
                "response": None,
                "command": cmd2_str,
                "status": 500,
                "error": str(e2),
            }


def auto_set_fan_speed(
    minimum_fan_speed: int | float = 5,
    maximum_fan_speed: int | float = 100,
    minimum_temperature: int | float = 50,
    maximum_temperature: int | float = 80,
    temperature_power: int = 5,
    runner: CommandRunner | None = None,
):
    """Drive the temperature-to-fan-speed curve once (CONCEPT:FM-OS.governance.service-writes-fan-level).

    Reads the current temperature (CONCEPT:FM-OS.governance.service-reads-temperature-through) via the injected
    :class:`CommandRunner` and applies a logarithmic temperature-to-speed curve.
    On a temperature read error, the fans fail safe to ``maximum_fan_speed``.
    """
    runner = runner or _DEFAULT_RUNNER
    logger = logging.getLogger("FanManager")
    temp_result = get_temp(runner=runner)
    if temp_result["status"] != 200:
        logger.error(
            f"Skipping fan adjustment due to temperature error: {temp_result.get('error', 'Unknown error')}. Setting fan to maximum as fallback."
        )
        fan_result = set_fan(int(maximum_fan_speed), runner=runner)
        if fan_result["status"] != 200:
            logger.error(
                f"Failed to set fallback fan: {fan_result.get('error', 'Unknown error')}"
            )
        return  # Exit early to avoid computation with None

    cpu_temperature = temp_result["response"]
    x: float = min(
        1.0,
        max(
            0.0,
            (cpu_temperature - minimum_temperature)
            / (maximum_temperature - minimum_temperature),
        ),
    )
    fan_level = int(
        min(
            maximum_fan_speed,
            max(
                minimum_fan_speed,
                pow(x, temperature_power) * (maximum_fan_speed - minimum_fan_speed)
                + minimum_fan_speed,
            ),
        )
    )
    fan_result = set_fan(fan_level, runner=runner)
    if fan_result["status"] != 200:
        logger.error(f"Failed to set fan: {fan_result.get('error', 'Unknown error')}")
    # Native, best-effort timeseries ingestion of this thermal sample.
    _kg_record_thermal_sample(cpu_temperature, fan_level)


def _clamp(value: Any, lo: int, hi: int, fallback: int) -> int:
    """Coerce ``value`` to an int within ``[lo, hi]``; ``fallback`` if it isn't a number."""
    try:
        return max(lo, min(hi, int(round(float(value)))))
    except (TypeError, ValueError):
        return fallback


def load_fan_policy(
    defaults: dict[str, Any], host: str | None = None
) -> dict[str, Any]:
    """Phase 2 control seam: overlay an *approved* per-host FanPolicy on the CLI ``defaults``.

    Reads ``FAN_MANAGER_POLICY_FILE`` — a JSON map ``{"<host>": {cold,warm,slow,fast,poll,
    approved}, "*": {...}}`` (e.g. a mounted ConfigMap the epistemic-graph derivation loop
    writes). Only an ``approved`` entry is applied; every value is clamped and an invalid
    curve (``cold>=warm`` / ``slow>=fast``) falls back to ``defaults``. Missing file / bad
    JSON / no host match ⇒ ``defaults`` unchanged — the fail-safe curve always wins. This is
    the ONLY place a KG-derived policy can change fan behaviour, and it can only ever tune
    within these bounds.
    """
    path = os.getenv("FAN_MANAGER_POLICY_FILE")
    if not path or not os.path.exists(path):
        return defaults
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:  # noqa: BLE001 — unreadable/invalid policy file → safe fallback
        return defaults
    host = host or os.getenv("FAN_MANAGER_HOST") or os.uname().nodename
    pol = data.get(host) or data.get("*") or {}
    if not isinstance(pol, dict) or not pol.get("approved"):
        return defaults
    cold = _clamp(pol.get("cold"), 40, 90, int(defaults["minimum_temperature"]))
    warm = _clamp(pol.get("warm"), 40, 90, int(defaults["maximum_temperature"]))
    slow = _clamp(pol.get("slow"), 0, 100, int(defaults["minimum_fan_speed"]))
    fast = _clamp(pol.get("fast"), 0, 100, int(defaults["maximum_fan_speed"]))
    if cold >= warm or slow >= fast:  # incoherent curve — never apply it
        return defaults
    out = dict(defaults)
    out.update(
        minimum_temperature=cold,
        maximum_temperature=warm,
        minimum_fan_speed=slow,
        maximum_fan_speed=fast,
    )
    if pol.get("poll") is not None:
        out["temperature_poll_rate"] = _clamp(
            pol.get("poll"), 1, 300, int(defaults["temperature_poll_rate"])
        )
    logging.getLogger("FanManager").info(
        "Applied KG-approved fan policy for %s: cold=%s warm=%s slow=%s fast=%s",
        host,
        cold,
        warm,
        slow,
        fast,
    )
    return out


def run_service(
    temperature_poll_rate: int = 24,
    minimum_fan_speed: int | float = 5,
    maximum_fan_speed: int | float = 100,
    minimum_temperature: int | float = 50,
    maximum_temperature: int | float = 80,
    temperature_power: int = 5,
    runner: CommandRunner | None = None,
):
    """Continuously poll temperature and adjust fans (CONCEPT:FM-OS.governance.service-writes-fan-level loop).

    Each tick re-runs :func:`auto_set_fan_speed` (CONCEPT:FM-OS.governance.service-reads-temperature-through read +
    CONCEPT:FM-OS.governance.service-writes-fan-level write) through the injected :class:`CommandRunner`, then
    sleeps for the active poll rate. Every ``FAN_MANAGER_POLICY_REFRESH`` ticks (default 20)
    the curve is re-read via :func:`load_fan_policy`, so an epistemic-graph-approved policy
    hot-reloads without restarting the pod (CONCEPT:FM-OS.control.policy-source-seam).
    """
    runner = runner or _DEFAULT_RUNNER
    logger = logging.getLogger("FanManager")
    logger.info("Starting fan manager service")
    base = {
        "temperature_poll_rate": temperature_poll_rate,
        "minimum_fan_speed": minimum_fan_speed,
        "maximum_fan_speed": maximum_fan_speed,
        "minimum_temperature": minimum_temperature,
        "maximum_temperature": maximum_temperature,
        "temperature_power": temperature_power,
    }
    refresh = _clamp(os.getenv("FAN_MANAGER_POLICY_REFRESH", "20"), 0, 100000, 20)
    curve = load_fan_policy(base)
    tick = 0
    while True:
        if refresh and tick % refresh == 0:
            curve = load_fan_policy(base)
        auto_set_fan_speed(
            minimum_fan_speed=curve["minimum_fan_speed"],
            maximum_fan_speed=curve["maximum_fan_speed"],
            minimum_temperature=curve["minimum_temperature"],
            maximum_temperature=curve["maximum_temperature"],
            temperature_power=curve["temperature_power"],
            runner=runner,
        )
        time.sleep(curve["temperature_poll_rate"])
        tick += 1


def usage():
    """Print CLI usage for the fan-control service (CONCEPT:FM-OS.governance.service-writes-fan-level)."""
    logger = logging.getLogger("FanManager")
    logger.info(
        "Usage: \n"
        "-h | --help      [ See usage for fan-speed ]\n"
        "-i | --intensity [ Intensity of Fan Speed - Scales Logarithmically (0-10) ]\n"
        "-c | --cold      [ Minimum Temperature for Fan Speed (40-90) ]\n"
        "-w | --warm      [ Maximum Temperature for Fan Speed (40-90) ]\n"
        "-s | --slow      [ Minimum Fan Speed (0-100) ]\n"
        "-f | --fast      [ Maximum Fan Speed (0-100) ]\n"
        "-p | --poll-rate [ Poll Rate for CPU Temperature in Seconds (1-300) ]\n"
        "\nExample: \n\t"
        "fan-manager --intensity 5 --cold 50 --warm 80 --slow 5 --fast 100 --poll-rate 24\n"
    )


def fan_manager():
    """CLI entrypoint: parse args and run the fan-management service loop.

    Wires the temperature read (CONCEPT:FM-OS.governance.service-reads-temperature-through) and fan-control (CONCEPT:FM-OS.governance.service-writes-fan-level)
    paths together as a long-running poller.
    """
    setup_logging()
    logger = logging.getLogger("FanManager")
    logger.debug("Initializing fan manager")

    # Define default values
    defaults = {
        "temperature_poll_rate": 24,
        "minimum_fan_speed": 5,
        "maximum_fan_speed": 100,
        "minimum_temperature": 50,
        "maximum_temperature": 80,
        "temperature_power": 5,
    }

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Fan manager tool to control fan speeds based on temperature.",
        add_help=False,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message and exit",
    )
    parser.add_argument(
        "-i",
        "--intensity",
        type=int,
        default=defaults["temperature_power"],
        help="Temperature power intensity (default: %(default)s)",
    )
    parser.add_argument(
        "-c",
        "--cold",
        type=int,
        default=defaults["minimum_temperature"],
        help="Minimum temperature (default: %(default)s)",
    )
    parser.add_argument(
        "-w",
        "--warm",
        type=int,
        default=defaults["maximum_temperature"],
        help="Maximum temperature (default: %(default)s)",
    )
    parser.add_argument(
        "-s",
        "--slow",
        type=int,
        default=defaults["minimum_fan_speed"],
        help="Minimum fan speed (default: %(default)s)",
    )
    parser.add_argument(
        "-f",
        "--fast",
        type=int,
        default=defaults["maximum_fan_speed"],
        help="Maximum fan speed (default: %(default)s)",
    )
    parser.add_argument(
        "-p",
        "--poll-rate",
        type=int,
        default=defaults["temperature_poll_rate"],
        help="Temperature poll rate (default: %(default)s)",
    )

    try:
        args = parser.parse_args()
    except SystemExit:
        usage()
        sys.exit(2)

    run_service(
        temperature_poll_rate=args.poll_rate,
        minimum_fan_speed=args.slow,
        maximum_fan_speed=args.fast,
        minimum_temperature=args.cold,
        maximum_temperature=args.warm,
        temperature_power=args.intensity,
    )


if __name__ == "__main__":
    fan_manager()
