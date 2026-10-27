"""PIPE-CONNSPEC-R120.4: Fan Manager rapid-delivery skill contract."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "fan_manager/skills/fan-manager-development/SKILL.md"

pytestmark = pytest.mark.spec("PIPE-CONNSPEC-R120.4")


def test_development_skill_binds_fan_manager_contract_and_package_data() -> None:
    text = SKILL.read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert SKILL.is_file()
    assert re.search(r"^name:\s*fan-manager-development\s*$", frontmatter, re.M)
    assert re.search(r"^skill_type:\s*skill\s*$", frontmatter, re.M)
    assert "## Rapid delivery: the 5-minute contract" in text
    for reference in (
        "fan_manager/fan_manager.py",
        "fan_manager/api_client.py",
        "fan_manager/mcp_server.py",
        "fan_manager/mcp/mcp_temperature.py",
        "fan_manager/mcp/mcp_fan_control.py",
        "fan_manager/connector_sources.py",
        "fan_manager/kg_ingest.py",
        "FAN_MANAGER_HOST",
        "FAN_MANAGER_NODE_API_TOKEN",
        "TEMPERATURETOOL",
        "FAN_CONTROLTOOL",
        "MCP_TOOL_MODE",
        "python_pipeline.yml@main",
        "container_pipeline.yml@main",
        "render_connector: true",
        "pages_pipeline.yml@main",
        "uv run --locked --extra test pytest",
    ):
        assert reference in text

    package_data = project["tool"]["setuptools"]["package-data"]["fan_manager"]
    assert "skills/**" in package_data
    assert not re.search(r"(?:sk-|ghp_|Bearer\s+)[A-Za-z0-9_./-]{12,}", text)
    assert project["project"]["name"] == "fan-manager"
