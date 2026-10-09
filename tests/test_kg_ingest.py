"""Epistemic-graph typed-node ingestion via agent_connector_sdk — Wire-First coverage.

Exercises the real ``fan_manager.kg_ingest`` mappers against a fake transport one level
below the SDK's own ``KnowledgeIngest`` facade, so these tests still run the SDK's real
request-building/validation contract. Asserts the fan-manager telemetry →
:TemperatureReading / :FanSpeedSetting / :SensorReading mapping and node/edge counts.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from agent_connector_sdk.ingest import IngestError, KnowledgeIngest

from fan_manager.kg_ingest import (
    ingest_entities,
    ingest_fan_settings,
    ingest_sensor_readings,
    ingest_temperature_readings,
    parse_sensor_list,
)


class _FakeTransport:
    def __init__(self) -> None:
        self.requests: list[Any] = []

    async def source_status(self, connector, stream):
        return SimpleNamespace(accepted_checkpoint=None)

    async def submit(self, request):
        self.requests.append(request)
        return SimpleNamespace(
            affected_count=len(request.records),
            relationship_count=len(request.relationships),
        )

    async def store_blob(self, data):
        raise AssertionError("fan-manager ingestion carries no media")


@pytest.fixture
def ingest():
    transport = _FakeTransport()
    return KnowledgeIngest(transport, loop=None), transport


def _node_type(record: Any) -> str:
    """The real generated ``SourceRecord`` carries no bare ``node_type`` field — it's
    encoded as the last segment of ``mapping_reference``
    (``manifest:<connector>#schema_mappings/<NodeType>``)."""
    return record.mapping_reference.rsplit("/", 1)[-1]


def _rel_name(relationship: Any) -> str:
    """Likewise, a ``SourceRelationship``'s kind is the last segment of
    ``relation_reference`` (``manifest:<connector>#resources/<NodeType>/relations/<kind>``)."""
    return relationship.relation_reference.rsplit("/", 1)[-1]


async def test_ingest_entities_writes_nodes_and_edges(ingest):
    service, transport = ingest
    res = await ingest_entities(
        [
            {"id": "a", "node_type": "ManagedHost", "name": "h"},
            {"id": "b", "node_type": "FanController"},
        ],
        [{"source": "b", "target": "a", "relationship": "controlsHost"}],
        ingest=service,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(transport.requests) == 1
    record_ids = {r.record_id for r in transport.requests[0].records}
    assert record_ids == {"a", "b"}
    rel = transport.requests[0].relationships[0]
    assert (rel.source.record_id, rel.target.record_id, _rel_name(rel)) == (
        "b",
        "a",
        "controlsHost",
    )


async def test_ingest_temperature_readings_maps_reading_host_and_setting(ingest):
    service, transport = ingest
    res = await ingest_temperature_readings(
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
        ingest=service,
    )
    # host + controller + reading + setting = 4 nodes
    assert res == {"nodes": 4, "edges": 4}
    records = {r.record_id: r for r in transport.requests[0].records}
    rid = "fan:tempreading:r820:2026-07-04T00:00:00Z"
    sid = "fan:setting:r820:2026-07-04T00:00:00Z"
    assert _node_type(records[rid]) == "TemperatureReading"
    assert records[rid].payload["celsius"] == 63.0
    assert records[rid].payload["observedAt"] == "2026-07-04T00:00:00Z"
    assert _node_type(records[sid]) == "FanSpeedSetting"
    assert records[sid].payload["fanLevel"] == 42
    assert _node_type(records["fan:host:r820"]) == "ManagedHost"
    assert _node_type(records["fan:controller:r820"]) == "FanController"
    kinds = {_rel_name(r) for r in transport.requests[0].relationships}
    assert kinds == {
        "controlsHost",
        "readingForHost",
        "appliedToHost",
        "triggeredSetting",
    }


async def test_ingest_temperature_reading_without_fan_level_omits_setting(ingest):
    service, transport = ingest
    res = await ingest_temperature_readings(
        [{"response": 50.0, "status": 200, "observed_at": "2026-07-04T01:00:00Z"}],
        host="localhost",
        ingest=service,
    )
    # host + controller + reading = 3 nodes, no setting
    assert res == {"nodes": 3, "edges": 2}
    assert not any(
        _node_type(r) == "FanSpeedSetting" for r in transport.requests[0].records
    )


async def test_ingest_fan_settings_maps_setting(ingest):
    service, transport = ingest
    res = await ingest_fan_settings(
        [
            {
                "fan_level": 80,
                "command": "ipmitool raw 0x30 0x30 0x02 0xff 0x50",
                "observed_at": "2026-07-04T02:00:00Z",
            }
        ],
        host="r710",
        ingest=service,
    )
    # host + controller + setting = 3 nodes
    assert res == {"nodes": 3, "edges": 2}
    records = {r.record_id: r for r in transport.requests[0].records}
    sid = "fan:setting:r710:2026-07-04T02:00:00Z"
    assert _node_type(records[sid]) == "FanSpeedSetting"
    assert records[sid].payload["fanLevel"] == 80


async def test_ingest_sensor_readings_classifies_fan_and_temp(ingest):
    service, transport = ingest
    sensors = parse_sensor_list(
        "Fan1 RPM | 5000.000 | RPM | ok |\n"
        "Inlet Temp | 24.000 | degrees C | ok |\n"
        "bad line without pipes\n"
    )
    assert len(sensors) == 2
    res = await ingest_sensor_readings(sensors, host="r820", ingest=service)
    # host + controller + 2 sensors = 4 nodes; controlsHost + 2 readingForHost = 3 edges
    assert res == {"nodes": 4, "edges": 3}
    fan_nodes = [
        r for r in transport.requests[0].records
        if r.payload.get("sensorType") == "Fan"
    ]
    temp_nodes = [
        r for r in transport.requests[0].records
        if r.payload.get("sensorType") == "Temperature"
    ]
    assert fan_nodes and fan_nodes[0].payload["fanRpm"] == 5000.0
    assert temp_nodes and temp_nodes[0].payload["celsius"] == 24.0


def test_parse_sensor_list_handles_na_values():
    rows = parse_sensor_list("Voltage 1 | na | Volts | ns |")
    assert rows == [
        {"name": "Voltage 1", "value": None, "unit": "Volts", "status": "ns"}
    ]


async def test_ingest_rejects_legacy_structural_fields(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError):
        await ingest_entities([{"id": "legacy", "type": "Legacy"}], ingest=service)


async def test_ingest_empty_is_rejected(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError, match="at least one entity"):
        await ingest_entities([], ingest=service)
    for ingestor in (
        ingest_temperature_readings,
        ingest_fan_settings,
        ingest_sensor_readings,
    ):
        # these mappers no-op on an empty batch (scaffold-only input), not raise
        assert await ingestor([], ingest=service) == {"nodes": 0, "edges": 0}
