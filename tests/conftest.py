"""Shared pytest fixtures for fan-manager.

Fan Manager shells out to ``ipmitool`` and ``sensors`` via ``subprocess.run``
(resolved through ``shutil.which``); tests must never touch real hardware, so we
patch those call sites to return canned output by default.
"""

import json
import subprocess
from unittest.mock import patch

import pytest

# Reason for any skipped hardware-dependent tests
reason = "Unit tests using mocks — no real BMC/sensors"


@pytest.fixture(autouse=True)
def mock_hardware():
    """Prevent any real IPMI/sensor calls during tests.

    ``fan_manager`` resolves the ``sensors``/``ipmitool`` binaries with
    ``shutil.which`` and runs them with ``subprocess.run([...], shell=False)``.
    We stub both so routing can be exercised with no hardware present.
    """
    fake_sensors = json.dumps(
        {
            "coretemp-isa-0000": {
                "Core 0": {"temp1_input": 55.0},
                "Core 1": {"temp2_input": 60.0},
            }
        }
    )

    def fake_which(name: str):
        # Pretend both required binaries exist at a stable, fake path.
        return f"/usr/bin/{name}"

    def fake_run(cmd, *args, **kwargs):
        argv = cmd if isinstance(cmd, (list, tuple)) else [cmd]
        executable = str(argv[0])
        stdout = fake_sensors if executable.endswith("sensors") else ""
        return subprocess.CompletedProcess(
            args=argv, returncode=0, stdout=stdout, stderr=""
        )

    with (
        patch("fan_manager.fan_manager.shutil.which", side_effect=fake_which) as which,
        patch(
            "fan_manager.fan_manager.subprocess.run", side_effect=fake_run
        ) as run,
    ):
        yield {"which": which, "run": run}
