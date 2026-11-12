"""MCP tools for native knowledge-graph ingestion of fan-manager telemetry.

CONCEPT:AU-KG.ingest.enterprise-source-extractor — KG ingest (tag ``kg``)

Wire-First: these tools list live data via the real fan-manager surface (``sensors -j``
for temperature, ``ipmitool sensor list`` for the SDR) and push it into the ONE
medulla engine as typed ``:TemperatureReading`` / ``:SensorReading`` timeseries
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
    async def fan_ingest_telemetry_temperature(
        host: str | None = Field(
            default=None,
            description="BMC hostname or IP, recorded for provenance.",
        ),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> Any:
        """Ingest the current CPU temperature into medulla as a typed node.

        Reads the temperature via ``sensors -j`` and pushes it as a
        ``:TemperatureReading`` sample linked to the ``:ManagedHost``.
        """
        if ctx:
            await ctx.info(
                "Ingesting temperature telemetry into the knowledge graph..."
            )
        reading = get_temp()
        if reading.get("status") != 200:
            return {"read": reading, "ingested": None}
        result = await ingest_temperature_readings([reading], host=host)
        return {"read": 1, "ingested": result}

    @mcp.tool(tags={"kg"})
    async def fan_ingest_telemetry_sensors(
        host: str | None = Field(
            default=None,
            description="BMC hostname or IP, recorded for provenance.",
        ),
        target_json: str | None = Field(
            default=None,
            description="Optional JSON object {host,user,password} that drives the "
            "read out-of-band over LAN.",
        ),
        ctx: Context | None = Field(
            default=None, description="MCP context for progress reporting"
        ),
    ) -> Any:
        """Ingest the full IPMI sensor table into medulla as typed nodes.

        Reads the SDR (``ipmitool sensor list``), parses it and pushes each row as
        a ``:SensorReading`` (fan RPM, temperature or voltage) node.
        """
        if ctx:
            await ctx.info("Ingesting sensor telemetry into the knowledge graph...")
        try:
            target = json.loads(target_json) if target_json else None
        except Exception:  # noqa: BLE001
            return {"error": "Operation failed"}
        sensor_result = ipmi.sensors(action="full", target=target)
        if sensor_result.get("status") != 200:
            return {"read": sensor_result, "ingested": None}
        records = parse_sensor_list(sensor_result.get("response") or "")
        result = await ingest_sensor_readings(records, host=host)
        return {"read": len(records), "ingested": result}
