"""Smoke test: the MCP and agent server modules import and expose entrypoints."""

import importlib

import pytest


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
def test_mcp_server_smoke_imports():
    """Smoke: the MCP server (CONCEPT:FAN-001/CONCEPT:FAN-002 surface) imports."""
    mod = importlib.import_module("fan_manager.mcp_server")
    assert callable(mod.mcp_server)
    assert mod.__version__


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
def test_agent_server_smoke_imports():
    """Smoke: the agent server exposing CONCEPT:FAN-001/CONCEPT:FAN-002 tools imports."""
    mod = importlib.import_module("fan_manager.agent_server")
    assert callable(mod.agent_server)
    assert mod.__version__


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
def test_versions_aligned():
    """Package/MCP/agent versions stay aligned across the CONCEPT:FAN-* surface."""
    import fan_manager
    from fan_manager import agent_server, mcp_server

    assert fan_manager.__version__ == mcp_server.__version__ == agent_server.__version__
