#!/usr/bin/env python
# coding: utf-8

import os
import sys
import argparse
import json
import time


def get_core_temp(cpus, sensors) -> int:
    highest_temp = 0
    highest_core = 0
    highest_cpu = ""
    cores = 0
    temp_cpu = 0
    for cpu in cpus:
        if cpu in sensors:
            for key in sensors[cpu].keys():
                if "Core" in key:
                    cores = cores + 1
                    for temp_key in sensors[cpu][key].keys():
                        if "_input" in temp_key:
                            temp_cpu = sensors[cpu][key][temp_key]
                            if temp_cpu > highest_temp:
                                highest_temp = temp_cpu
                                highest_core = cores
                                highest_cpu = cpu
            temp_cpu = highest_temp
    print(
        f"Highest \n\tCPU: {highest_cpu} \n\tCore: {highest_core} \n\tTemperature: {highest_temp}"
    )
    return temp_cpu


def get_temp() -> float:
    sensors = json.loads(os.popen("sensors -j").read())
    cpus = ["coretemp-isa-0000", "coretemp-isa-0001"]
    temp_cpu = get_core_temp(cpus, sensors)
    print(f"Current Temperature: {temp_cpu}")
    return temp_cpu


def set_fan(fan_level: int):
    # manual fan control
    cmd = "ipmitool raw 0x30 0x30 0x01 0x00"
    os.system(cmd)
    # set fan level
    cmd = f"ipmitool raw 0x30 0x30 0x02 0xff {hex(fan_level)}"
    os.system(cmd)


def run_service(
    temperature_poll_rate: int = 24,
    minimum_fan_speed: int = 5,
    maximum_fan_speed: int = 100,
    minimum_temperature: int = 50,
    maximum_temperature: int = 80,
    temperature_power: int = 5,
):
    while True:
        cpu_temperature = get_temp()
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
                    int(
                        pow(x, temperature_power) * (maximum_fan_speed - minimum_fan_speed)
                        + minimum_fan_speed
                    ),
                ),
            )
        )
        set_fan(fan_level)
        time.sleep(temperature_poll_rate)



def usage():
    print(
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
    # Define default values
    defaults = {
        'temperature_poll_rate': 24,
        'minimum_fan_speed': 5,
        'maximum_fan_speed': 100,
        'minimum_temperature': 50,
        'maximum_temperature': 80,
        'temperature_power': 5
    }

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Fan manager tool to control fan speeds based on temperature.",
        add_help=False  # Disable default help to customize it
    )
    parser.add_argument(
        '-h', '--help',
        action='help',
        default=argparse.SUPPRESS,
        help='Show this help message and exit'
    )
    parser.add_argument(
        '-i', '--intensity',
        type=int,
        default=defaults['temperature_power'],
        help='Temperature power intensity (default: %(default)s)'
    )
    parser.add_argument(
        '-c', '--cold',
        type=int,
        default=defaults['minimum_temperature'],
        help='Minimum temperature (default: %(default)s)'
    )
    parser.add_argument(
        '-w', '--warm',
        type=int,
        default=defaults['maximum_temperature'],
        help='Maximum temperature (default: %(default)s)'
    )
    parser.add_argument(
        '-s', '--slow',
        type=int,
        default=defaults['minimum_fan_speed'],
        help='Minimum fan speed (default: %(default)s)'
    )
    parser.add_argument(
        '-f', '--fast',
        type=int,
        default=defaults['maximum_fan_speed'],
        help='Maximum fan speed (default: %(default)s)'
    )
    parser.add_argument(
        '-p', '--poll-rate',
        type=int,
        default=defaults['temperature_poll_rate'],
        help='Temperature poll rate (default: %(default)s)'
    )

    # Parse arguments
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # Handle parsing errors (e.g., invalid integer input)
        usage()
        sys.exit(2)

    # Call run_service with parsed arguments
    run_service(
        temperature_poll_rate=args.poll_rate,
        minimum_fan_speed=args.slow,
        maximum_fan_speed=args.fast,
        minimum_temperature=args.cold,
        maximum_temperature=args.warm,
        temperature_power=args.intensity
    )

if __name__ == "__main__":
    fan_manager()