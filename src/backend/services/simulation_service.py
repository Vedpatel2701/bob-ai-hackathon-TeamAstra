"""What-if simulation engine."""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def run_simulation(
    shipments: list[dict],
    fleet: list[dict],
    ml_service,
    risk_engine_fn,
    weather_severity_delta: float = 0.0,
    traffic_level_delta: float = 0.0,
    port_congestion_delta: float = 0.0,
    vehicle_unavailable_ids: Optional[list[str]] = None,
    apply_to_shipment_ids: Optional[list[str]] = None,
) -> dict:
    """
    Run a what-if simulation by modifying operational parameters and
    re-computing risk metrics. Returns current vs simulated comparison.
    """
    unavailable = set(vehicle_unavailable_ids or [])
    apply_ids = set(apply_to_shipment_ids) if apply_to_shipment_ids else None

    def _clamp(v: float) -> float:
        return max(0.0, min(1.0, v))

    # ── Current state metrics ──────────────────────────────────────────────────
    current_metrics = _compute_aggregate_metrics(
        shipments, fleet, ml_service, risk_engine_fn, {}, set()
    )

    # ── Simulated state metrics ────────────────────────────────────────────────
    simulated_metrics = _compute_aggregate_metrics(
        shipments,
        fleet,
        ml_service,
        risk_engine_fn,
        {
            "weather_severity_delta": weather_severity_delta,
            "traffic_level_delta": traffic_level_delta,
            "port_congestion_delta": port_congestion_delta,
        },
        unavailable,
        apply_to=apply_ids,
    )

    # ── Delta ──────────────────────────────────────────────────────────────────
    delta = {
        "disruption_probability_avg": round(
            simulated_metrics["disruption_probability_avg"]
            - current_metrics["disruption_probability_avg"], 4
        ),
        "expected_delay_avg_hours": round(
            simulated_metrics["expected_delay_avg_hours"]
            - current_metrics["expected_delay_avg_hours"], 4
        ),
        "high_risk_count": float(
            simulated_metrics["high_risk_count"] - current_metrics["high_risk_count"]
        ),
        "critical_risk_count": float(
            simulated_metrics["critical_risk_count"] - current_metrics["critical_risk_count"]
        ),
        "estimated_fleet_cost": round(
            simulated_metrics["estimated_fleet_cost"]
            - current_metrics["estimated_fleet_cost"], 2
        ),
        "fleet_utilization_avg": round(
            simulated_metrics["fleet_utilization_avg"]
            - current_metrics["fleet_utilization_avg"], 4
        ),
    }

    affected = len(apply_ids) if apply_ids else len(shipments)

    # Build simulation label
    parts = []
    if weather_severity_delta != 0:
        parts.append(f"weather {'increased' if weather_severity_delta > 0 else 'decreased'} by {abs(weather_severity_delta):.0%}")
    if traffic_level_delta != 0:
        parts.append(f"traffic {'increased' if traffic_level_delta > 0 else 'decreased'} by {abs(traffic_level_delta):.0%}")
    if port_congestion_delta != 0:
        parts.append(f"port congestion {'increased' if port_congestion_delta > 0 else 'decreased'} by {abs(port_congestion_delta):.0%}")
    if unavailable:
        parts.append(f"{len(unavailable)} vehicle(s) removed ({', '.join(sorted(unavailable)[:3])})")
    label = "Scenario: " + ("; ".join(parts) if parts else "no changes")

    return {
        "current": current_metrics,
        "simulated": simulated_metrics,
        "delta": delta,
        "affected_shipments": affected,
        "simulation_label": label,
    }


def _compute_aggregate_metrics(
    shipments: list[dict],
    fleet: list[dict],
    ml_service,
    risk_engine_fn,
    deltas: dict,
    unavailable: set,
    apply_to: Optional[set] = None,
) -> dict:
    w_delta = deltas.get("weather_severity_delta", 0.0)
    t_delta = deltas.get("traffic_level_delta", 0.0)
    p_delta = deltas.get("port_congestion_delta", 0.0)

    def _clamp(v: float) -> float:
        return max(0.0, min(1.0, v))

    # Build modified feature rows for batch prediction
    feature_rows = []
    for s in shipments:
        sid = s.get("shipment_id", "")
        should_modify = apply_to is None or sid in apply_to
        feature_rows.append({
            "weather_severity": _clamp(float(s.get("weather_severity", 0)) + (w_delta if should_modify else 0)),
            "traffic_level": _clamp(float(s.get("traffic_level", 0)) + (t_delta if should_modify else 0)),
            "port_congestion": _clamp(float(s.get("port_congestion", 0)) + (p_delta if should_modify else 0)),
            "warehouse_delay_hours": float(s.get("warehouse_delay_hours", 0)),
            "supplier_risk": float(s.get("supplier_risk", 0)),
            "vehicle_utilization": float(s.get("vehicle_utilization", 0.5)),
            "historical_delay_hours": float(s.get("historical_delay_hours", 0)),
            "delivery_deadline_hours": float(s.get("delivery_deadline_hours", 48)),
            "distance_km": float(s.get("distance_km", 500)),
            "cargo_weight_kg": float(s.get("cargo_weight_kg", 5000)),
            "priority": str(s.get("priority", "MEDIUM")),
        })

    # Batch prediction — one vectorized call instead of N individual calls
    try:
        batch_preds = ml_service.predict_batch(feature_rows)
    except Exception:
        batch_preds = [
            {"disruption_probability": float(s.get("disruption", 0)), "expected_delay_hours": float(s.get("actual_delay_hours", 0))}
            for s in shipments
        ]

    probs = []
    delays = []
    risk_scores = []
    for features, pred in zip(feature_rows, batch_preds):
        prob = pred["disruption_probability"]
        delay = pred["expected_delay_hours"]
        risk_result = risk_engine_fn(
            disruption_probability=prob,
            weather_severity=features["weather_severity"],
            traffic_level=features["traffic_level"],
            port_congestion=features["port_congestion"],
            warehouse_delay_hours=features["warehouse_delay_hours"],
            supplier_risk=features["supplier_risk"],
            vehicle_utilization=features["vehicle_utilization"],
            priority=features["priority"],
            delivery_deadline_hours=features["delivery_deadline_hours"],
        )
        probs.append(prob)
        delays.append(delay)
        risk_scores.append(risk_result["risk_score"])

    n = max(len(shipments), 1)

    # Fleet metrics
    modified_fleet = [
        v for v in fleet if v.get("vehicle_id") not in unavailable
    ]
    util_avg = (
        sum(float(v.get("current_utilization", 0.5)) for v in modified_fleet)
        / max(len(modified_fleet), 1)
    )
    est_cost = sum(
        float(v.get("operating_cost_per_km", 2.0)) * 500  # avg 500 km
        for v in modified_fleet
        if v.get("availability", False)
    )

    high_risk_count = sum(1 for r in risk_scores if r >= 0.55)
    critical_risk_count = sum(1 for r in risk_scores if r >= 0.75)

    return {
        "disruption_probability_avg": round(sum(probs) / n, 4),
        "expected_delay_avg_hours": round(sum(delays) / n, 4),
        "high_risk_count": high_risk_count,
        "critical_risk_count": critical_risk_count,
        "estimated_fleet_cost": round(est_cost, 2),
        "fleet_utilization_avg": round(util_avg, 4),
    }
