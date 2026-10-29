"""PIPE-CONNSPEC-R120.3: Fan Manager Pages and spec-dashboard contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / ".github/spec-dashboard.json"

pytestmark = pytest.mark.spec("PIPE-CONNSPEC-R120.3")


@pytest.fixture(autouse=True)
def mock_hardware():
    """Keep this filesystem-only contract test independent of package imports."""
    yield




def test_dashboard_reads_only_canonical_spec_status_files() -> None:
    config = json.loads(DASHBOARD.read_text(encoding="utf-8"))

    assert config == {
        "version": 1,
        "sources": [{"glob": "specs/*/status.json", "kind": "spec"}],
    }
