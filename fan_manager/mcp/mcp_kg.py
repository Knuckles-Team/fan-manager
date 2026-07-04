"""MCP tools for native knowledge-graph ingestion of fan-manager telemetry.

CONCEPT:AU-KG.ingest.enterprise-source-extractor — KG ingest (tag ``kg``)

Wire-First: these tools list live data via the real fan-manager surface (``sensors -j``
for temperature, ``ipmitool sensor list`` for the SDR) and push it into the ONE
epistemic-graph engine as typed ``:TemperatureReading`` / ``:SensorReading`` timeseries
nodes. Best-effort: when no engine is reachable the tool returns ``{"ingested": None}``.
"""

import json
from typing import Any

from fastmcp import Context, FastMCP
from pydantic import Field

from fan_manager import ipmi
from fan_manager.fan_manager import get_temp
from fan_manager.kg_ingest import (
    ingest_sensor_readings,
    ingest_temperature_readings,
    parse_sensor_list,
)


def register_kg_tools(mcp: FastMCP):
    @mcp.tool(tags={"kg"})
    async def fan_ingest_telemetry(
        action: str = Field(
            default="temperature",
            description="Action to perform. Must be one of: 'temperature', 'sensors'.",
        ),
        params_json: str = Field(
            default="{}",
            description="JSON string of options. Optional 'host' (BMC hostname/IP, "
            "for provenance and out-of-band). For 'sensors', an optional 'target' "
            "{host,user,password} drives the read out-of-band over LAN.",
        ),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> Any:
        """Ingest live thermal telemetry into epistemic-graph as typed nodes.

        Action-routed methods:
          - ``temperature``: read the current CPU temperature via ``sensors -j`` and push
            it as a ``:TemperatureReading`` sample linked to the ``:ManagedHost``.
          - ``sensors``: read the full IPMI SDR (``ipmitool sensor list``), parse it, and
            push each row as a ``:SensorReading`` (fan RPM / temperature / voltage) node.
        """
        if ctx:
            await ctx.info(f"Ingesting {action} telemetry into the knowledge graph...")

        try:
            opts = json.loads(params_json) if params_json else {}
        except Exception as e:  # noqa: BLE001
            return {"error": f"Invalid params_json: {e}"}

        host = opts.get("host")

        if action == "temperature":
            reading = get_temp()
            if reading.get("status") != 200:
                return {"read": reading, "ingested": None}
            result = ingest_temperature_readings([reading], host=host)
            return {"read": 1, "ingested": result}

        if action == "sensors":
            sensor_result = ipmi.sensors(action="full", target=opts.get("target"))
            if sensor_result.get("status") != 200:
                return {"read": sensor_result, "ingested": None}
            records = parse_sensor_list(sensor_result.get("response") or "")
            result = ingest_sensor_readings(records, host=host)
            return {"read": len(records), "ingested": result}

        raise ValueError(f"Unknown action: {action}")
