"""Verify package initialization and version metadata."""

import importlib

import pytest

PKG = "fan_manager"


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
def test_package_importable():
    """The package exposing CONCEPT:FAN-001/CONCEPT:FAN-002 imports cleanly."""
    mod = importlib.import_module(PKG)
    assert mod is not None


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
def test_version_exists():
    """The package carries a discoverable version (CONCEPT:FAN-001/FAN-002 surface)."""
    mod = importlib.import_module(PKG)
    version = getattr(mod, "__version__", None)
    if version is None:
        from importlib.metadata import version as get_version

        version = get_version("fan-manager")
    assert version is not None, "fan_manager has no __version__"


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
def test_version_format():
    """The version is at least major.minor (CONCEPT:FAN-001/CONCEPT:FAN-002 surface)."""
    mod = importlib.import_module(PKG)
    version = getattr(mod, "__version__", None)
    if version is None:
        from importlib.metadata import version as get_version

        version = get_version("fan-manager")
    parts = version.split(".")
    assert len(parts) >= 2, f"Version {version} should have at least major.minor"


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
def test_core_callables_exposed():
    """Core CONCEPT:FAN-001/CONCEPT:FAN-002 callables are importable from the package."""
    mod = importlib.import_module(PKG)
    for name in ("get_temp", "set_fan", "auto_set_fan_speed", "fan_manager"):
        assert hasattr(mod, name), f"{name} not exposed on fan_manager"


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
@pytest.mark.parametrize("attr", ["_MCP_AVAILABLE", "_AGENT_AVAILABLE"])
def test_availability_flags(attr):
    """Optional-dependency flags gating the CONCEPT:FAN-* tool surface are booleans."""
    mod = importlib.import_module(PKG)
    assert isinstance(getattr(mod, attr), bool)
