"""Risk scoring engine — deterministic, transparent, configurable."""
from __future__ import annotations

from typing import Optional

PRIORITY_WEIGHT = {"LOW": 0.8, "MEDIUM": 1.0, "HIGH": 1.3, "CRITICAL": 1.6}
RISK_THRESHOLDS = {"LOW": 0.30, "MEDIUM": 0.55, "HIGH": 0.75, "CRITICAL": 1.01}

RECOMMENDED_ACTIONS = {
    "LOW": "Monitor shipment status. No immediate action required.",
    "MEDIUM": (
        "Review shipment conditions. Consider contingency routing if conditions worsen. "
        "Notify the assigned driver of potential delays."
    ),
    "HIGH": (
        "Escalate to operations supervisor. Evaluate alternative vehicle or route. "
        "Contact warehouse and supplier for status updates. Prepare customer notification."
    ),
    "CRITICAL": (
        "Immediate intervention required. Reassign to highest-availability vehicle. "
        "Activate disruption playbook. Notify customer and management. "
        "Consider emergency routing or partial delivery."
    ),
}


def compute_risk_score(
    disruption_probability: float,
    weather_severity: float = 0.0,
    traffic_level: float = 0.0,
    port_congestion: float = 0.0,
    warehouse_delay_hours: float = 0.0,
    supplier_risk: float = 0.0,
    vehicle_utilization: float = 0.5,
    priority: str = "MEDIUM",
    delivery_deadline_hours: float = 48.0,
    expected_delay_hours: float = 0.0,
) -> dict:
    """
    Compute a composite risk score combining ML probability with
    operational context. Returns score, level, and recommended action.
    """
    # Deadline pressure: 0 = no pressure, 1 = critical pressure
    deadline_pressure = max(0.0, 1.0 - delivery_deadline_hours / 72.0)

    # Operational severity score (0-1)
    ops_score = (
        0.30 * disruption_probability
        + 0.15 * weather_severity
        + 0.12 * traffic_level
        + 0.12 * port_congestion
        + 0.08 * min(warehouse_delay_hours / 10.0, 1.0)
        + 0.10 * supplier_risk
        + 0.05 * vehicle_utilization
        + 0.08 * deadline_pressure
    )

    # Priority multiplier
    p_weight = PRIORITY_WEIGHT.get(str(priority).upper(), 1.0)
    risk_score = float(min(ops_score * p_weight, 1.0))

    # Determine risk level
    if risk_score < RISK_THRESHOLDS["LOW"]:
        risk_level = "LOW"
    elif risk_score < RISK_THRESHOLDS["MEDIUM"]:
        risk_level = "MEDIUM"
    elif risk_score < RISK_THRESHOLDS["HIGH"]:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    recommended_action = RECOMMENDED_ACTIONS[risk_level]

    return {
        "risk_score": round(risk_score, 4),
        "risk_level": risk_level,
        "recommended_action": recommended_action,
        "components": {
            "disruption_probability": round(disruption_probability, 4),
            "operational_severity": round(ops_score, 4),
            "priority_weight": p_weight,
            "deadline_pressure": round(deadline_pressure, 4),
        },
    }
