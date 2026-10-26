"""Typed IPMI/BMC operations served as one MCP tool each.

Each method wraps one :mod:`fan_manager.ipmi` call. Reads may use an optional
out-of-band target ``host``/``user``/``password``; writes require all three
fields and credentials are resolved by the runtime and never persisted in
connector records.
"""

from typing import Any

from fan_manager import fleet, ipmi
from fan_manager.kg_ingest import parse_sensor_list


def _target(host: str | None, user: str, password: str | None) -> dict[str, Any] | None:
    if not host:
        return None
    return {"host": host, "user": user, "password": password or ""}


def _write_guard(
    host: str | None, user: str, password: str | None
) -> dict[str, Any] | None:
    """Refuse an IPMI write unless its out-of-band target is fully explicit."""
    if host and user and password:
        return None
    return {
        "response": None,
        "command": "write",
        "status": 400,
        "error": "write requires an explicit out-of-band host, user, and BMC password",
    }


class IpmiApi:
    """The BMC operations of a Dell PowerEdge server, over ``ipmitool``."""

    def power_status(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Read the chassis power state."""
        if host is None and fleet.enabled():
            return fleet.read_all("power_status")
        return ipmi.power("status", target=_target(host, user, password))

    def power_on(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Power the chassis on."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.power("on", target=_target(host, user, password))

    def power_off(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Power the chassis off (destructive: confirm the target first)."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.power("off", target=_target(host, user, password))

    def power_cycle(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Power-cycle the chassis (destructive: confirm the target first)."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.power("cycle", target=_target(host, user, password))

    def power_reset(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Hard-reset the chassis (destructive: confirm the target first)."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.power("reset", target=_target(host, user, password))

    def power_soft(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Request an ACPI soft shutdown."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.power("soft", target=_target(host, user, password))

    def chassis_identify(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Blink the chassis identify LED for 15 seconds."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.chassis("identify", target=_target(host, user, password))

    def chassis_set_boot_device(
        self,
        bootdev: str,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Set the next boot device (pxe, disk, cdrom or bios)."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.chassis(
            "bootdev", target=_target(host, user, password), bootdev=bootdev
        )

    def sensors_list(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """List the BMC sensor data records (SDR)."""
        if host is None and fleet.enabled():
            return fleet.read_all("sensors_list")
        return ipmi.sensors("list", target=_target(host, user, password))

    def sensors_full(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """List every BMC sensor with readings and thresholds."""
        if host is None and fleet.enabled():
            return fleet.read_all("sensors_full")
        return ipmi.sensors("full", target=_target(host, user, password))

    def sensors_by_type(
        self,
        sensor_type: str,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """List BMC sensors of one type, such as Temperature, Fan or Drive Slot."""
        return ipmi.sensors(
            "type", target=_target(host, user, password), sensor_type=sensor_type
        )

    def sensors_records(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Read every BMC sensor as structured records."""
        if host is None and fleet.enabled():
            return fleet.read_all("sensors_records")
        response = ipmi.sensors("full", target=_target(host, user, password))
        if not isinstance(response, dict) or response.get("status") != 200:
            return {"records": [], "status": "source-unavailable"}
        return {"records": parse_sensor_list(str(response.get("response") or ""))}

    def sel_list(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """List the system event log."""
        if host is None and fleet.enabled():
            return fleet.read_all("sel_list")
        return ipmi.sel("list", target=_target(host, user, password))

    def sel_elist(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """List the system event log with sensor names."""
        if host is None and fleet.enabled():
            return fleet.read_all("sel_elist")
        return ipmi.sel("elist", target=_target(host, user, password))

    def sel_info(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Read system event log capacity and state."""
        if host is None and fleet.enabled():
            return fleet.read_all("sel_info")
        return ipmi.sel("info", target=_target(host, user, password))

    def sel_clear(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Clear the system event log (destructive)."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.sel("clear", target=_target(host, user, password))

    def sol_info(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Read Serial-over-LAN configuration."""
        if host is None and fleet.enabled():
            return fleet.read_all("sol_info")
        return ipmi.sol("info", target=_target(host, user, password))

    def sol_deactivate(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Deactivate an open Serial-over-LAN session."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.sol("deactivate", target=_target(host, user, password))

    def lan_print(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Print the BMC LAN channel configuration."""
        if host is None and fleet.enabled():
            return fleet.read_all("lan_print")
        return ipmi.lan("print", target=_target(host, user, password))

    def lan_set(
        self,
        param: str,
        value: str,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Set one BMC LAN parameter, such as ipaddr."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.lan(
            "set", target=_target(host, user, password), param=param, value=value
        )

    def user_list(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """List BMC users."""
        if host is None and fleet.enabled():
            return fleet.read_all("user_list")
        return ipmi.user("list", target=_target(host, user, password))

    def user_set_password(
        self,
        user_id: str,
        new_password: str,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Set a BMC user's password."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.user(
            "set_password",
            target=_target(host, user, password),
            user_id=user_id,
            password=new_password,
        )

    def user_enable(
        self,
        user_id: str,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Enable a BMC user."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.user(
            "enable", target=_target(host, user, password), user_id=user_id
        )

    def user_disable(
        self,
        user_id: str,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Disable a BMC user."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.user(
            "disable", target=_target(host, user, password), user_id=user_id
        )

    def mc_info(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Read management-controller firmware information."""
        if host is None and fleet.enabled():
            return fleet.read_all("mc_info")
        return ipmi.mc("info", target=_target(host, user, password))

    def mc_reset_cold(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Cold-reset the management controller (destructive)."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.mc("reset_cold", target=_target(host, user, password))

    def mc_reset_warm(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Warm-reset the management controller (destructive)."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.mc("reset_warm", target=_target(host, user, password))

    def mc_selftest(
        self,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Run the management-controller self-test."""
        if host is None and fleet.enabled():
            return fleet.read_all("mc_selftest")
        return ipmi.mc("selftest", target=_target(host, user, password))

    def send_raw(
        self,
        data: str,
        host: str | None = None,
        user: str = "root",
        password: str | None = None,
    ) -> dict[str, Any]:
        """Send a raw IPMI command given as space-separated hex bytes (advanced, vendor-specific)."""
        if refusal := _write_guard(host, user, password):
            return refusal
        return ipmi.raw(data, target=_target(host, user, password))
