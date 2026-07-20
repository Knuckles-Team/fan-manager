"""Regression tests for epistemic-graph–driven fan control (Phases 1-3 of
``reports/epistemic-graph-fan-control-plan.md``). Locks the pure reasoning (baseline
learning, policy derivation with its safety bounds, anomaly detection, ambient correlation),
the Phase-2 approved-policy control seam, and one end-to-end derivation pass over a fake KG.

Re-run as the fan-control regression gate: ``pytest tests/test_kg_control.py``.
"""

import json

import fan_manager.fan_manager as fm
import fan_manager.kg_control as kc


def _trend(avg, fan, at, *, span=5):
    return {
        "avg_temp": avg, "min_temp": avg - span, "max_temp": avg + span,
        "avg_fan": fan, "fan_mode": "manual", "samples": 150, "window_s": 3600,
        "observed_at": at,
    }


# --- numeric helpers ------------------------------------------------------- #
def test_percentile_interpolates():
    assert kc._percentile([50, 52, 54, 56, 58, 60, 62, 64], 50) == 57.0
    assert kc._percentile([10], 95) == 10.0
    assert kc._percentile([], 50) is None


# --- Phase 1: baseline ----------------------------------------------------- #
def test_compute_baseline_distills_distribution_and_inertia():
    trends = [
        _trend(t, f, f"2026-07-{d:02d}T00:00:00Z")
        for d, (t, f) in enumerate(
            [(50, 10), (52, 10), (54, 15), (56, 15), (58, 20), (60, 20), (62, 25), (64, 25)], 1
        )
    ]
    b = kc.compute_baseline(trends, host="h1")
    assert b is not None
    assert b["temp_p50"] == 57.0
    assert b["temp_p95"] == 68.3          # p95 of the max tail (avg+5)
    assert b["idle_temp"] == 50.0 and b["load_temp"] == 64.0
    assert b["avg_fan"] == 17.5 and b["windows"] == 8
    assert b["thermal_inertia"] is not None and b["thermal_inertia"] > 0  # fan varied


def test_compute_baseline_insufficient_history_is_none():
    trends = [_trend(55, 10, f"2026-07-0{d}T00:00:00Z") for d in range(1, 4)]  # 3 < MIN_WINDOWS
    assert kc.compute_baseline(trends) is None
    assert kc.compute_baseline(trends, min_windows=3) is not None  # threshold is tunable


# --- Phase 1/3: policy derivation + safety bounds -------------------------- #
def test_derive_policy_quiets_a_cool_host():
    b = {"temp_p50": 52.0, "temp_p95": 58.0, "idle_temp": 45.0, "load_temp": 60.0,
         "thermal_inertia": 0.5, "windows": 300}
    p = kc.derive_policy(b)  # current = DEFAULT_CURVE (cold55 warm80 slow10 fast100)
    assert p["cold"] == 58 and p["slow"] == 8      # let fans idle longer, ease the floor
    assert p["warm"] == 80 and p["fast"] == 100    # top of curve untouched (safety)
    assert p["approved"] is False                  # report-only without an envelope
    assert "headroom" in p["rationale"]


def test_derive_policy_ramps_earlier_on_a_hot_host():
    b = {"temp_p50": 70.0, "temp_p95": 78.0, "idle_temp": 60.0, "load_temp": 76.0,
         "thermal_inertia": 0.3, "windows": 300}
    p = kc.derive_policy(b)
    assert p["cold"] == 70 and p["slow"] == 13     # earlier ramp, higher base
    assert p["cold"] < p["warm"] and p["slow"] >= kc.SLOW_FLOOR


def test_derive_policy_never_breaches_safety_ceiling():
    b = {"temp_p50": 80.0, "temp_p95": 100.0, "idle_temp": 70.0, "load_temp": 95.0,
         "thermal_inertia": 0.1, "windows": 300}
    p = kc.derive_policy(b, ceiling_c=90.0, margin_c=15.0)
    assert p["cold"] <= 70                          # bounded by warm-10 AND safe-5
    assert p["cold"] < p["warm"] and p["slow"] >= kc.SLOW_FLOOR


def test_derive_policy_insufficient_data_holds_current():
    p = kc.derive_policy(None, {"cold": 55, "warm": 80, "slow": 10, "fast": 100, "poll": 24})
    assert p["cold"] == 55 and p["approved"] is False
    assert "insufficient" in p["rationale"]


def test_derive_policy_envelope_bounded_auto_approve():
    cool = {"temp_p50": 52.0, "temp_p95": 58.0, "idle_temp": 45.0, "load_temp": 60.0,
            "thermal_inertia": 0.5, "windows": 300}
    hot = {"temp_p50": 70.0, "temp_p95": 78.0, "idle_temp": 60.0, "load_temp": 76.0,
           "thermal_inertia": 0.3, "windows": 300}
    env = {"cold": 5, "slow": 5}
    assert kc.derive_policy(cool, envelope=env)["approved"] is True    # small delta → approve
    assert kc.derive_policy(hot, envelope=env)["approved"] is False    # cold jumps 15 → hold


# --- Phase 3: anomaly detection + ambient correlation ---------------------- #
_BASE = {"temp_p50": 55.0, "temp_p95": 62.0, "idle_temp": 45.0, "load_temp": 60.0,
         "thermal_inertia": 0.4, "windows": 300}


def test_detect_anomaly_above_baseline():
    recent = [_trend(t, 20, f"2026-07-14T0{i}:00:00Z") for i, t in enumerate([79, 80, 81])]
    a = kc.detect_anomaly(recent, _BASE)
    assert a is not None
    assert a["kind"] == "above-baseline" and a["observed_c"] == 80.0 and a["zscore"] >= 3.0


def test_detect_anomaly_none_when_normal():
    recent = [_trend(t, 20, f"2026-07-14T0{i}:00:00Z") for i, t in enumerate([56, 57, 58])]
    assert kc.detect_anomaly(recent, _BASE) is None


def test_detect_anomaly_cooling_saturated():
    recent = [_trend(61, f, f"2026-07-14T0{i}:00:00Z") for i, f in enumerate([96, 97, 98])]
    a = kc.detect_anomaly(recent, _BASE)
    assert a is not None
    assert a["kind"] == "cooling-saturated"     # fans pinned yet still above load temp


def test_classify_ambient_collapses_simultaneous_spikes():
    anoms = {
        "a": {"kind": "above-baseline"}, "b": {"kind": "above-baseline"},
        "c": None, "d": {"kind": "cooling-saturated"},
    }
    kc.classify_ambient(anoms, total_hosts=4)
    a, b, d = anoms["a"], anoms["b"], anoms["d"]
    assert a is not None and b is not None and d is not None
    assert a["kind"] == "ambient" and b["kind"] == "ambient"
    assert d["kind"] == "cooling-saturated"   # different fault, not retagged


def test_classify_ambient_leaves_a_lone_spike_alone():
    anoms = {"a": {"kind": "above-baseline"}, "b": None, "c": None, "d": None}
    kc.classify_ambient(anoms, total_hosts=4)
    a = anoms["a"]
    assert a is not None and a["kind"] == "above-baseline"      # 1 of 4 → not ambient


def test_notify_uses_bounded_shared_http_boundary(monkeypatch):
    import agent_utilities.core.config as config_module
    import agent_utilities.protocols.source_connectors.http_safety as http_safety

    monkeypatch.setattr(
        config_module,
        "setting",
        lambda key, default=None, cast=None: (
            "https://notify.example.invalid/events"
            if key == "FAN_MANAGER_NOTIFY_URL"
            else default
        ),
    )
    calls = []
    monkeypatch.setattr(
        http_safety,
        "safe_post_json",
        lambda url, payload, **kwargs: calls.append((url, payload, kwargs)) or {},
    )

    kc._notify("bounded message")

    assert calls[0][1] == {"source": "fan-control", "message": "bounded message"}
    assert calls[0][2]["max_request_bytes"] == 64 * 1024
    assert calls[0][2]["tls_service"] == "fan-manager-notify"


# --- Phase 2: the approved-policy control seam ----------------------------- #
_DEFAULTS = {
    "temperature_poll_rate": 24, "minimum_fan_speed": 10, "maximum_fan_speed": 100,
    "minimum_temperature": 55, "maximum_temperature": 80, "temperature_power": 5,
}


def test_load_fan_policy_no_file_returns_defaults(monkeypatch):
    monkeypatch.delenv("FAN_MANAGER_POLICY_FILE", raising=False)
    assert fm.load_fan_policy(_DEFAULTS) == _DEFAULTS


def _write_policy(tmp_path, monkeypatch, payload):
    p = tmp_path / "fan-policy.json"
    p.write_text(json.dumps(payload))
    monkeypatch.setenv("FAN_MANAGER_POLICY_FILE", str(p))


def test_load_fan_policy_applies_approved(tmp_path, monkeypatch):
    _write_policy(tmp_path, monkeypatch,
                  {"r510": {"cold": 60, "warm": 82, "slow": 8, "fast": 100, "poll": 30,
                            "approved": True}})
    out = fm.load_fan_policy(_DEFAULTS, host="r510")
    assert out["minimum_temperature"] == 60 and out["maximum_temperature"] == 82
    assert out["minimum_fan_speed"] == 8 and out["temperature_poll_rate"] == 30


def test_load_fan_policy_ignores_unapproved(tmp_path, monkeypatch):
    _write_policy(tmp_path, monkeypatch, {"r510": {"cold": 60, "approved": False}})
    assert fm.load_fan_policy(_DEFAULTS, host="r510") == _DEFAULTS


def test_load_fan_policy_rejects_incoherent_curve(tmp_path, monkeypatch):
    _write_policy(tmp_path, monkeypatch,
                  {"r510": {"cold": 90, "warm": 80, "approved": True}})  # cold >= warm
    assert fm.load_fan_policy(_DEFAULTS, host="r510") == _DEFAULTS


def test_load_fan_policy_clamps_out_of_range(tmp_path, monkeypatch):
    # cold 35 is below the 40 floor and slow -5 below 0 → both clamped; curve stays coherent.
    _write_policy(tmp_path, monkeypatch,
                  {"r510": {"cold": 35, "warm": 85, "slow": -5, "fast": 100, "approved": True}})
    out = fm.load_fan_policy(_DEFAULTS, host="r510")
    assert out["minimum_temperature"] == 40 and out["minimum_fan_speed"] == 0


def test_load_fan_policy_wildcard_host(tmp_path, monkeypatch):
    _write_policy(tmp_path, monkeypatch,
                  {"*": {"cold": 58, "warm": 80, "slow": 9, "fast": 100, "approved": True}})
    out = fm.load_fan_policy(_DEFAULTS, host="unknown-host")
    assert out["minimum_temperature"] == 58 and out["minimum_fan_speed"] == 9


# --- orchestration: one derivation pass over a fake KG --------------------- #
def test_run_derivation_end_to_end(monkeypatch):
    import fan_manager.kg_ingest as kgi

    synth = [
        _trend(t, f, f"2026-07-{d:02d}T00:00:00Z")
        for d, (t, f) in enumerate(
            [(50, 10), (52, 10), (54, 15), (56, 15), (58, 20), (60, 20), (62, 25), (64, 25)], 1
        )
    ]
    cap: dict[str, list] = {"baseline": [], "policy": [], "anomaly": []}
    monkeypatch.setattr(kgi, "read_thermal_trends",
                        lambda host, days=14: synth if host == "h1" else [])
    monkeypatch.setattr(kgi, "ingest_thermal_baseline",
                        lambda b, host=None: cap["baseline"].append((host, b)))
    monkeypatch.setattr(kgi, "ingest_fan_policy",
                        lambda p, host=None: cap["policy"].append((host, p)))
    monkeypatch.setattr(kgi, "ingest_thermal_anomaly",
                        lambda a, host=None: cap["anomaly"].append((host, a)))

    out = kc.run_derivation(["h1", "empty"], days=14)
    assert out["hosts"] == 2
    # h1 has enough history → baseline + a (report-only) policy; empty → policy only, no baseline
    assert [h for h, _ in cap["baseline"]] == ["h1"]
    assert sorted(h for h, _ in cap["policy"]) == ["empty", "h1"]
    h1_policy = next(p for h, p in cap["policy"] if h == "h1")
    assert h1_policy["approved"] is False           # report-only by default
    empty_policy = next(p for h, p in cap["policy"] if h == "empty")
    assert "insufficient" in empty_policy["rationale"]
