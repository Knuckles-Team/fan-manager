"""Per-node read endpoints and connector aggregation (CONN-FAN-MANAGER-R002, R003)."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from fan_manager import fleet, ipmi, node_api
from fan_manager.api_client import Api
from fan_manager.ipmi_api import IpmiApi


def _ops(name: str) -> dict:
    return {
        "temperature": lambda: {"response": 61.0, "status": 200},
        "sensors_list": lambda: {"response": f"sdr-{name}", "status": 200},
        "power_status": lambda: {"response": "on", "status": 200},
    }


@pytest.fixture
def nodes(monkeypatch):
    """Two node endpoints on loopback, each reporting its own name."""
    servers = [
        node_api.make_server(
            0, bind="127.0.0.1", token="t0k", node=n, operations=_ops(n)
        )
        for n in ("node-a", "node-b")
    ]
    for srv in servers:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    ports = [srv.server_address[1] for srv in servers]
    monkeypatch.setenv("FAN_MANAGER_HOSTS", ",".join(str(p) for p in ports))
    monkeypatch.setenv("FAN_MANAGER_NODE_URL_TEMPLATE", "http://127.0.0.1:{host}")
    monkeypatch.setenv("FAN_MANAGER_NODE_API_TOKEN", "t0k")
    yield ports
    for srv in servers:
        srv.shutdown()


def _get(url: str, token: str | None = None, method: str = "GET"):
    req = urllib.request.Request(url, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read()
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return exc.code, json.loads(body) if body else {}


@pytest.mark.spec("CONN-FAN-MANAGER-R002.1")
def test_node_endpoint_serves_reads_and_refuses_writes(nodes):
    """CONN-FAN-MANAGER-R002.1, R002.2: GET reads work, every other method is 405."""
    port = nodes[0]
    base = f"http://127.0.0.1:{port}"
    assert _get(f"{base}/health")[0] == 200
    code, body = _get(f"{base}/v1/temperature", token="t0k")
    assert code == 200 and body["result"]["response"] == 61.0
    assert _get(f"{base}/v1/power_off", token="t0k")[0] == 404
    for method in ("POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"):
        assert _get(f"{base}/v1/temperature", token="t0k", method=method)[0] == 405


@pytest.mark.spec("CONN-FAN-MANAGER-R002.3")
def test_node_endpoint_requires_the_token(nodes):
    """CONN-FAN-MANAGER-R002.3: with a token configured, a request without it is 401."""
    port = nodes[0]
    assert _get(f"http://127.0.0.1:{port}/v1/temperature")[0] == 401
    assert _get(f"http://127.0.0.1:{port}/v1/temperature", token="bad")[0] == 401
    # R002.1's method guard runs first, so an unsupported unauthenticated
    # method is 405 rather than an auth-shaped 401.
    assert _get(f"http://127.0.0.1:{port}/v1/temperature", method="OPTIONS")[0] == 405


@pytest.mark.spec("CONN-FAN-MANAGER-R002.2")
def test_node_read_operations_are_reads_only():
    """CONN-FAN-MANAGER-R002.2: the served operation set names no write."""
    writes = {
        "power_on",
        "power_off",
        "power_cycle",
        "power_reset",
        "power_soft",
        "sel_clear",
        "lan_set",
        "user_set_password",
        "user_enable",
        "user_disable",
        "mc_reset_cold",
        "mc_reset_warm",
        "send_raw",
        "set_fan",
        "sol_deactivate",
        "chassis_identify",
        "chassis_set_boot_device",
    }
    assert not writes & set(node_api.READ_OPERATIONS)


@pytest.mark.spec("CONN-FAN-MANAGER-R003.1")
def test_connector_aggregates_temperature_by_node(nodes):
    """CONN-FAN-MANAGER-R003.1: get_temp returns one answer per node, keyed by name."""
    result = Api().get_temp()
    assert result["status"] == 200
    assert set(result["response"]) == {"node-a", "node-b"}
    assert result["nodes_ok"] == 2


@pytest.mark.spec("CONN-FAN-MANAGER-R003.2")
def test_connector_routes_inband_ipmi_reads(nodes):
    """CONN-FAN-MANAGER-R003.2: an IPMI read with no host goes to every node."""
    result = IpmiApi().sensors_list()
    assert result["response"] == {
        "node-a": {"response": "sdr-node-a", "status": 200},
        "node-b": {"response": "sdr-node-b", "status": 200},
    }


@pytest.mark.spec("CONN-FAN-MANAGER-R003.3")
def test_connector_never_fans_out_writes(nodes, monkeypatch):
    """CONN-FAN-MANAGER-R003.3: writes require one explicit OOB target and never fan out."""
    called = []
    monkeypatch.setattr(
        ipmi, "_exec", lambda runner, target, args, **_: {"status": 500, "args": args}
    )
    assert called == []

    write_calls = [
        ("power_on", {}),
        ("power_off", {}),
        ("power_cycle", {}),
        ("power_reset", {}),
        ("power_soft", {}),
        ("chassis_identify", {}),
        ("chassis_set_boot_device", {"bootdev": "pxe"}),
        ("sel_clear", {}),
        ("sol_deactivate", {}),
        ("lan_set", {"param": "access", "value": "on"}),
        ("user_set_password", {"user_id": "2", "new_password": "new"}),
        ("user_enable", {"user_id": "2"}),
        ("user_disable", {"user_id": "2"}),
        ("mc_reset_cold", {}),
        ("mc_reset_warm", {}),
        ("send_raw", {"data": "0x30 0x30 0x01 0x00"}),
    ]
    for method, kwargs in write_calls:
        result = getattr(IpmiApi(), method)(**kwargs)
        assert result["status"] == 400, method

    # A complete OOB target reaches the runner seam with the credentials intact;
    # this remains a mock and never invokes hardware.
    monkeypatch.setattr(
        ipmi,
        "_exec",
        lambda runner, target, args, **_: {"status": 200, "target": target, "args": args},
    )
    result = IpmiApi().power_off(host="bmc.example", user="operator", password="x")
    assert result == {
        "status": 200,
        "target": {"host": "bmc.example", "user": "operator", "password": "x"},
        "args": ["chassis", "power", "off"],
    }


@pytest.mark.spec("CONN-FAN-MANAGER-R003.4")
def test_unreachable_node_is_reported_not_raised(monkeypatch):
    """CONN-FAN-MANAGER-R003.4: a dead node is a typed 502 entry, not an exception."""
    monkeypatch.setenv("FAN_MANAGER_HOSTS", "http://127.0.0.1:1")
    result = fleet.read_all("temperature", timeout=1)
    assert result["status"] == 502 and result["nodes_ok"] == 0


@pytest.mark.spec("CONN-FAN-MANAGER-R003.5")
def test_hosts_map_through_the_url_template(monkeypatch):
    """CONN-FAN-MANAGER-R003.5: names map through the template; URLs pass through; no template means local."""
    assert fleet.node_endpoints(
        "a, b ,https://c.example/", "http://{host}.example:9180"
    ) == [
        "http://a.example:9180",
        "http://b.example:9180",
        "https://c.example",
    ]
    monkeypatch.setenv("FAN_MANAGER_HOSTS", "r1,r2")
    monkeypatch.delenv("FAN_MANAGER_NODE_URL_TEMPLATE", raising=False)
    assert not fleet.enabled()
