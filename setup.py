#!/usr/bin/env python
# coding: utf-8

from setuptools import setup
from fan_manager.version import __version__, __author__
from pathlib import Path
import os
import re
from pip._internal.network.session import PipSession
from pip._internal.req import parse_requirements

readme = Path("README.md").read_text()
version = __version__
requirements = parse_requirements(
    os.path.join(os.path.dirname(__file__), "requirements.txt"), session=PipSession()
)
readme = re.sub(r"Version: [0-9]*\.[0-9]*\.[0-9][0-9]*", f"Version: {version}", readme)
with open("README.md", "w") as readme_file:
    readme_file.write(readme)
description = "Manager your Dell PowerEdge Fan Speed with this handy tool!"

setup(
    name="fan-manager",
    version=f"{version}",
    description=description,
    long_description=f"{readme}",
    long_description_content_type="text/markdown",
    url="https://github.com/Knuckles-Team/fan-manager",
    author=__author__,
    author_email="knucklessg1@gmail.com",
    license="MIT",
    packages=["fan_manager"],
    include_package_data=True,
    install_requires=[str(requirement.requirement) for requirement in requirements],
    py_modules=["fan_manager"],
    package_data={"fan_manager": ["fan_manager"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: Public Domain",
        "Environment :: Console",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={"console_scripts": ["fan-manager = fan_manager.fan_manager:main"]},
)
