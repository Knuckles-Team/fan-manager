#!/usr/bin/env python
"""fan-manager — manage your Dell PowerEdge fan speed.

Local CLI tool + MCP Server + A2A Agent for the agent-utilities ecosystem.
"""

import importlib
import importlib.util
import inspect
from typing import Any

__version__ = "1.5.0"

__all__: list[str] = ["__version__"]

CORE_MODULES: list[str] = [
    "fan_manager.fan_manager",
    "fan_manager.api_client",
    "fan_manager.models",
]

OPTIONAL_MODULES = {
    "fan_manager.agent_server": "agent",
    "fan_manager.mcp_server": "mcp",
}


def _expose_members(module):
    """Expose public classes and functions from a module into globals and __all__.

    A member is skipped when its name collides with a submodule of this package
    (e.g. the ``mcp_server``/``agent_server`` entrypoint functions share the name
    of their defining submodule). Re-binding those would shadow the submodule and
    break ``from fan_manager import mcp_server`` (it would yield the function
    instead of the module).
    """
    for name, obj in inspect.getmembers(module):
        if (inspect.isclass(obj) or inspect.isfunction(obj)) and not name.startswith(
            "_"
        ):
            if importlib.util.find_spec(f"{__name__}.{name}") is not None:
                continue
            globals()[name] = obj
            if name not in __all__:
                __all__.append(name)


for module_name in CORE_MODULES:
    if module_name:
        module = importlib.import_module(module_name)
        _expose_members(module)

_loaded_optional_modules: dict[str, Any] = {}


def _import_module_safely(module_name: str):
    """Try to import a module and return it, or None if not available."""
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def __getattr__(name: str) -> Any:
    """Lazily expose optional MCP/agent members and availability flags."""
    if name == "_MCP_AVAILABLE":
        return _import_module_safely("fan_manager.mcp_server") is not None
    if name == "_AGENT_AVAILABLE":
        return _import_module_safely("fan_manager.agent_server") is not None

    for module_name in OPTIONAL_MODULES:
        if module_name not in _loaded_optional_modules:
            module = _import_module_safely(module_name)
            if module is not None:
                _loaded_optional_modules[module_name] = module
                _expose_members(module)

        module = _loaded_optional_modules.get(module_name)
        if module is not None and hasattr(module, name):
            return getattr(module, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
