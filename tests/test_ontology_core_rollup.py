"""CONN-FAN-MANAGER-CONNECTOR-CONTENT-R002: every packaged ontology class reaches a core class."""

from __future__ import annotations

from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")
from rdflib.namespace import OWL, RDF, RDFS  # noqa: E402

pytestmark = pytest.mark.spec("CONN-FAN-MANAGER-CONNECTOR-CONTENT-R002")

ONTOLOGY_DIR = Path(__file__).resolve().parent.parent / "fan_manager" / "ontology"
CORE = "https://knuckles-team.github.io/ontology/core#"


@pytest.mark.parametrize(
    "path", sorted(ONTOLOGY_DIR.glob("*.ttl")), ids=lambda p: p.name
)
def test_every_class_rolls_up_to_core(path: Path) -> None:
    graph = rdflib.Graph()
    graph.parse(path)
    classes = {
        c for c in graph.subjects(RDF.type, OWL.Class) if isinstance(c, rdflib.URIRef)
    }

    def reaches_core(node: rdflib.URIRef, seen: set) -> bool:
        if str(node).startswith(CORE):
            return True
        if node in seen:
            return False
        seen.add(node)
        return any(
            isinstance(parent, rdflib.URIRef) and reaches_core(parent, seen)
            for parent in graph.objects(node, RDFS.subClassOf)
        )

    orphans = sorted(str(c) for c in classes if not reaches_core(c, set()))
    assert not orphans, f"{path.name}: classes with no path to a core class: {orphans}"
    for imported in graph.objects(None, OWL.imports):
        assert not str(imported).startswith(CORE.rstrip("#"))
