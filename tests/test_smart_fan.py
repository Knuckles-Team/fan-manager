"""Regression tests for the smart fan-manager: iDRAC-auto fallback + thermal-trend
aggregation. These lock in the two behaviours added for the homelab so they can be
re-run any time (``pytest tests/test_smart_fan.py``) as a regression gate."""

import fan_manager.fan_manager as fm


class _Runner:
    """Fake CommandRunner. ``raise_manual`` makes the raw *manual level-set* command
    (``... 0x02 ...``) fail, emulating a BMC (e.g. the R510) that rejects raw control."""

    def __init__(self, raise_manual: bool = False):
        self.raise_manual = raise_manual
        self.calls: list = []

    def which(self, name: str):
        return "/usr/bin/ipmitool"

    def run(self, argv, *, check: bool = True):
        self.calls.append(list(argv))
        if self.raise_manual and "0x02" in argv:
            raise RuntimeError("Command '[...]' returned non-zero exit status 1.")
        return ""


def test_set_fan_manual_path(monkeypatch):
    monkeypatch.setattr(fm, "_FAN_MODE", "manual")
    r = _Runner(raise_manual=False)
    out = fm.set_fan(10, runner=r)
    assert out["status"] == 200 and out.get("mode") != "idrac-auto"
    assert any("0x02" in c for c in r.calls)  # actually applied a manual level


def test_set_fan_falls_back_to_idrac_auto_and_is_sticky(monkeypatch):
    """A BMC that rejects raw manual control -> enable iDRAC AUTOMATIC once, status 200
    (NOT an error 500), and never retry raw control on this host again."""
    monkeypatch.setattr(fm, "_FAN_MODE", "manual")
    r = _Runner(raise_manual=True)
    out = fm.set_fan(10, runner=r)
    assert out["status"] == 200 and out.get("mode") == "idrac-auto"
    # enabled automatic fan control (0x30 0x30 0x01 0x01)
    assert any(c[-4:] == ["0x30", "0x30", "0x01", "0x01"] for c in r.calls)
    assert fm._FAN_MODE == "idrac-auto"
    # sticky: a second call short-circuits — no ipmitool invocation at all
    r2 = _Runner(raise_manual=True)
    out2 = fm.set_fan(20, runner=r2)
    assert out2.get("mode") == "idrac-auto"
    assert r2.calls == []


def test_kg_thermal_trend_aggregates_not_per_sample(monkeypatch):
    """Samples accumulate and are distilled to ONE trend when the window elapses —
    never one KG write per ping (the DB-bloat guard)."""
    import time as _t

    import fan_manager.kg_ingest as kgi

    captured: list = []

    async def _fake_ingest_thermal_trend(trend, host=None, **_kw):
        captured.append(trend)

    monkeypatch.setattr(kgi, "ingest_thermal_trend", _fake_ingest_thermal_trend)
    monkeypatch.setenv("FAN_MANAGER_KG_INGEST", "true")
    monkeypatch.setenv("FAN_MANAGER_KG_AGGREGATE_S", "3600")
    monkeypatch.setattr(fm, "_FAN_MODE", "manual")
    fm._thermal_buf.clear()
    fm._thermal_last_flush[0] = _t.time()  # "just flushed" -> the next few only accumulate

    for temp, fan in [(50.0, 10), (60.0, 20), (70.0, 30)]:
        fm._kg_record_thermal_sample(temp, fan)
    assert captured == []               # NOT ingested per-sample
    assert len(fm._thermal_buf) == 3

    fm._thermal_last_flush[0] = 0.0      # window elapsed -> distill on the next sample
    fm._kg_record_thermal_sample(80.0, 40)
    assert len(captured) == 1            # exactly ONE trend written
    trend = captured[0]
    assert trend["min_temp"] == 50.0 and trend["max_temp"] == 80.0
    assert trend["avg_temp"] == 65.0 and trend["samples"] == 4
    assert fm._thermal_buf == []         # window reset after distill


def test_kg_ingest_disabled_is_noop(monkeypatch):
    monkeypatch.setenv("FAN_MANAGER_KG_INGEST", "false")
    fm._thermal_buf.clear()
    fm._kg_record_thermal_sample(99.0, 100)
    assert fm._thermal_buf == []  # short-circuits before buffering
