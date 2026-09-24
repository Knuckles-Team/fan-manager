"""Smoke test: the MCP server module imports and exposes its entrypoint."""

import importlib

import pytest


@pytest.mark.concept("FM-OS.governance.service-reads-temperature-through")
@pytest.mark.concept("FM-OS.governance.service-writes-fan-level")
def test_mcp_server_smoke_imports():
    """Smoke: the MCP server (CONCEPT:FM-OS.governance.service-reads-temperature-through/CONCEPT:FM-OS.governance.service-writes-fan-level surface) imports."""
    mod = importlib.import_module("fan_manager.mcp_server")
    assert callable(mod.mcp_server)
    assert mod.__version__


@pytest.mark.concept("FM-OS.governance.service-reads-temperature-through")
@pytest.mark.concept("FM-OS.governance.service-writes-fan-level")
def test_versions_aligned():
    """Package/MCP versions stay aligned across the CONCEPT:FAN-* surface."""
    import fan_manager
    from fan_manager import mcp_server

    assert fan_manager.__version__ == mcp_server.__version__
