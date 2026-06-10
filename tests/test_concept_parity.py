"""Concept parity: every CONCEPT:FAN-* used in MCP tool docstrings must be
registered in docs/concepts.md.
"""

import os
import re

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_DIR = os.path.join(ROOT_DIR, "fan_manager", "mcp")
CONCEPTS_DOC = os.path.join(ROOT_DIR, "docs", "concepts.md")

CONCEPT_RE = re.compile(r"CONCEPT:(FAN-\d+)")


def _concepts_in(path: str) -> set[str]:
    found: set[str] = set()
    with open(path, encoding="utf-8") as f:
        found.update(CONCEPT_RE.findall(f.read()))
    return found


def _concepts_in_dir(directory: str) -> set[str]:
    found: set[str] = set()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                found |= _concepts_in(os.path.join(root, file))
    return found


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
def test_mcp_concepts_are_documented():
    """Each CONCEPT:FAN-* in the MCP tool modules is in docs/concepts.md."""
    tool_concepts = _concepts_in_dir(MCP_DIR)
    assert tool_concepts, "Expected at least one CONCEPT:FAN-* in fan_manager/mcp/"

    documented = _concepts_in(CONCEPTS_DOC)
    missing = tool_concepts - documented
    assert not missing, (
        f"These CONCEPT:FAN-* ids are used in MCP tool docstrings but are NOT "
        f"registered in docs/concepts.md: {sorted(missing)}"
    )


@pytest.mark.concept("FAN-001")
@pytest.mark.concept("FAN-002")
def test_expected_concepts_present():
    """The two core fan-manager concepts exist in the registry."""
    documented = _concepts_in(CONCEPTS_DOC)
    assert {"FAN-001", "FAN-002"} <= documented
