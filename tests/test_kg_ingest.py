"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``fan_manager.kg_ingest`` mappers with a fake engine client (no engine
required), asserting the txn add_node/commit + edge calls and the fan-manager telemetry →
:TemperatureReading / :FanSpeedSetting / :SensorReading mapping.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from fan_manager.kg_ingest import (
    ingest_entities,
    ingest_fan_settings,
    ingest_sensor_readings,
    ingest_temperature_readings,
    parse_sensor_list,
)


class _FakeTxn:
    def __init__(self):
        self.nodes = {}
        self.committed = False

    def begin(self, graph=None):
        self.graph = graph
        return "txn-1"

    def add_node(self, txn, node_id, props):
        self.nodes[node_id] = props

    def commit(self, txn):
        self.committed = True
        return True


class _FakeEdges:
    def __init__(self):
        self.edges = []

    def add(self, src, dst, props):
        self.edges.append((src, dst, props))


class _FakeClient:
    def __init__(self):
        self.txn = _FakeTxn()
        self.edges = _FakeEdges()


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "a", "type": "ManagedHost", "name": "h"},
            {"id": "b", "type": "FanController"},
        ],
        [{"source": "b", "target": "a", "type": "controlsHost"}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.committed is True
    assert set(c.txn.nodes) == {"a", "b"}
    # provenance is stamped
    assert c.txn.nodes["a"]["source"] == "fan-manager"
    assert c.txn.nodes["a"]["domain"] == "fan"
    assert c.edges.edges == [("b", "a", {"type": "controlsHost"})]


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
    assert c.txn.nodes[rid]["type"] == "TemperatureReading"
    assert c.txn.nodes[rid]["celsius"] == 63.0
    assert c.txn.nodes[rid]["observedAt"] == "2026-07-04T00:00:00Z"
    assert c.txn.nodes[sid]["type"] == "FanSpeedSetting"
    assert c.txn.nodes[sid]["fanLevel"] == 42
    assert c.txn.nodes["fan:host:r820"]["type"] == "ManagedHost"
    assert c.txn.nodes["fan:controller:r820"]["type"] == "FanController"
    # links: controlsHost, readingForHost, appliedToHost, triggeredSetting
    kinds = {e[2]["type"] for e in c.edges.edges}
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
    assert not any(n.get("type") == "FanSpeedSetting" for n in c.txn.nodes.values())


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
    assert c.txn.nodes[sid]["type"] == "FanSpeedSetting"
    assert c.txn.nodes[sid]["fanLevel"] == 80


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
    fan_nodes = [n for n in c.txn.nodes.values() if n.get("sensorType") == "Fan"]
    temp_nodes = [
        n for n in c.txn.nodes.values() if n.get("sensorType") == "Temperature"
    ]
    assert fan_nodes and fan_nodes[0]["fanRpm"] == 5000.0
    assert temp_nodes and temp_nodes[0]["celsius"] == 24.0


def test_parse_sensor_list_handles_na_values():
    rows = parse_sensor_list("Voltage 1 | na | Volts | ns |")
    assert rows == [
        {"name": "Voltage 1", "value": None, "unit": "Volts", "status": "ns"}
    ]


def test_ingest_noops_without_engine():
    # No injected client + no reachable engine -> clean no-op.
    assert ingest_entities([{"id": "a", "type": "ManagedHost"}]) is None


def test_ingest_empty_is_noop():
    assert ingest_temperature_readings([], client=_FakeClient()) is None
    assert ingest_sensor_readings([], client=_FakeClient()) is None
    assert ingest_fan_settings([], client=_FakeClient()) is None
