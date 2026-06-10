#!/usr/bin/env python

import argparse
import json
import logging
import shutil
import subprocess
import sys
import time
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CommandRunner(Protocol):
    """Seam for resolving and executing the local ``sensors``/``ipmitool`` binaries.

    Fan Manager shells out to hardware tools (CONCEPT:FAN-001 reads temperature
    via ``sensors``; CONCEPT:FAN-002 drives the BMC via ``ipmitool``). Injecting
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

    Bootstraps the logging used across the CONCEPT:FAN-001 temperature read path
    and the CONCEPT:FAN-002 fan-control path.
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
    Get the highest core temperature from the specified CPUs (CONCEPT:FAN-001).

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
    Get the current CPU temperature (CONCEPT:FAN-001).

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
    Set the fan speed to the specified level (CONCEPT:FAN-002).

    Validates ``fan_level`` (0-100) and drives the BMC through the injected
    :class:`CommandRunner` (defaulting to ``ipmitool`` raw commands).
    Returns a dictionary with response, command, and status.
    """
    runner = runner or _DEFAULT_RUNNER
    logger = logging.getLogger("FanManager")
    cmd2_str = "ipmitool raw"
    try:
        if not (0 <= fan_level <= 100):
            raise ValueError(f"Fan level {fan_level} is out of range (0-100)")
        ipmitool_bin = runner.which("ipmitool")
        if ipmitool_bin is None:
            raise RuntimeError("'ipmitool' executable not found on PATH")
        # fan_level is validated to be an int in [0, 100] above; hex() yields a
        # safe "0x.." token. argv is fixed and shell=False, so no injection is
        # possible despite the BMC raw command.
        cmd1 = [ipmitool_bin, "raw", "0x30", "0x30", "0x01", "0x00"]
        cmd2 = [ipmitool_bin, "raw", "0x30", "0x30", "0x02", "0xff", hex(fan_level)]
        cmd2_str = " ".join(cmd2)
        # Enable manual fan control.
        runner.run(cmd1, check=True)
        # Apply the requested fan level.
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
        logger.error(f"Failed to set fan level: {str(e)}")
        return {
            "response": None,
            "command": cmd2_str,
            "status": 500,
            "error": str(e),
        }


def auto_set_fan_speed(
    minimum_fan_speed: int | float = 5,
    maximum_fan_speed: int | float = 100,
    minimum_temperature: int | float = 50,
    maximum_temperature: int | float = 80,
    temperature_power: int = 5,
    runner: CommandRunner | None = None,
):
    """Drive the temperature-to-fan-speed curve once (CONCEPT:FAN-002).

    Reads the current temperature (CONCEPT:FAN-001) via the injected
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


def run_service(
    temperature_poll_rate: int = 24,
    minimum_fan_speed: int | float = 5,
    maximum_fan_speed: int | float = 100,
    minimum_temperature: int | float = 50,
    maximum_temperature: int | float = 80,
    temperature_power: int = 5,
    runner: CommandRunner | None = None,
):
    """Continuously poll temperature and adjust fans (CONCEPT:FAN-002 loop).

    Each tick re-runs :func:`auto_set_fan_speed` (CONCEPT:FAN-001 read +
    CONCEPT:FAN-002 write) through the injected :class:`CommandRunner`, then
    sleeps for ``temperature_poll_rate`` seconds.
    """
    runner = runner or _DEFAULT_RUNNER
    logger = logging.getLogger("FanManager")
    logger.info("Starting fan manager service")
    while True:
        auto_set_fan_speed(
            minimum_fan_speed=minimum_fan_speed,
            maximum_fan_speed=maximum_fan_speed,
            minimum_temperature=minimum_temperature,
            maximum_temperature=maximum_temperature,
            temperature_power=temperature_power,
            runner=runner,
        )
        time.sleep(temperature_poll_rate)


def usage():
    """Print CLI usage for the fan-control service (CONCEPT:FAN-002)."""
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

    Wires the temperature read (CONCEPT:FAN-001) and fan-control (CONCEPT:FAN-002)
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
