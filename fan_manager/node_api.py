"""Read-only per-node HTTP endpoint served by every fan-manager daemon (CONN-FAN-MANAGER-R002).

The fan-manager daemon runs on each server, next to that server's BMC. When
``FAN_MANAGER_NODE_API_PORT`` is set, the daemon also serves this endpoint so a
remote connector can read the node's temperature and BMC state.

The endpoint serves ``GET`` only. It exposes no fan-level, power, BMC user, or
raw IPMI write: every other method returns 405 before request authentication.
When
``FAN_MANAGER_NODE_API_TOKEN`` is set, each request except ``/health`` must
carry ``Authorization: Bearer <token>``. The endpoint binds to
``FAN_MANAGER_NODE_API_BIND`` (default loopback); a deployment sets it to the
node's own address.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from fan_manager import ipmi
from fan_manager.fan_manager import get_temp
from fan_manager.kg_ingest import parse_sensor_list

_log = logging.getLogger("FanManager.node_api")


def _sensor_records() -> dict[str, Any]:
    response = ipmi.sensors("full")
    if response.get("status") != 200:
        return {"records": [], "status": "source-unavailable"}
    return {"records": parse_sensor_list(str(response.get("response") or ""))}


#: The only operations a node serves. Each is an in-band read of the local BMC.
READ_OPERATIONS: dict[str, Callable[[], dict[str, Any]]] = {
    "temperature": get_temp,
    "power_status": lambda: ipmi.power("status"),
    "chassis_status": lambda: ipmi.chassis("status"),
    "sensors_list": lambda: ipmi.sensors("list"),
    "sensors_full": lambda: ipmi.sensors("full"),
    "sensors_records": _sensor_records,
    "sel_list": lambda: ipmi.sel("list"),
    "sel_elist": lambda: ipmi.sel("elist"),
    "sel_info": lambda: ipmi.sel("info"),
    "sol_info": lambda: ipmi.sol("info"),
    "lan_print": lambda: ipmi.lan("print"),
    "user_list": lambda: ipmi.user("list"),
    "mc_info": lambda: ipmi.mc("info"),
    "mc_selftest": lambda: ipmi.mc("selftest"),
}


def node_name() -> str:
    """The name this node reports, from ``FAN_MANAGER_HOST`` or the hostname."""
    return os.getenv("FAN_MANAGER_HOST") or os.uname().nodename


class _Handler(BaseHTTPRequestHandler):
    token: str = ""
    node: str = ""
    operations: dict[str, Callable[[], dict[str, Any]]] = READ_OPERATIONS

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        _log.debug("node-api %s", format % args)

    def _send(self, code: int, body: dict[str, Any]) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        # RFC 9110: HEAD carries the same headers as GET but no response body.
        if self.command != "HEAD":
            self.wfile.write(data)

    def send_error(
        self, code: int, message: str | None = None, explain: str | None = None
    ) -> None:
        """Turn BaseHTTPRequestHandler's unknown-method 501 into our 405 contract."""
        if code == 501:
            self._refuse()
            return
        super().send_error(code, message, explain)

    def _authorized(self) -> bool:
        if not self.token:
            return True
        got = self.headers.get("Authorization", "")
        return hmac.compare_digest(got, f"Bearer {self.token}")

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/")
        if path == "/health":
            self._send(200, {"status": "ok", "host": self.node or node_name()})
            return
        if not self._authorized():
            self._send(401, {"error": "unauthorized"})
            return
        prefix = "/v1/"
        op = path[len(prefix) :] if path.startswith(prefix) else ""
        call = self.operations.get(op)
        if call is None:
            self._send(404, {"error": f"unknown read operation '{op}'"})
            return
        result = call()
        self._send(
            200, {"host": self.node or node_name(), "operation": op, "result": result}
        )

    def _refuse(self) -> None:
        self._send(405, {"error": "the node endpoint is read-only"})

    do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = _refuse  # noqa: N815


def make_server(
    port: int,
    bind: str = "127.0.0.1",
    token: str | None = None,
    node: str = "",
    operations: dict[str, Callable[[], dict[str, Any]]] | None = None,
) -> ThreadingHTTPServer:
    """Build (not start) the read-only node server."""
    attrs: dict[str, Any] = {"token": token or "", "node": node}
    if operations is not None:
        attrs["operations"] = operations
    handler = type("NodeHandler", (_Handler,), attrs)
    return ThreadingHTTPServer((bind, port), handler)


def start_from_env() -> ThreadingHTTPServer | None:
    """Start the node endpoint in a daemon thread when ``FAN_MANAGER_NODE_API_PORT`` is set."""
    port = os.getenv("FAN_MANAGER_NODE_API_PORT", "").strip()
    if not port:
        return None
    server = make_server(
        int(port),
        bind=os.getenv("FAN_MANAGER_NODE_API_BIND", "").strip() or "127.0.0.1",
        token=os.getenv("FAN_MANAGER_NODE_API_TOKEN", "").strip(),
    )
    threading.Thread(
        target=server.serve_forever, name="fan-node-api", daemon=True
    ).start()
    _log.info("node endpoint serving read operations on port %s", port)
    return server
