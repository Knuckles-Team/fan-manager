"""Smoke test: the MCP and agent server modules import and expose entrypoints."""

import importlib


def test_mcp_server_imports():
    mod = importlib.import_module("fan_manager.mcp_server")
    assert callable(mod.mcp_server)
    assert mod.__version__


def test_agent_server_imports():
    mod = importlib.import_module("fan_manager.agent_server")
    assert callable(mod.agent_server)
    assert mod.__version__


def test_versions_aligned():
    import fan_manager
    from fan_manager import agent_server, mcp_server

    assert fan_manager.__version__ == mcp_server.__version__ == agent_server.__version__
