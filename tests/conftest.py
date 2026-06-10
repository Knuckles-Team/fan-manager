"""Shared pytest fixtures for fan-manager.

Fan Manager shells out to ``ipmitool`` and ``sensors``; tests must never touch
real hardware, so we patch ``os.system`` / ``os.popen`` by default.
"""

import json
from unittest.mock import patch

import pytest

# Reason for any skipped hardware-dependent tests
reason = "Unit tests using mocks — no real BMC/sensors"


@pytest.fixture(autouse=True)
def mock_hardware():
    """Prevent any real IPMI/sensor calls during tests."""
    fake_sensors = json.dumps(
        {
            "coretemp-isa-0000": {
                "Core 0": {"temp1_input": 55.0},
                "Core 1": {"temp2_input": 60.0},
            }
        }
    )

    class _FakePopen:
        def __init__(self, output):
            self._output = output

        def read(self):
            return self._output

    with (
        patch("os.system", return_value=0) as mock_system,
        patch("os.popen", return_value=_FakePopen(fake_sensors)) as mock_popen,
    ):
        yield {"system": mock_system, "popen": mock_popen}
