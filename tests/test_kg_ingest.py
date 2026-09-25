"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``fan_manager.kg_ingest`` mappers with a fake ChangeEnvelope-capable
engine client (no engine required), asserting the applied node/edge writes + the
fan-manager telemetry → :TemperatureReading / :FanSpeedSetting / :SensorReading mapping.
The fake client and governed-session fixture mirror agent-utilities' own
``tests/knowledge_graph/test_native_ingest.py`` reference fake — the shape
``_change_envelope_authority`` actually requires (``changes``/``nodes``/``rdf``/
``supports``; the retired raw ``txn``-only fake is rejected).
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from typing import Any

import msgpack
import pytest
from agent_utilities.knowledge_graph.core.session import GraphSession, use_session
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError
from agent_utilities.security.actor_identity import ActorType
from agent_utilities.security.brain_context import ActorContext, use_actor

from fan_manager.kg_ingest import (
    ingest_entities,
    ingest_fan_settings,
    ingest_sensor_readings,
    ingest_temperature_readings,
    parse_sensor_list,
)


@pytest.fixture(autouse=True)
def _governed_session():
    """Ambient actor + GraphSession required by native_ingest's injected-client path."""
    actor = ActorContext(
        actor_id="subject:opaque:synthetic",
        actor_type=ActorType.AUTOMATED_SERVICE,
        roles=(),
        tenant_id="tenant:opaque:synthetic",
        authenticated=True,
    )
    session = GraphSession(
        actor=actor,
        tenant=actor.tenant_id,
        scopes=frozenset({"kg:write"}),
        graph="__commons__",
        policy_version="policy:opaque:synthetic",
        audience="epistemic-graph",
    )
    with use_actor(actor), use_session(session):
        yield


class _FakeNodes:
    def __init__(self) -> None:
        self.values: dict[str, dict[str, Any]] = {}

    def properties(self, node_id: str) -> dict[str, Any] | None:
        return self.values.get(node_id)

    def list(self) -> list[tuple[str, dict[str, Any]]]:
        return list(self.values.items())


class _FakeChanges:
    def __init__(self, nodes: _FakeNodes) -> None:
        self.nodes = nodes
        self.edges: list[tuple[str, str, dict[str, Any]]] = []
        self.applied: list[dict[str, Any]] = []
        self.records: dict[str, dict[str, Any]] = {}
        self.versions: dict[str, dict[str, Any]] = {}

    def get(self, envelope_id: str) -> dict[str, Any] | None:
        return self.records.get(envelope_id)

    def content_version(self, object_id: str) -> dict[str, Any] | None:
        return self.versions.get(object_id)

    def cursor(self, _source: str, _partition: str = "") -> None:
        return None

    def apply(self, envelope: dict[str, Any]) -> dict[str, Any]:
        self.applied.append(envelope)
        mutation = envelope["mutation"]
        for operation in mutation["operations"]:
            method = operation["method"]
            params = method["params"]
            properties = msgpack.unpackb(params["properties_msgpack"], raw=False)
            if method["method"] == "AddNode":
                self.nodes.values[params["node_id"]] = properties
            elif method["method"] == "AddEdge":
                self.edges.append(
                    (params["source_id"], params["target_id"], properties)
                )
        version = envelope["content_version"]
        self.versions[version["object_id"]] = version
        self.records[envelope["envelope_id"]] = envelope
        return {
            "batch_id": mutation["batch_id"],
            "replayed": False,
            "projection_pending": False,
        }


class _FakeRdf:
    def validate_shacl(self, _shapes: str, _data_graph: str) -> dict[str, Any]:
        return {"conforms": True, "results": []}


class _FakeClient:
    def __init__(self) -> None:
        self.nodes = _FakeNodes()
        self.changes = _FakeChanges(self.nodes)
        self.rdf = _FakeRdf()

    @staticmethod
    def supports(operation: str) -> bool:
        return operation == "ApplyChangeEnvelope"

    @staticmethod
    def shacl_validate_committed(_data_graph: str) -> Any:
        """EG's committed-GraphSchema SHACL authority (agent-utilities EH-385)."""
        from epistemic_graph.generated.rdf_report import ShaclValidationReport

        digest = "sha256:" + "0" * 64
        return ShaclValidationReport(
            conforms=True, results=[], composed_digest=digest, schema_digests=[digest]
        )


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "a", "node_type": "ManagedHost", "name": "h"},
            {"id": "b", "node_type": "FanController"},
        ],
        [{"source": "b", "target": "a", "relationship": "controlsHost"}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(c.changes.applied) == 1
    assert set(c.nodes.values) == {"a", "b"}
    # provenance is stamped
    assert c.nodes.values["a"]["source"] == "fan-manager"
    assert c.nodes.values["a"]["domain"] == "fan"
    assert c.changes.edges == [("b", "a", {"relationship": "controlsHost"})]


def test_ingest_temperature_readings_maps_reading_host_and_setting():
    c = _FakeClient()
    res = ingest_temperature_readings(
        [
            {
                "response": 63.0,
                "command": "sensors -j",
                "status": 200,
                "fan_level": 42,
                "observed_at": "2026-07-04T00:00:00Z",
            }
        ],
        host="r820",
        client=c,
        graph="__commons__",
    )
    # host + controller + reading + setting = 4 nodes
    assert res == {"nodes": 4, "edges": 4}
    rid = "fan:tempreading:r820:2026-07-04T00:00:00Z"
    sid = "fan:setting:r820:2026-07-04T00:00:00Z"
    assert c.nodes.values[rid]["node_type"] == "TemperatureReading"
    assert c.nodes.values[rid]["celsius"] == 63.0
    assert c.nodes.values[rid]["observedAt"] == "2026-07-04T00:00:00Z"
    assert c.nodes.values[sid]["node_type"] == "FanSpeedSetting"
    assert c.nodes.values[sid]["fanLevel"] == 42
    assert c.nodes.values["fan:host:r820"]["node_type"] == "ManagedHost"
    assert c.nodes.values["fan:controller:r820"]["node_type"] == "FanController"
    # links: controlsHost, readingForHost, appliedToHost, triggeredSetting
    kinds = {e[2]["relationship"] for e in c.changes.edges}
    assert kinds == {
        "controlsHost",
        "readingForHost",
        "appliedToHost",
        "triggeredSetting",
    }


def test_ingest_temperature_reading_without_fan_level_omits_setting():
    c = _FakeClient()
    res = ingest_temperature_readings(
        [{"response": 50.0, "status": 200, "observed_at": "2026-07-04T01:00:00Z"}],
        host="localhost",
        client=c,
        graph="__commons__",
    )
    # host + controller + reading = 3 nodes, no setting
    assert res == {"nodes": 3, "edges": 2}
    assert not any(
        n.get("node_type") == "FanSpeedSetting" for n in c.nodes.values.values()
    )


def test_ingest_fan_settings_maps_setting():
    c = _FakeClient()
    res = ingest_fan_settings(
        [
            {
                "fan_level": 80,
                "command": "ipmitool raw 0x30 0x30 0x02 0xff 0x50",
                "observed_at": "2026-07-04T02:00:00Z",
            }
        ],
        host="r710",
        client=c,
        graph="__commons__",
    )
    # host + controller + setting = 3 nodes
    assert res == {"nodes": 3, "edges": 2}
    sid = "fan:setting:r710:2026-07-04T02:00:00Z"
    assert c.nodes.values[sid]["node_type"] == "FanSpeedSetting"
    assert c.nodes.values[sid]["fanLevel"] == 80


def test_ingest_sensor_readings_classifies_fan_and_temp():
    c = _FakeClient()
    sensors = parse_sensor_list(
        "Fan1 RPM | 5000.000 | RPM | ok |\n"
        "Inlet Temp | 24.000 | degrees C | ok |\n"
        "bad line without pipes\n"
    )
    assert len(sensors) == 2
    res = ingest_sensor_readings(sensors, host="r820", client=c, graph="__commons__")
    # host + controller + 2 sensors = 4 nodes; controlsHost + 2 readingForHost = 3 edges
    assert res == {"nodes": 4, "edges": 3}
    fan_nodes = [n for n in c.nodes.values.values() if n.get("sensorType") == "Fan"]
    temp_nodes = [
        n for n in c.nodes.values.values() if n.get("sensorType") == "Temperature"
    ]
    assert fan_nodes and fan_nodes[0]["fanRpm"] == 5000.0
    assert temp_nodes and temp_nodes[0]["celsius"] == 24.0


def test_parse_sensor_list_handles_na_values():
    rows = parse_sensor_list("Voltage 1 | na | Volts | ns |")
    assert rows == [
        {"name": "Voltage 1", "value": None, "unit": "Volts", "status": "ns"}
    ]


def test_ingest_rejects_legacy_structural_fields():
    with pytest.raises(NativeIngestError, match="canonical node_type"):
        ingest_entities([{"id": "legacy", "type": "Legacy"}], client=_FakeClient())


def test_ingest_empty_is_rejected():
    with pytest.raises(NativeIngestError, match="at least one entity"):
        ingest_entities([], client=_FakeClient())
    for ingestor in (
        ingest_temperature_readings,
        ingest_fan_settings,
        ingest_sensor_readings,
    ):
        with pytest.raises(NativeIngestError, match="at least one entity"):
            ingestor([], client=_FakeClient())
