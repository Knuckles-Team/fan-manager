"""Native epistemic-graph ingestion for Fan Manager thermal telemetry (typed nodes).

CONCEPT:AU-KG.ingest.enterprise-source-extractor. Fan Manager natively pushes its
thermal timeseries into the ONE epistemic-graph knowledge graph as **typed OWL nodes**
— ``:TemperatureReading`` / ``:FanSpeedSetting`` / ``:SensorReading`` samples, each linked
to the ``:ManagedHost`` and its ``:FanController`` — using the lightweight engine client
(``GraphComputeEngine()._client`` + ``txn``), the same fast client the blob ``MediaStore``
uses, NOT the heavy in-process ingestion engine.

Entirely best-effort and dependency-/engine-guarded: with no agent-utilities KG stack or
no reachable engine, every entry point **no-ops** (returns ``None``), so fan-manager keeps
managing thermals with zero KG infrastructure. Node ids follow ``fan:<class>:<extId>`` and
each entity's ``type`` matches a class the ``fan_manager.ontology`` ``fan.ttl`` federates.

The write path prefers the shared primitive
``agent_utilities.knowledge_graph.memory.native_ingest``; when that is not present in the
installed ``agent_utilities`` it falls back to a self-contained txn dance over the same
fast engine client, so the behaviour is identical either way.
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("fan_manager.kg")

_SOURCE = "fan-manager"
_DOMAIN = "fan"
_DEFAULT_GRAPH = "__commons__"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _client() -> tuple[Any | None, str]:
    """Return ``(engine_client, graph_name)`` or ``(None, "")`` when unavailable."""
    try:
        from agent_utilities.knowledge_graph.core.graph_compute import (
            GraphComputeEngine,
        )
    except Exception as e:  # noqa: BLE001 — KG stack absent
        logger.debug("KG ingest unavailable (import): %s", e)
        return None, ""
    try:
        engine = GraphComputeEngine()
        client = getattr(engine, "_client", None)
        if client is None:
            return None, ""
        return client, (getattr(engine, "graph_name", None) or _DEFAULT_GRAPH)
    except Exception as e:  # noqa: BLE001 — engine unreachable
        logger.debug("KG ingest: engine unreachable: %s", e)
        return None, ""


def _local_write_nodes(
    client: Any,
    graph: str,
    nodes: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None,
) -> dict[str, int] | None:
    """Self-contained txn fallback (used when the shared primitive is absent)."""
    nodes = [n for n in nodes if n.get("id")]
    if not nodes:
        return None
    try:
        txn = client.txn.begin(graph=graph)
        for node in nodes:
            props = {k: v for k, v in node.items() if k != "id" and v is not None}
            props.setdefault("source", _SOURCE)
            props.setdefault("domain", _DOMAIN)
            client.txn.add_node(txn, node["id"], props)
        committed = client.txn.commit(txn)
    except Exception as e:  # noqa: BLE001 — engine/txn failure is non-fatal
        logger.warning("KG ingest: txn failed: %s", e)
        return None
    if not committed:
        logger.warning("KG ingest: txn not committed (conflict)")
        return None

    edges = 0
    for rel in relationships or []:
        try:
            client.edges.add(
                rel["source"], rel["target"], {"type": rel.get("type", "RELATED")}
            )
            edges += 1
        except Exception as e:  # noqa: BLE001 — pure edge link, best-effort
            logger.debug("KG ingest: edge skipped: %s", e)

    logger.info("KG ingest[fan]: wrote %d nodes, %d edges", len(nodes), edges)
    return {"nodes": len(nodes), "edges": edges}


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write typed OWL nodes (+ edges) into epistemic-graph via the fast engine client.

    ``entities``: ``[{"id":..., "type":<owl:Class>, ...props}]``.
    ``relationships``: ``[{"source":id, "target":id, "type":<link>}]``.
    Returns ``{"nodes":n, "edges":m}`` or ``None`` (no engine / failure; never raises).
    Prefers the shared ``native_ingest`` primitive; otherwise uses the local txn fallback.
    ``client``/``graph`` may be injected (tests); otherwise resolved on demand.
    """
    entities = [e for e in (entities or []) if e.get("id")]
    if not entities:
        return None

    # Preferred path: the shared fleet primitive (single canonical txn implementation).
    if client is None:
        try:
            from agent_utilities.knowledge_graph.memory.native_ingest import (
                ingest_entities as _shared_ingest,
            )

            return _shared_ingest(entities, relationships, source=source, domain=domain)
        except Exception as e:  # noqa: BLE001 — primitive absent / engine down
            logger.debug("KG ingest: shared primitive unavailable: %s", e)

    if client is None:
        client, graph = _client()
    if client is None:
        return None
    return _local_write_nodes(client, graph or _DEFAULT_GRAPH, entities, relationships)


def ingest_documents(
    documents: list[dict[str, Any]],
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write text records as ``:Document`` nodes (semantic-search fodder).

    Each doc: ``{"id":..., "text":..., "title"?:..., "source_uri"?:..., ...props}``.
    Prefers the shared primitive; otherwise maps to ``:Document`` and writes locally.
    """
    documents = [d for d in (documents or []) if d.get("id")]
    if not documents:
        return None
    if client is None:
        try:
            from agent_utilities.knowledge_graph.memory.native_ingest import (
                ingest_documents as _shared_docs,
            )

            return _shared_docs(documents, source=source, domain=domain)
        except Exception as e:  # noqa: BLE001 — primitive absent / engine down
            logger.debug("KG ingest: shared doc primitive unavailable: %s", e)

    now = _now()
    nodes: list[dict[str, Any]] = []
    for doc in documents:
        text = doc.get("text") or doc.get("content")
        if not text:
            continue
        node = {k: v for k, v in doc.items() if k not in ("content",) and v is not None}
        node["type"] = "Document"
        node["text"] = text
        node.setdefault("created_at", now)
        nodes.append(node)
    if not nodes:
        return None
    if client is None:
        client, graph = _client()
    if client is None:
        return None
    return _local_write_nodes(client, graph or _DEFAULT_GRAPH, nodes, None)


def media_store() -> Any | None:
    """Return a :class:`MediaStore` over a live engine (for raw-blob ingestion), or ``None``.

    Fan Manager has no blob modality today; this is provided for parity with the fleet
    primitive so future firmware/log-dump capture can push raw bytes uniformly.
    """
    try:
        from agent_utilities.knowledge_graph.memory.native_ingest import (
            media_store as _shared_media,
        )

        return _shared_media()
    except Exception as e:  # noqa: BLE001
        logger.debug("KG ingest: media_store unavailable: %s", e)
        return None


# --------------------------------------------------------------------------- #
# Domain mappers — fan-manager records -> typed :Class nodes                   #
# --------------------------------------------------------------------------- #


def _host_id(host: str | None) -> str:
    return f"fan:host:{host or 'localhost'}"


def _controller_id(host: str | None) -> str:
    return f"fan:controller:{host or 'localhost'}"


def _host_and_controller(
    host: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build the shared :ManagedHost + :FanController scaffold nodes/links."""
    hid = _host_id(host)
    cid = _controller_id(host)
    label = host or "localhost"
    entities = [
        {"id": hid, "type": "ManagedHost", "name": label, "externalToolId": label},
        {
            "id": cid,
            "type": "FanController",
            "name": f"BMC:{label}",
            "bmcHost": host,
            "externalToolId": label,
        },
    ]
    rels = [{"source": cid, "target": hid, "type": "controlsHost"}]
    return entities, rels


def ingest_temperature_readings(
    readings: list[dict[str, Any]],
    *,
    host: str | None = None,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Map temperature-read envelopes → ``:TemperatureReading`` timeseries nodes.

    Each reading is a fan-manager result dict, e.g.
    ``{"response": 63.0, "command": "sensors -j", "status": 200}`` (optionally carrying
    ``observed_at`` / ``fan_level``). Links every sample to the ``:ManagedHost`` +
    ``:FanController`` and, when a ``fan_level`` is present, emits the derived
    ``:FanSpeedSetting`` and the ``:triggeredSetting`` link.
    """
    if not readings:
        return None
    entities, relationships = _host_and_controller(host)
    hid = _host_id(host)
    for reading in readings or []:
        temp = reading.get("celsius", reading.get("response"))
        if temp is None:
            continue
        at = reading.get("observed_at") or _now()
        rid = f"fan:tempreading:{host or 'localhost'}:{at}"
        entities.append(
            {
                "id": rid,
                "type": "TemperatureReading",
                "celsius": temp,
                "observedAt": at,
                "command": reading.get("command"),
                "sensorStatus": "ok" if reading.get("status") == 200 else "error",
            }
        )
        relationships.append({"source": rid, "target": hid, "type": "readingForHost"})
        level = reading.get("fan_level")
        if level is not None:
            sid = f"fan:setting:{host or 'localhost'}:{at}"
            entities.append(
                {
                    "id": sid,
                    "type": "FanSpeedSetting",
                    "fanLevel": level,
                    "observedAt": at,
                }
            )
            relationships.append(
                {"source": sid, "target": hid, "type": "appliedToHost"}
            )
            relationships.append(
                {"source": rid, "target": sid, "type": "triggeredSetting"}
            )
    if len(entities) <= 2:  # only the host/controller scaffold — no real samples
        return None
    return ingest_entities(entities, relationships, client=client, graph=graph)


def ingest_fan_settings(
    settings: list[dict[str, Any]],
    *,
    host: str | None = None,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Map fan-level write results → ``:FanSpeedSetting`` timeseries nodes.

    Each setting: ``{"fan_level": 42, "command": "ipmitool raw ...", "observed_at"?: ...}``.
    """
    if not settings:
        return None
    entities, relationships = _host_and_controller(host)
    hid = _host_id(host)
    for setting in settings or []:
        level = setting.get("fan_level")
        if level is None:
            continue
        at = setting.get("observed_at") or _now()
        sid = f"fan:setting:{host or 'localhost'}:{at}"
        entities.append(
            {
                "id": sid,
                "type": "FanSpeedSetting",
                "fanLevel": level,
                "observedAt": at,
                "command": setting.get("command"),
            }
        )
        relationships.append({"source": sid, "target": hid, "type": "appliedToHost"})
    if len(entities) <= 2:  # only the host/controller scaffold — no real samples
        return None
    return ingest_entities(entities, relationships, client=client, graph=graph)


def ingest_sensor_readings(
    sensors: list[dict[str, Any]],
    *,
    host: str | None = None,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Map parsed IPMI SDR sensor rows → ``:SensorReading`` nodes.

    Each sensor: ``{"name": "Fan1 RPM", "value": 5000, "unit": "RPM", "type"?: "Fan",
    "status"?: "ok"}`` (as produced by :func:`parse_sensor_list`). Fan-type sensors get
    ``fanRpm``; temperature-type sensors get ``celsius``.
    """
    if not sensors:
        return None
    entities, relationships = _host_and_controller(host)
    hid = _host_id(host)
    at = _now()
    for idx, sensor in enumerate(sensors or []):
        name = sensor.get("name")
        if not name:
            continue
        stype = sensor.get("type") or _classify_sensor(name, sensor.get("unit"))
        sid = f"fan:sensor:{host or 'localhost'}:{name}:{at}:{idx}"
        node: dict[str, Any] = {
            "id": sid,
            "type": "SensorReading",
            "sensorName": name,
            "sensorType": stype,
            "sensorStatus": sensor.get("status"),
            "observedAt": at,
        }
        value = sensor.get("value")
        if value is not None:
            if stype == "Fan":
                node["fanRpm"] = value
            elif stype == "Temperature":
                node["celsius"] = value
        entities.append(node)
        relationships.append({"source": sid, "target": hid, "type": "readingForHost"})
    if len(entities) <= 2:  # only the host/controller scaffold — no real samples
        return None
    return ingest_entities(entities, relationships, client=client, graph=graph)


def _classify_sensor(name: str, unit: str | None) -> str:
    unit = (unit or "").lower()
    lname = name.lower()
    if "rpm" in unit or "fan" in lname:
        return "Fan"
    if "degrees" in unit or "temp" in lname or unit in {"c", "°c"}:
        return "Temperature"
    if "volt" in unit or "volt" in lname:
        return "Voltage"
    return "Unknown"


def parse_sensor_list(raw: str) -> list[dict[str, Any]]:
    """Parse ``ipmitool sensor list`` pipe-delimited output into sensor records.

    Rows look like ``Fan1 RPM | 5000.000 | RPM | ok | ...``. Non-numeric / 'na' values
    are surfaced as ``None`` so the timeseries still records presence + status.
    """
    records: list[dict[str, Any]] = []
    for line in (raw or "").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3 or not parts[0]:
            continue
        name, raw_val, unit = parts[0], parts[1], parts[2]
        status = parts[3] if len(parts) > 3 else None
        value: float | None
        try:
            value = float(raw_val)
        except (TypeError, ValueError):
            value = None
        records.append({"name": name, "value": value, "unit": unit, "status": status})
    return records
