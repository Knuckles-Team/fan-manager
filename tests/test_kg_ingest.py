"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the ``fan_manager.kg_ingest`` mappers' structural validation (still enforced
locally) and their no-op commit contract, plus the fan-manager telemetry ->
:TemperatureReading / :FanSpeedSetting / :SensorReading mapping shape.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.

SDK GAP (EH-481/SDK-GAPS.md): ``_native_ingest_entities``/``_native_ingest_documents``
are stubs (no SDK equivalent yet for the old dependency-injected
``agent_utilities.knowledge_graph.memory.native_ingest`` ChangeEnvelope committer — see
``fan_manager/kg_ingest.py``'s module docstring). Every ``ingest_*`` call below is
therefore exercised for its validation + no-op-commit contract rather than real graph
writes; the DI-based ``_FakeClient`` coverage of the retired real-commit path is dropped
with it.
"""

from __future__ import annotations

import pytest

from fan_manager.kg_ingest import (
    NativeIngestError,
    ingest_entities,
    ingest_fan_settings,
    ingest_sensor_readings,
    ingest_temperature_readings,
    parse_sensor_list,
)


def test_ingest_entities_validates_then_noops():
    res = ingest_entities(
        [
            {"id": "a", "node_type": "ManagedHost", "name": "h"},
            {"id": "b", "node_type": "FanController"},
        ],
        [{"source": "b", "target": "a", "relationship": "controlsHost"}],
    )
    assert res == {"nodes": 0, "edges": 0}


def test_ingest_temperature_readings_maps_then_noops():
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
    )
    assert res == {"nodes": 0, "edges": 0}


def test_ingest_temperature_reading_without_fan_level_still_noops():
    res = ingest_temperature_readings(
        [{"response": 50.0, "status": 200, "observed_at": "2026-07-04T01:00:00Z"}],
        host="localhost",
    )
    assert res == {"nodes": 0, "edges": 0}


def test_ingest_fan_settings_maps_then_noops():
    res = ingest_fan_settings(
        [
            {
                "fan_level": 80,
                "command": "ipmitool raw 0x30 0x30 0x02 0xff 0x50",
                "observed_at": "2026-07-04T02:00:00Z",
            }
        ],
        host="r710",
    )
    assert res == {"nodes": 0, "edges": 0}


def test_ingest_sensor_readings_classifies_fan_and_temp_then_noops():
    sensors = parse_sensor_list(
        "Fan1 RPM | 5000.000 | RPM | ok |\n"
        "Inlet Temp | 24.000 | degrees C | ok |\n"
        "bad line without pipes\n"
    )
    assert len(sensors) == 2
    assert sensors[0]["unit"] == "RPM"
    assert sensors[1]["unit"] == "degrees C"
    res = ingest_sensor_readings(sensors, host="r820")
    assert res == {"nodes": 0, "edges": 0}


def test_parse_sensor_list_handles_na_values():
    rows = parse_sensor_list("Voltage 1 | na | Volts | ns |")
    assert rows == [
        {"name": "Voltage 1", "value": None, "unit": "Volts", "status": "ns"}
    ]


def test_ingest_rejects_legacy_structural_fields():
    with pytest.raises(NativeIngestError, match="canonical node_type"):
        ingest_entities([{"id": "legacy", "type": "Legacy"}])


def test_ingest_empty_is_rejected():
    with pytest.raises(NativeIngestError, match="at least one entity"):
        ingest_entities([])
    for ingestor in (
        ingest_temperature_readings,
        ingest_fan_settings,
        ingest_sensor_readings,
    ):
        with pytest.raises(NativeIngestError, match="at least one entity"):
            ingestor([])
