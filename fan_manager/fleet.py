"""Aggregate the per-node read endpoints into one connector answer (CONN-FAN-MANAGER-R003).

The connector usually runs away from any BMC. When ``FAN_MANAGER_HOSTS`` is
set, an in-band read (no out-of-band ``host``) is sent to every node endpoint
and the answers are returned keyed by node name.

Routing needs two settings. ``FAN_MANAGER_HOSTS`` is the comma-separated list
of node names (the same names the derivation pass uses).
``FAN_MANAGER_NODE_URL_TEMPLATE`` maps one name to its endpoint, for example
``http://{host}.example:9180``. An entry that is already an ``http(s)://`` URL
is used as is. ``FAN_MANAGER_NODE_API_TOKEN`` is sent as a bearer token.

Writes are never fanned out: the node endpoints serve reads only.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any


def node_endpoints(raw: str | None = None, template: str | None = None) -> list[str]:
    """Base URLs of every node endpoint named by ``FAN_MANAGER_HOSTS``."""
    raw = os.getenv("FAN_MANAGER_HOSTS", "") if raw is None else raw
    if template is None:
        template = os.getenv("FAN_MANAGER_NODE_URL_TEMPLATE", "")
    urls: list[str] = []
    for entry in (e.strip() for e in raw.split(",")):
        if not entry:
            continue
        if entry.startswith(("http://", "https://")):
            urls.append(entry.rstrip("/"))
        elif template:
            urls.append(template.strip().format(host=entry).rstrip("/"))
    return list(dict.fromkeys(urls))


def enabled() -> bool:
    """True when the connector routes in-band reads to the node endpoints."""
    return bool(node_endpoints())


def _fetch(base: str, operation: str, timeout: float) -> tuple[str, dict[str, Any]]:
    if not base.startswith(("http://", "https://")):
        return base, {
            "response": None,
            "status": 400,
            "error": "node endpoint must be http(s)",
        }
    req = urllib.request.Request(f"{base}/v1/{operation}")
    token = os.getenv("FAN_MANAGER_NODE_API_TOKEN", "").strip()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310  # nosec B310 - scheme checked above
            body = json.loads(resp.read().decode())
        return str(body.get("host") or base), body.get("result") or {}
    except (urllib.error.URLError, OSError, ValueError) as exc:
        reason = getattr(exc, "code", None) or type(exc).__name__
        return base, {
            "response": None,
            "status": 502,
            "error": f"node unreachable: {reason}",
        }


def read_all(operation: str, timeout: float = 20.0) -> dict[str, Any]:
    """Run one read operation on every node and return the answers by node name."""
    endpoints = node_endpoints()
    if not endpoints:
        return {
            "response": None,
            "status": 400,
            "error": "FAN_MANAGER_HOSTS and FAN_MANAGER_NODE_URL_TEMPLATE name no node",
        }
    with ThreadPoolExecutor(max_workers=min(16, len(endpoints))) as pool:
        answers = list(pool.map(lambda b: _fetch(b, operation, timeout), endpoints))
    nodes = dict(answers)
    ok = sum(
        1 for r in nodes.values() if isinstance(r, dict) and r.get("status", 200) == 200
    )
    result: dict[str, Any] = {
        "response": nodes,
        "command": f"fleet {operation}",
        "status": 200 if ok else 502,
        "nodes": len(nodes),
        "nodes_ok": ok,
    }
    if not ok:
        result["error"] = "no node answered"
    return result
