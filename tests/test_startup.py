"""Smoke test: the MCP and agent server modules import and expose entrypoints."""

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
def test_agent_server_smoke_imports():
    """Smoke: the agent server exposing CONCEPT:FM-OS.governance.service-reads-temperature-through/CONCEPT:FM-OS.governance.service-writes-fan-level tools imports."""
    mod = importlib.import_module("fan_manager.agent_server")
    assert callable(mod.agent_server)
    assert mod.__version__


@pytest.mark.concept("FM-OS.governance.service-reads-temperature-through")
@pytest.mark.concept("FM-OS.governance.service-writes-fan-level")
def test_versions_aligned():
    """Package/MCP/agent versions stay aligned across the CONCEPT:FAN-* surface."""
    import fan_manager
    from fan_manager import agent_server, mcp_server

    assert fan_manager.__version__ == mcp_server.__version__ == agent_server.__version__
