"""Epistemic-graph–driven fan control — learn per-host thermal baselines, recommend
per-host fan policies, and flag thermal anomalies from the accumulated ``:ThermalTrend``
history (see ``reports/epistemic-graph-fan-control-plan.md``).

This module is the **brain**: the reasoning is pure, cheap statistics (percentiles + a
least-squares slope over the at-most-few-hundred hourly trend rows per host) — no ML, no
per-sample work, no numpy. The KG I/O lives in :mod:`fan_manager.kg_ingest`; here we only
compose read → reason → write → notify.

Design stance (from the plan): **report-only by default.** :func:`run_derivation` writes
recommended :FanPolicy nodes with ``approved=false`` and never touches a fan — a host only
acts on a policy that a human (or, once ``--apply`` + a conservative envelope is enabled,
the loop itself) has approved. The applied-policy read seam lives in
:func:`fan_manager.fan_manager.load_fan_policy`.

The pure statistics (``compute_baseline``/``detect_anomaly``/``classify_ambient`` +
``_percentile``/``_slope``) were the reference implementation for a fleet-wide shared
primitive, ``agent_utilities.observability.health`` (metric-agnostic: any named signal,
not just °C — see ``reports/unified-infra-intelligence-plan.md``). This module now
**consumes** that shared primitive via a guarded import, mapping fan-manager's
temp/fan-shaped dicts to/from the kernel's generic ``value_key``/``peak_key``/
``control_key`` shape — dogfooding the extraction. When the installed
``agent-utilities`` predates the shared module (or is absent), it falls back to the
original local implementation below, so this package never breaks on an older
``agent-utilities``.

CONCEPT:FM-OS.control.baseline-learning / .policy-derivation / .anomaly-detection /
.ambient-correlation.
"""

from __future__ import annotations

import json
import logging
import math
import os
from typing import Any

logger = logging.getLogger("fan_manager.control")

try:
    from agent_utilities.observability.health import _percentile as _shared_percentile
    from agent_utilities.observability.health import _slope as _shared_slope
    from agent_utilities.observability.health import (
        compute_baseline as _shared_compute_baseline,
    )
    from agent_utilities.observability.health import (
        correlate as _shared_correlate,
    )
    from agent_utilities.observability.health import (
        detect_anomaly as _shared_detect_anomaly,
    )

    _HAS_SHARED_HEALTH = True
except Exception as _e:  # noqa: BLE001 — older/absent agent-utilities falls back to local
    logger.debug("shared health kernels unavailable, using local fallback: %s", _e)
    _HAS_SHARED_HEALTH = False

# The curve the DaemonSet ships today (``fan-manager -c 55 -w 80 -s 10 -f 100 -p 24``).
# Treated as the "currently running" policy when no approved override exists yet.
DEFAULT_CURVE: dict[str, int] = {
    "cold": 55,
    "warm": 80,
    "slow": 10,
    "fast": 100,
    "poll": 24,
}
# CPU throttle ceiling and the margin we insist p95 stay below it — the safety invariant.
DEFAULT_CEILING_C = 90.0
DEFAULT_MARGIN_C = 15.0
# Fewest hourly trend windows before a baseline is trustworthy enough to derive from.
MIN_WINDOWS = 6
# A fan should never idle to a stop on a server — the hard floor for any derived slow %.
SLOW_FLOOR = 5


# --------------------------------------------------------------------------- #
# small numeric helpers (pure, stdlib only) — delegate to the shared kernel     #
# when available; otherwise the original local implementation.                 #
# --------------------------------------------------------------------------- #
def _g(row: dict[str, Any], *keys: str) -> Any:
    """First present, non-None value among ``keys`` — bridges the clean node form
    (``avgCelsius``) and the raw trend form (``avg_temp``)."""
    for k in keys:
        v = row.get(k)
        if v is not None:
            return v
    return None


def _local_percentile(values: list[float], pct: float) -> float | None:
    """Linear-interpolated percentile of ``values`` (``pct`` in 0..100)."""
    if not values:
        return None
    s = sorted(values)
    if len(s) == 1:
        return float(s[0])
    k = (len(s) - 1) * (pct / 100.0)
    lo = int(math.floor(k))
    hi = min(lo + 1, len(s) - 1)
    return float(s[lo] + (s[hi] - s[lo]) * (k - lo))


def _local_slope(xs: list[float], ys: list[float]) -> float | None:
    """Least-squares slope of ``ys`` on ``xs`` (``None`` if degenerate)."""
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=False)) / denom


def _percentile(values: list[float], pct: float) -> float | None:
    """Linear-interpolated percentile of ``values`` (``pct`` in 0..100)."""
    if _HAS_SHARED_HEALTH:
        return _shared_percentile(values, pct)
    return _local_percentile(values, pct)


def _slope(xs: list[float], ys: list[float]) -> float | None:
    """Least-squares slope of ``ys`` on ``xs`` (``None`` if degenerate)."""
    if _HAS_SHARED_HEALTH:
        return _shared_slope(xs, ys)
    return _local_slope(xs, ys)


# --------------------------------------------------------------------------- #
# Phase 1 — learn baselines                                                    #
# --------------------------------------------------------------------------- #
def _compute_baseline_local(
    trends: list[dict[str, Any]], *, host: str | None, min_windows: int
) -> dict[str, Any] | None:
    """Original local implementation (fallback when the shared kernel is absent)."""
    avg_t = [
        float(v) for r in trends if (v := _g(r, "avgCelsius", "avg_temp")) is not None
    ]
    max_t = [
        float(v) for r in trends if (v := _g(r, "maxCelsius", "max_temp")) is not None
    ]
    fans = [float(v) for r in trends if (v := _g(r, "avgFan", "avg_fan")) is not None]
    if not avg_t or len(avg_t) < min_windows:
        return None
    p50 = _percentile(avg_t, 50)
    p95 = _percentile(max_t or avg_t, 95)
    if p50 is None or p95 is None:
        return None
    # inertia only makes sense if the fan actually varied — pair temp↔fan where both exist
    pairs = [
        (float(f), float(t))
        for r in trends
        if (f := _g(r, "avgFan", "avg_fan")) is not None
        and (t := _g(r, "avgCelsius", "avg_temp")) is not None
    ]
    inertia = None
    if len({f for f, _ in pairs}) >= 3:
        s = _slope([f for f, _ in pairs], [t for _, t in pairs])
        inertia = round(abs(s), 3) if s is not None else None
    return {
        "host": host,
        "temp_p50": round(p50, 1),
        "temp_p95": round(p95, 1),
        "idle_temp": round(min(avg_t), 1),
        "load_temp": round(max(avg_t), 1),
        "avg_fan": round(sum(fans) / len(fans), 1) if fans else None,
        "thermal_inertia": inertia,
        "windows": len(avg_t),
    }


def compute_baseline(
    trends: list[dict[str, Any]],
    *,
    host: str | None = None,
    min_windows: int = MIN_WINDOWS,
) -> dict[str, Any] | None:
    """Distill a host's ``:ThermalTrend`` rows into a :ThermalBaseline (CONCEPT:FM-OS.control.baseline-learning).

    Returns ``None`` when there is too little history to trust. Otherwise a dict with the
    temperature distribution (``temp_p50`` / ``temp_p95``), the idle↔load envelope, and
    ``thermal_inertia`` — the |°C per fan-%| slope that says how much thermal margin a fan
    step actually buys on this box (``None`` when the fan barely moved across the window).

    Delegates to the shared ``agent_utilities.observability.health.compute_baseline``
    kernel (mapping the host's raw ``avg_temp``/``max_temp``/``avg_fan`` trend keys onto
    the kernel's generic ``value_key``/``peak_key``/``control_key``) when available, and
    translates the generic result back onto this exact dict shape so every caller
    (``derive_policy``, ``kg_ingest.ingest_thermal_baseline``, tests) is unaffected.
    """
    if not _HAS_SHARED_HEALTH:
        return _compute_baseline_local(trends, host=host, min_windows=min_windows)
    normalized = [
        {
            "avg_temp": _g(r, "avgCelsius", "avg_temp"),
            "max_temp": _g(r, "maxCelsius", "max_temp"),
            "avg_fan": _g(r, "avgFan", "avg_fan"),
        }
        for r in trends
    ]
    b = _shared_compute_baseline(
        normalized,
        value_key="avg_temp",
        peak_key="max_temp",
        control_key="avg_fan",
        min_windows=min_windows,
    )
    if b is None:
        return None
    return {
        "host": host,
        "temp_p50": round(b["p50"], 1),
        "temp_p95": round(b["p95"], 1),
        "idle_temp": round(b["min_env"], 1),
        "load_temp": round(b["max_env"], 1),
        "avg_fan": round(b["avg_control"], 1) if b["avg_control"] is not None else None,
        "thermal_inertia": b["inertia"],
        "windows": b["windows"],
    }


# --------------------------------------------------------------------------- #
# Phase 1/3 — derive a recommended policy (bounded by the safety ceiling)      #
# --------------------------------------------------------------------------- #
def derive_policy(
    baseline: dict[str, Any] | None,
    current: dict[str, int] | None = None,
    *,
    ceiling_c: float = DEFAULT_CEILING_C,
    margin_c: float = DEFAULT_MARGIN_C,
    envelope: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Recommend a per-host fan curve from a baseline (CONCEPT:FM-OS.control.policy-derivation).

    Optimizes for *quiet / low power* where a host has thermal headroom and *earlier ramp*
    where it doesn't — while holding two safety invariants: p95 must stay ``margin_c`` below
    ``ceiling_c``, and ``slow`` never drops below :data:`SLOW_FLOOR`. **``warm`` and ``fast``
    (the top of the curve) are never loosened** — only the idle end is tuned.

    ``approved`` is ``False`` (report-only) unless an ``envelope`` is supplied *and* the
    recommendation sits within it of the current curve (Phase 3 bounded auto-approve).
    """
    current = dict(current or DEFAULT_CURVE)
    if not baseline:
        return {
            **current,
            "approved": False,
            "rationale": "insufficient thermal history",
        }

    safe = ceiling_c - margin_c
    p95 = float(baseline["temp_p95"])
    p50 = float(baseline["temp_p50"])

    # Let fans stay slow up to the observed hot ceiling, bounded away from warm and the
    # safety line; a cool host ⇒ higher cold (quieter), a hot host ⇒ lower cold (earlier ramp).
    rec_cold = max(40, min(int(round(p95)), current["warm"] - 10, int(safe) - 5))

    rec_slow = current["slow"]
    if p95 < safe - 10:  # comfortable headroom → ease the floor down
        rec_slow = current["slow"] - 2
    elif p95 > safe:  # tight → lift the base so it never runs hot
        rec_slow = current["slow"] + 3
    rec_slow = max(SLOW_FLOOR, min(rec_slow, current["fast"] - 10))

    rec: dict[str, Any] = {
        "cold": rec_cold,
        "warm": current["warm"],  # untouched — safety
        "slow": rec_slow,
        "fast": current["fast"],  # untouched — safety
        "poll": current["poll"],
    }
    headroom = round(current["warm"] - p95, 1)
    rec["rationale"] = (
        f"p50={p50}°C p95={p95}°C headroom={headroom}°C "
        f"(inertia={baseline.get('thermal_inertia')}) → cold {current['cold']}→{rec_cold}, "
        f"slow {current['slow']}→{rec_slow} (warm/fast held for safety)"
    )
    if envelope:
        within = abs(rec_cold - current["cold"]) <= envelope.get("cold", 5) and abs(
            rec_slow - current["slow"]
        ) <= envelope.get("slow", 5)
        rec["approved"] = bool(within)
    else:
        rec["approved"] = False
    return rec


# --------------------------------------------------------------------------- #
# Phase 3 — anomaly detection + cross-host ambient correlation                 #
# --------------------------------------------------------------------------- #
def _detect_anomaly_local(
    recent: list[dict[str, Any]], baseline: dict[str, Any] | None, *, z_thresh: float
) -> dict[str, Any] | None:
    """Original local implementation (fallback when the shared kernel is absent)."""
    if not baseline or not recent:
        return None
    r_temps = [
        float(v) for r in recent if (v := _g(r, "avgCelsius", "avg_temp")) is not None
    ]
    r_fans = [float(v) for r in recent if (v := _g(r, "avgFan", "avg_fan")) is not None]
    if not r_temps:
        return None
    r_avg = sum(r_temps) / len(r_temps)
    p50, p95 = float(baseline["temp_p50"]), float(baseline["temp_p95"])
    spread = max(p95 - p50, 3.0)
    z = (r_avg - p50) / spread
    kind = None
    if r_avg > p95 and z >= z_thresh:
        kind = "above-baseline"
    elif (
        r_fans
        and (sum(r_fans) / len(r_fans)) >= 95
        and r_avg > float(baseline["load_temp"])
    ):
        kind = "cooling-saturated"
    if not kind:
        return None
    return {
        "kind": kind,
        "zscore": round(z, 2),
        "observed_c": round(r_avg, 1),
        "expected_c": round(p50, 1),
    }


def detect_anomaly(
    recent: list[dict[str, Any]],
    baseline: dict[str, Any] | None,
    *,
    z_thresh: float = 3.0,
) -> dict[str, Any] | None:
    """Flag a host drifting off its own baseline (CONCEPT:FM-OS.control.anomaly-detection).

    ``above-baseline``: the recent window's avg temp is beyond p95 *and* ``z_thresh`` z-scores
    above p50 — the early signal of dust / a failing fan / degraded paste. ``cooling-saturated``:
    fans effectively pinned (≥95%) yet still hotter than the learned load temp. ``None`` when
    the host is behaving normally.

    Delegates to the shared ``agent_utilities.observability.health.detect_anomaly``
    kernel (its generic ``"saturated"`` kind is remapped to this domain's
    ``"cooling-saturated"``) when available.
    """
    if not baseline:
        return None
    if not _HAS_SHARED_HEALTH:
        return _detect_anomaly_local(recent, baseline, z_thresh=z_thresh)
    normalized = [
        {
            "avg_temp": _g(r, "avgCelsius", "avg_temp"),
            "avg_fan": _g(r, "avgFan", "avg_fan"),
        }
        for r in recent
    ]
    shared_baseline = {
        "p50": baseline["temp_p50"],
        "p95": baseline["temp_p95"],
        "max_env": baseline["load_temp"],
    }
    a = _shared_detect_anomaly(
        normalized,
        shared_baseline,
        value_key="avg_temp",
        control_key="avg_fan",
        z_thresh=z_thresh,
        saturated_control=95.0,
    )
    if a is None:
        return None
    return {
        "kind": "cooling-saturated" if a["kind"] == "saturated" else a["kind"],
        "zscore": a["zscore"],
        "observed_c": round(a["observed"], 1),
        "expected_c": round(a["expected"], 1),
    }


def classify_ambient(
    anomalies_by_host: dict[str, dict[str, Any] | None], total_hosts: int
) -> dict[str, dict[str, Any] | None]:
    """Retag simultaneous ``above-baseline`` anomalies as ``ambient`` (CONCEPT:FM-OS.control.ambient-correlation).

    If a majority of hosts spike at once it's the room / rack AC, not N independent faults —
    collapse them to one cause so the loop raises one ``ambient`` signal, not a storm. Mutates
    and returns the mapping.

    Delegates to the shared ``agent_utilities.observability.health.correlate`` kernel
    (this is the ``kind="above-baseline"``, ``systemic_kind="ambient"`` instance of it)
    when available.
    """
    if _HAS_SHARED_HEALTH:
        return _shared_correlate(
            anomalies_by_host,
            total_hosts,
            kind="above-baseline",
            systemic_kind="ambient",
        )
    above = [
        h for h, a in anomalies_by_host.items() if a and a["kind"] == "above-baseline"
    ]
    if len(above) >= max(2, math.ceil(total_hosts / 2)):
        for h in above:
            a = anomalies_by_host[h]
            if a is not None:
                a["kind"] = "ambient"
    return anomalies_by_host


# --------------------------------------------------------------------------- #
# orchestration — one derivation pass over the fleet (report-only by default)  #
# --------------------------------------------------------------------------- #
def _hosts_from_env() -> list[str]:
    raw = os.getenv("FAN_MANAGER_HOSTS", "").strip()
    return [h.strip() for h in raw.split(",") if h.strip()]


def _current_curve() -> dict[str, int]:
    raw = os.getenv("FAN_MANAGER_CURVE", "").strip()
    if raw:
        try:
            return {**DEFAULT_CURVE, **json.loads(raw)}
        except Exception as e:  # noqa: BLE001 — bad override falls back to the shipped curve
            logger.debug("Operation failed: error_type=%s", type(e).__name__)
    return dict(DEFAULT_CURVE)


def _notify(message: str) -> None:
    """Best-effort push to the intelligent alert router (``FAN_MANAGER_NOTIFY_URL``)."""
    logger.info(message)
    try:
        from agent_utilities.core.config import config, setting
        from agent_utilities.protocols.source_connectors.http_safety import (
            safe_post_json,
        )

        url = str(setting("FAN_MANAGER_NOTIFY_URL", "") or "").strip()
        if not url:
            return
        safe_post_json(
            url,
            {"source": "fan-control", "message": message},
            timeout=5,
            max_bytes=64 * 1024,
            max_request_bytes=64 * 1024,
            allowed_private_hosts=config.source_http_allowed_private_hosts,
            tls_service="fan-manager-notify",
        )
    except Exception as exc:  # noqa: BLE001 — notification is best-effort
        logger.debug("Operation failed: error_type=%s", type(exc).__name__)


def run_derivation(
    hosts: list[str] | None = None,
    *,
    days: int = 14,
    apply: bool = False,
    ceiling_c: float = DEFAULT_CEILING_C,
    margin_c: float = DEFAULT_MARGIN_C,
) -> dict[str, Any]:
    """One learn→recommend→flag pass over ``hosts`` (default: ``FAN_MANAGER_HOSTS``).

    Reads each host's recent ``:ThermalTrend`` history, writes a :ThermalBaseline and a
    recommended :FanPolicy (``approved`` only when ``apply`` and within a conservative
    envelope), and mints a :ThermalAnomaly for any host off its baseline — cross-host spikes
    collapsed to a single ``ambient`` cause. Notifies a summary. Returns the per-host result.
    All KG I/O is best-effort: with no reachable engine every host degrades to "no data".
    """
    import asyncio

    from fan_manager import kg_ingest

    hosts = hosts or _hosts_from_env() or [os.getenv("FAN_MANAGER_HOST") or "localhost"]
    current = _current_curve()
    envelope = {"cold": 5, "slow": 5} if apply else None

    results: dict[str, Any] = {}
    anomalies: dict[str, dict[str, Any] | None] = {}
    for host in hosts:
        trends = kg_ingest.read_thermal_trends(host, days=days) or []
        baseline = compute_baseline(trends, host=host)
        anomaly = detect_anomaly(trends[-3:], baseline)
        policy = derive_policy(
            baseline, current, ceiling_c=ceiling_c, margin_c=margin_c, envelope=envelope
        )
        anomalies[host] = anomaly
        results[host] = {"trends": len(trends), "baseline": baseline, "policy": policy}

    classify_ambient(anomalies, len(hosts))

    for host, res in results.items():
        baseline, policy = res["baseline"], res["policy"]
        if baseline:
            asyncio.run(kg_ingest.ingest_thermal_baseline(baseline, host=host))
        asyncio.run(kg_ingest.ingest_fan_policy(policy, host=host))
        anomaly = anomalies.get(host)
        if anomaly:
            asyncio.run(kg_ingest.ingest_thermal_anomaly(anomaly, host=host))
            _notify(
                f"[fan-control] {host}: {anomaly['kind']} — {anomaly['observed_c']}°C "
                f"vs expected {anomaly['expected_c']}°C (z={anomaly['zscore']})"
            )
        res["anomaly"] = anomaly
        verb = "APPROVED" if policy.get("approved") else "recommend"
        logger.info("%s: %s policy — %s", host, verb, policy.get("rationale"))

    return {"hosts": len(hosts), "results": results}


def main() -> None:
    """CLI: run one derivation pass and print a JSON summary (``fan-manager-control``)."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    p = argparse.ArgumentParser(
        description="Epistemic-graph fan-control derivation pass."
    )
    p.add_argument(
        "--days", type=int, default=14, help="trend lookback window (default 14)"
    )
    p.add_argument(
        "--hosts", default="", help="comma-separated hosts (default $FAN_MANAGER_HOSTS)"
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="allow bounded auto-approve of recommendations (default: report-only)",
    )
    p.add_argument("--ceiling", type=float, default=DEFAULT_CEILING_C)
    p.add_argument("--margin", type=float, default=DEFAULT_MARGIN_C)
    args = p.parse_args()
    hosts = [h.strip() for h in args.hosts.split(",") if h.strip()] or None
    summary = run_derivation(
        hosts,
        days=args.days,
        apply=args.apply,
        ceiling_c=args.ceiling,
        margin_c=args.margin,
    )
    print(json.dumps(summary, default=str, indent=2))


if __name__ == "__main__":
    main()
