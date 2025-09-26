#!/usr/bin/env python
# coding: utf-8

import os
import sys
import argparse
import json
import time
import logging
from typing import Union, Dict, Any


def setup_logging(
    is_mcp_server: bool = False, log_file: str = "fan_manager.log"
) -> None:
    """
    Configure logging for the fan manager application.
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


def get_core_temp(cpus: list, sensors: dict) -> Dict[str, Any]:
    """
    Get the highest core temperature from the specified CPUs.
    Returns a dictionary with response, command, and status.
    """
    logger = logging.getLogger("FanManager")
    highest_temp = 0.0
    highest_core = 0
    highest_cpu = ""
    cores = 0
    temp_cpu = 0.0
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
                temp_cpu = highest_temp
        logger.info(
            f"Highest CPU: {highest_cpu}, Core: {highest_core}, Temperature: {highest_temp}"
        )
        return {"response": temp_cpu, "command": command, "status": 200}
    except Exception as e:
        logger.error(f"Failed to get core temperature: {str(e)}")
        return {"response": None, "command": command, "status": 500, "error": str(e)}


def get_temp() -> Dict[str, Any]:
    """
    Get the current CPU temperature.
    Returns a dictionary with response, command, and status.
    """
    logger = logging.getLogger("FanManager")
    command = "sensors -j"
    try:
        sensors = json.loads(os.popen("sensors -j").read())
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


def set_fan(fan_level: int) -> Dict[str, Any]:
    """
    Set the fan speed to the specified level.
    Returns a dictionary with response, command, and status.
    """
    logger = logging.getLogger("FanManager")
    try:
        if not (0 <= fan_level <= 100):
            raise ValueError(f"Fan level {fan_level} is out of range (0-100)")
        # Manual fan control
        cmd1 = "ipmitool raw 0x30 0x30 0x01 0x00"
        os.system(cmd1)
        # Set fan level
        cmd2 = f"ipmitool raw 0x30 0x30 0x02 0xff {hex(fan_level)}"
        os.system(cmd2)
        logger.info(f"Set fan level to {fan_level}")
        return {"response": None, "command": f"{cmd1}; {cmd2}", "status": 200}
    except ValueError as e:
        logger.error(f"Invalid fan level: {str(e)}")
        return {
            "response": None,
            "command": cmd2 if "cmd2" in locals() else "ipmitool raw",
            "status": 400,
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Failed to set fan level: {str(e)}")
        return {
            "response": None,
            "command": cmd2 if "cmd2" in locals() else "ipmitool raw",
            "status": 500,
            "error": str(e),
        }


def auto_set_fan_speed(
    minimum_fan_speed: Union[int, float] = 5,
    maximum_fan_speed: Union[int, float] = 100,
    minimum_temperature: Union[int, float] = 50,
    maximum_temperature: Union[int, float] = 80,
    temperature_power: int = 5,
):
    logger = logging.getLogger("FanManager")
    logger.info("Starting fan manager service")
    temp_result = get_temp()
    if temp_result["status"] != 200:
        logger.error(
            f"Skipping fan adjustment due to temperature error: {temp_result.get('error', 'Unknown error')}"
        )
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
    fan_result = set_fan(fan_level)
    if fan_result["status"] != 200:
        logger.error(f"Failed to set fan: {fan_result.get('error', 'Unknown error')}")


def run_service(
    temperature_poll_rate: int = 24,
    minimum_fan_speed: Union[int, float] = 5,
    maximum_fan_speed: Union[int, float] = 100,
    minimum_temperature: Union[int, float] = 50,
    maximum_temperature: Union[int, float] = 80,
    temperature_power: int = 5,
):
    logger = logging.getLogger("FanManager")
    logger.info("Starting fan manager service")
    while True:
        auto_set_fan_speed(
            minimum_fan_speed=minimum_fan_speed,
            maximum_fan_speed=maximum_fan_speed,
            minimum_temperature=minimum_temperature,
            maximum_temperature=maximum_temperature,
            temperature_power=temperature_power,
        )
        time.sleep(temperature_poll_rate)


def usage():
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
