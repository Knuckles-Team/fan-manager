"""Verify package initialization and version metadata."""

import importlib

import pytest

PKG = "fan_manager"


def test_package_importable():
    mod = importlib.import_module(PKG)
    assert mod is not None


def test_version_exists():
    mod = importlib.import_module(PKG)
    version = getattr(mod, "__version__", None)
    if version is None:
        from importlib.metadata import version as get_version

        version = get_version("fan-manager")
    assert version is not None, "fan_manager has no __version__"


def test_version_format():
    mod = importlib.import_module(PKG)
    version = getattr(mod, "__version__", None)
    if version is None:
        from importlib.metadata import version as get_version

        version = get_version("fan-manager")
    parts = version.split(".")
    assert len(parts) >= 2, f"Version {version} should have at least major.minor"


def test_core_callables_exposed():
    """Core fan-control callables should be importable from the package."""
    mod = importlib.import_module(PKG)
    for name in ("get_temp", "set_fan", "auto_set_fan_speed", "fan_manager"):
        assert hasattr(mod, name), f"{name} not exposed on fan_manager"


@pytest.mark.parametrize("attr", ["_MCP_AVAILABLE", "_AGENT_AVAILABLE"])
def test_availability_flags(attr):
    mod = importlib.import_module(PKG)
    assert isinstance(getattr(mod, attr), bool)
