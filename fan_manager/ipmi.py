"""Full IPMI/BMC wrapper over the ``ipmitool`` binary (CONCEPT:FAN-003..FAN-008).

Extends fan-manager beyond fan/temperature into a general Dell-iDRAC / IPMI 2.0
control surface: power, chassis, sensors, system event log, Serial-over-LAN,
BMC LAN/user configuration, ``mc`` and raw commands. Works **in-band** (the host's
own ``/dev/ipmi0``, no creds) and **out-of-band** over LAN (``-I lanplus -H -U -P``).

Every function uses the injected :class:`CommandRunner` seam (fixed argv, no shell,
no user string ever reaches a command line) and returns the package-standard
``{"response", "command", "status", "error"?}`` dict. The ``command`` string is
returned with the ``-P <password>`` redacted.
"""

from __future__ import annotations

import logging
from typing import Any

from fan_manager.fan_manager import CommandRunner, SubprocessCommandRunner

_DEFAULT_RUNNER: CommandRunner = SubprocessCommandRunner()
_log = logging.getLogger("FanManager.ipmi")

# A "target" is an optional dict {host, user, password}. host present => out-of-band.
Target = dict[str, Any] | None


def _base_argv(runner: CommandRunner, target: Target) -> list[str]:
    ipmitool = runner.which("ipmitool")
    if ipmitool is None:
        raise RuntimeError("'ipmitool' executable not found on PATH")
    argv = [ipmitool]
    if target and target.get("host"):
        argv += [
            "-I",
            "lanplus",
            "-H",
            str(target["host"]),
            "-U",
            str(target.get("user", "root")),
            "-P",
            str(target.get("password", "")),
        ]
    return argv


def _redact(argv: list[str]) -> str:
    """Render argv as a string with the value after ``-P`` masked."""
    parts = []
    for i, a in enumerate(argv):
        parts.append("***" if i > 0 and argv[i - 1] == "-P" else a)
    return " ".join(parts)


def _exec(
    runner: CommandRunner | None, target: Target, args: list[str], *, check: bool = True
) -> dict[str, Any]:
    runner = runner or _DEFAULT_RUNNER
    try:
        argv = _base_argv(runner, target) + args
        cmd = _redact(argv)
        out = runner.run(argv, check=check)
        _log.info("ipmi ok: %s", cmd)
        return {"response": out.strip(), "command": cmd, "status": 200}
    except Exception as e:  # noqa: BLE001 — surface as a typed result, never raise
        _log.error("ipmi failed: %s", e)
        return {
            "response": None,
            "command": " ".join(args),
            "status": 500,
            "error": str(e),
        }


def _invalid(action: str, valid: set[str]) -> dict[str, Any]:
    return {
        "response": None,
        "command": action,
        "status": 400,
        "error": f"Unknown action '{action}'. Must be one of: {sorted(valid)}",
    }


# --- CONCEPT:FAN-003 — power + chassis -------------------------------------
def power(
    action: str, target: Target = None, runner: CommandRunner | None = None
) -> dict[str, Any]:
    """Chassis power control: status | on | off | cycle | reset | soft."""
    valid = {"status", "on", "off", "cycle", "reset", "soft"}
    if action not in valid:
        return _invalid(action, valid)
    return _exec(runner, target, ["chassis", "power", action])


def chassis(
    action: str,
    target: Target = None,
    bootdev: str | None = None,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Chassis info/control: status | identify | bootdev | restart_cause | poh."""
    valid = {"status", "identify", "bootdev", "restart_cause", "poh"}
    if action not in valid:
        return _invalid(action, valid)
    if action == "identify":
        return _exec(runner, target, ["chassis", "identify", "15"])  # blink 15s
    if action == "bootdev":
        if not bootdev:
            return {
                "response": None,
                "command": "chassis bootdev",
                "status": 400,
                "error": "bootdev required (pxe|disk|cdrom|bios)",
            }
        return _exec(runner, target, ["chassis", "bootdev", bootdev])
    if action == "restart_cause":
        return _exec(runner, target, ["chassis", "restart_cause"])
    if action == "poh":
        return _exec(runner, target, ["chassis", "poh"])
    return _exec(runner, target, ["chassis", "status"])


# --- CONCEPT:FAN-004 — sensors --------------------------------------------
def sensors(
    action: str = "list",
    target: Target = None,
    sensor_type: str | None = None,
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """Sensor readings: list (sdr list) | full (sensor list) | type (sdr type <T>)."""
    valid = {"list", "full", "type"}
    if action not in valid:
        return _invalid(action, valid)
    if action == "type":
        if not sensor_type:
            return {
                "response": None,
                "command": "sdr type",
                "status": 400,
                "error": "sensor_type required (e.g. 'Temperature', 'Fan', 'Drive Slot')",
            }
        return _exec(runner, target, ["sdr", "type", sensor_type])
    if action == "full":
        return _exec(runner, target, ["sensor", "list"])
    return _exec(runner, target, ["sdr", "list"])


# --- CONCEPT:FAN-005 — system event log -----------------------------------
def sel(
    action: str = "list", target: Target = None, runner: CommandRunner | None = None
) -> dict[str, Any]:
    """System Event Log: list | elist | info | clear."""
    valid = {"list", "elist", "info", "clear"}
    if action not in valid:
        return _invalid(action, valid)
    return _exec(runner, target, ["sel", action])


# --- CONCEPT:FAN-006 — Serial-over-LAN -------------------------------------
def sol(
    action: str = "info", target: Target = None, runner: CommandRunner | None = None
) -> dict[str, Any]:
    """Serial-over-LAN: info | deactivate. (interactive 'activate' is not exposed
    via MCP — use the printed `ipmitool ... sol activate` recipe for a live console)."""
    valid = {"info", "deactivate"}
    if action not in valid:
        return _invalid(action, valid)
    arg = ["sol", "info", "1"] if action == "info" else ["sol", "deactivate"]
    return _exec(runner, target, arg)


# --- CONCEPT:FAN-007 — BMC config (LAN / user / mc) ------------------------
def lan(
    action: str = "print",
    target: Target = None,
    param: str | None = None,
    value: str | None = None,
    channel: str = "1",
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """BMC LAN: print | set (param+value, e.g. ipaddr/netmask/defgw/access)."""
    valid = {"print", "set"}
    if action not in valid:
        return _invalid(action, valid)
    if action == "set":
        if not param or value is None:
            return {
                "response": None,
                "command": "lan set",
                "status": 400,
                "error": "param and value required (e.g. param='access' value='on')",
            }
        return _exec(runner, target, ["lan", "set", channel, param, value])
    return _exec(runner, target, ["lan", "print", channel])


def user(
    action: str = "list",
    target: Target = None,
    user_id: str | None = None,
    password: str | None = None,
    channel: str = "1",
    runner: CommandRunner | None = None,
) -> dict[str, Any]:
    """BMC users: list | set_password | enable | disable. (user_id required for the
    last three; set_password takes `password`)."""
    valid = {"list", "set_password", "enable", "disable"}
    if action not in valid:
        return _invalid(action, valid)
    if action == "list":
        return _exec(runner, target, ["user", "list", channel])
    if not user_id:
        return {
            "response": None,
            "command": f"user {action}",
            "status": 400,
            "error": "user_id required",
        }
    if action == "set_password":
        if not password:
            return {
                "response": None,
                "command": "user set password",
                "status": 400,
                "error": "password required",
            }
        # password is masked in the returned command string by _exec only for -P;
        # build the command but redact the literal pw in the returned 'command'.
        res = _exec(runner, target, ["user", "set", "password", user_id, password])
        res["command"] = f"user set password {user_id} ***"
        return res
    return _exec(runner, target, ["user", action, user_id])


def mc(
    action: str = "info", target: Target = None, runner: CommandRunner | None = None
) -> dict[str, Any]:
    """Management controller: info | reset_cold | reset_warm | selftest."""
    valid = {"info", "reset_cold", "reset_warm", "selftest"}
    if action not in valid:
        return _invalid(action, valid)
    if action == "reset_cold":
        return _exec(runner, target, ["mc", "reset", "cold"])
    if action == "reset_warm":
        return _exec(runner, target, ["mc", "reset", "warm"])
    if action == "selftest":
        return _exec(runner, target, ["mc", "selftest"])
    return _exec(runner, target, ["mc", "info"])


# --- CONCEPT:FAN-008 — raw -------------------------------------------------
def raw(
    data: str, target: Target = None, runner: CommandRunner | None = None
) -> dict[str, Any]:
    """Send a raw IPMI command, e.g. data='0x30 0x30 0x01 0x00'."""
    tokens = [t for t in str(data).split() if t]
    if not tokens:
        return {
            "response": None,
            "command": "raw",
            "status": 400,
            "error": "data required",
        }
    return _exec(runner, target, ["raw", *tokens])
