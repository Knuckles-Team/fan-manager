"""Tests for the IPMI/BMC wrapper (CONCEPT:FAN-003..FAN-008).

DI seam: a fake CommandRunner records the argv and returns canned output, so the
argv construction, out-of-band lanplus, password redaction, and validation are
exercised without any hardware.
"""

from __future__ import annotations

import pytest

from fan_manager import ipmi


class _FakeRunner:
    def __init__(self, out: str = "ok", have_bin: bool = True):
        self.out = out
        self.have_bin = have_bin
        self.last_argv: list[str] | None = None

    def which(self, name: str):
        return f"/usr/bin/{name}" if self.have_bin else None

    def run(self, argv: list[str], *, check: bool = True) -> str:
        self.last_argv = argv
        return self.out


def test_power_status_inband():
    r = _FakeRunner(out="System Power : on")
    res = ipmi.power("status", runner=r)
    assert res["status"] == 200
    assert r.last_argv[1:] == [
        "chassis",
        "power",
        "status",
    ]  # in-band: no lanplus prefix
    assert "on" in res["response"]


def test_power_invalid_action_400():
    res = ipmi.power("nuke", runner=_FakeRunner())
    assert res["status"] == 400 and "Unknown action" in res["error"]


def test_out_of_band_lanplus_and_password_redaction():
    r = _FakeRunner(out="System Power : on")
    res = ipmi.power(
        "status",
        target={"host": "10.0.0.113", "user": "root", "password": "s3cret"},
        runner=r,
    )
    assert res["status"] == 200
    # argv carries the lanplus target...
    assert "-I" in r.last_argv and "lanplus" in r.last_argv
    assert "10.0.0.113" in r.last_argv and "s3cret" in r.last_argv
    # ...but the returned command string masks the password.
    assert "s3cret" not in res["command"] and "***" in res["command"]


def test_bin_missing_500():
    res = ipmi.power("status", runner=_FakeRunner(have_bin=False))
    assert res["status"] == 500 and "ipmitool" in res["error"]


def test_sensors_type_requires_sensor_type():
    assert ipmi.sensors("type", runner=_FakeRunner())["status"] == 400
    r = _FakeRunner()
    ipmi.sensors("type", sensor_type="Drive Slot", runner=r)
    assert r.last_argv[-2:] == ["type", "Drive Slot"]


def test_sel_list():
    r = _FakeRunner(out="1 | Drive Slot | Asserted")
    res = ipmi.sel("list", runner=r)
    assert res["status"] == 200 and r.last_argv[-2:] == ["sel", "list"]


def test_sol_info_and_deactivate():
    r = _FakeRunner()
    assert ipmi.sol("info", runner=r)["status"] == 200
    assert r.last_argv[-3:] == ["sol", "info", "1"]
    ipmi.sol("deactivate", runner=r)
    assert r.last_argv[-2:] == ["sol", "deactivate"]
    assert ipmi.sol("bogus", runner=r)["status"] == 400


def test_lan_set_requires_param_value_and_user_pw_redacted():
    assert ipmi.lan("set", runner=_FakeRunner())["status"] == 400  # no param/value
    r = _FakeRunner()
    ipmi.lan("set", param="access", value="on", runner=r)
    assert r.last_argv[-4:] == ["lan", "set", "1", "access"] or "access" in r.last_argv
    # user set_password masks the literal password in the returned command
    res = ipmi.user("set_password", user_id="2", password="topsecret", runner=r)
    assert (
        res["status"] == 200
        and "topsecret" not in res["command"]
        and "***" in res["command"]
    )


def test_user_requires_id():
    assert ipmi.user("enable", runner=_FakeRunner())["status"] == 400


def test_mc_and_raw():
    r = _FakeRunner(out="Firmware Revision : 2.52")
    assert ipmi.mc("info", runner=r)["status"] == 200
    ipmi.mc("reset_cold", runner=r)
    assert r.last_argv[-2:] == ["reset", "cold"]
    assert ipmi.raw("", runner=r)["status"] == 400
    ipmi.raw("0x30 0x30 0x01 0x00", runner=r)
    assert r.last_argv[-4:] == ["0x30", "0x30", "0x01", "0x00"]


@pytest.mark.parametrize(
    "fn,act",
    [
        (ipmi.power, "status"),
        (ipmi.chassis, "status"),
        (ipmi.sel, "list"),
        (ipmi.mc, "info"),
    ],
)
def test_envelope_shape(fn, act):
    res = fn(act, runner=_FakeRunner())
    assert set(["response", "command", "status"]).issubset(res)
