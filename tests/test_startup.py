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




