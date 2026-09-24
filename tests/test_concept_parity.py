"""Concept parity: every OKF-CIS CONCEPT:<SLUG>-<PILLAR>.<domain>.<concept> id used
in MCP tool docstrings must be registered in docs/concepts.md.
"""

import os

import pytest

# The OKF-CIS marker grammar moved off agent-utilities onto repository-manager's
# governance module (lane au-decon-G13, unlanded at the time of this migration).
# repository-manager is not yet a resolvable dependency here (its own worktree lacks
# the .uv-workspace-siblings scaffolding this lane must not create in a worktree it
# doesn't own -- see NEW-LANE-BRIEF's HARD RULE); skip gracefully until it lands.
repository_manager_governance = pytest.importorskip(
    "repository_manager.governance.concept_hierarchy",
    reason="repository-manager (OKF_MARKER_RE's new home, lane au-decon-G13) not installed yet",
)
OKF_MARKER_RE = repository_manager_governance.OKF_MARKER_RE

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_DIR = os.path.join(ROOT_DIR, "fan_manager", "mcp")
CONCEPTS_DOC = os.path.join(ROOT_DIR, "docs", "concepts.md")

# Reuse the one canonical marker grammar (the OKF-CIS standard, owned by
# repository-manager's governance module since it moved off agent-utilities) rather
# than a locally-maintained copy, so this test can't drift from the ecosystem-wide
# concept-ID format.
CONCEPT_RE = OKF_MARKER_RE


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


# This package's own OKF-CIS slug — concepts under this slug are locally owned and
# must be registered in the "Project-Specific Concepts" table (CONCEPT:-prefixed).
# A different slug (e.g. AU-*) is a cross-project concept owned by that repo's own
# registry; docs/concepts.md bridges it as a *bare* id (no CONCEPT: prefix, by
# design — see the "Cross-Project References" section) so it deliberately isn't
# picked up by CONCEPT_RE, and only needs to appear in the doc at all.
LOCAL_SLUG = "FM-"


def test_mcp_concepts_are_documented():
    """Each CONCEPT:<id> in the MCP tool modules is documented in docs/concepts.md —
    locally registered (CONCEPT:-prefixed) if FM-owned, bridged (bare id) if not."""
    tool_concepts = _concepts_in_dir(MCP_DIR)
    assert tool_concepts, "Expected at least one CONCEPT:<id> in fan_manager/mcp/"

    with open(CONCEPTS_DOC, encoding="utf-8") as f:
        doc_text = f.read()
    locally_documented = _concepts_in(CONCEPTS_DOC)

    missing = set()
    for concept in tool_concepts:
        if concept.startswith(LOCAL_SLUG):
            if concept not in locally_documented:
                missing.add(concept)
        elif concept not in doc_text:  # external — bridged as a bare id
            missing.add(concept)
    assert not missing, (
        f"These CONCEPT:<id> ids are used in MCP tool docstrings but are NOT "
        f"documented in docs/concepts.md: {sorted(missing)}"
    )


@pytest.mark.concept("FM-OS.governance.service-reads-temperature-through")
@pytest.mark.concept("FM-OS.governance.service-writes-fan-level")
def test_expected_concepts_present():
    """The two core fan-manager concepts exist in the registry."""
    documented = _concepts_in(CONCEPTS_DOC)
    assert {"FM-OS.governance.service-reads-temperature-through", "FM-OS.governance.service-writes-fan-level"} <= documented
