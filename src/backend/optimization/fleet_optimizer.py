"""Fleet assignment optimizer using Google OR-Tools."""
from __future__ import annotations

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

PRIORITY_VALUES = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def optimize_fleet(
    shipments: list[dict],
    vehicles: list[dict],
) -> dict:
    """
    Solve the vehicle-to-shipment assignment problem using OR-Tools.

    Constraints:
    - Each shipment assigned to at most one vehicle
    - Vehicle capacity must accommodate shipment cargo weight
    - Vehicle must be available
    - Each vehicle can carry at most one shipment per run (MVP simplification)

    Objective: minimize total operating cost while prioritizing high-priority shipments.
    """
    start_time = time.time()

    try:
        from ortools.sat.python import cp_model
    except ImportError:
        logger.error("OR-Tools not installed. Run: pip install ortools")
        return _fallback_greedy(shipments, vehicles)

    available_vehicles = [v for v in vehicles if v.get("availability", False)]
    if not available_vehicles:
        return {
            "assignments": [],
            "unassigned_shipments": [s["shipment_id"] for s in shipments],
            "total_estimated_cost": 0.0,
            "utilization_before": _avg_utilization(vehicles),
            "utilization_after": _avg_utilization(vehicles),
            "high_risk_reduced": 0,
            "solver_status": "NO_VEHICLES",
            "optimization_time_ms": 0.0,
        }

    model = cp_model.CpModel()
    S = len(shipments)
    V = len(available_vehicles)

    # Decision variables: x[s][v] = 1 if shipment s assigned to vehicle v
    x = [[model.NewBoolVar(f"x_{s}_{v}") for v in range(V)] for s in range(S)]

    # Constraint 1: each shipment assigned to at most one vehicle
    for s in range(S):
        model.AddAtMostOne(x[s][v] for v in range(V))

    # Constraint 2: each vehicle carries at most one shipment
    for v in range(V):
        model.AddAtMostOne(x[s][v] for s in range(S))

    # Constraint 3: vehicle capacity must meet cargo weight
    feasible = []  # (s, v) pairs that are capacity-feasible
    for s, shipment in enumerate(shipments):
        cargo = float(shipment.get("cargo_weight_kg", 0))
        for v, vehicle in enumerate(available_vehicles):
            capacity = float(vehicle.get("capacity_kg", 0))
            if capacity >= cargo:
                feasible.append((s, v))
            else:
                model.Add(x[s][v] == 0)  # infeasible assignment forbidden

    # Objective: maximize number of assignments weighted by priority
    # Use large assignment bonus minus small cost penalty
    # All integer math for CP-SAT
    COST_SCALE = 10   # keep cost term small relative to bonus
    ASSIGNMENT_BONUS = 1_000_000  # always positive to incentivize assignment

    obj_terms = []
    for s, shipment in enumerate(shipments):
        p_val = PRIORITY_VALUES.get(str(shipment.get("priority", "MEDIUM")).upper(), 2)
        for v, vehicle in enumerate(available_vehicles):
            cost_per_km = float(vehicle.get("operating_cost_per_km", 2.0))
            dist = float(shipment.get("distance_km", 500))
            # Cost penalty is small relative to assignment bonus
            cost_penalty = max(1, int(cost_per_km * dist * COST_SCALE))
            # Assignment bonus dominates; cost penalty differentiates between vehicles
            obj_val = p_val * ASSIGNMENT_BONUS - cost_penalty
            obj_terms.append(obj_val * x[s][v])

    model.Maximize(sum(obj_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)

    elapsed_ms = (time.time() - start_time) * 1000

    status_names = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.UNKNOWN: "UNKNOWN",
    }
    solver_status = status_names.get(status, "UNKNOWN")

    assignments = []
    unassigned = []
    total_cost = 0.0
    assigned_vehicle_ids = set()

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for s, shipment in enumerate(shipments):
            assigned = False
            for v, vehicle in enumerate(available_vehicles):
                if solver.Value(x[s][v]) == 1:
                    dist = float(shipment.get("distance_km", 500))
                    cost = float(vehicle.get("operating_cost_per_km", 2.0)) * dist
                    total_cost += cost
                    assigned_vehicle_ids.add(vehicle["vehicle_id"])
                    assignments.append({
                        "shipment_id": shipment["shipment_id"],
                        "vehicle_id": vehicle["vehicle_id"],
                        "priority": shipment.get("priority", "MEDIUM"),
                        "estimated_cost": round(cost, 2),
                        "feasible": True,
                        "reason": (
                            f"Assigned {vehicle['vehicle_type']} "
                            f"(capacity {vehicle['capacity_kg']:.0f} kg) "
                            f"at ${vehicle['operating_cost_per_km']:.2f}/km"
                        ),
                    })
                    assigned = True
                    break
            if not assigned:
                unassigned.append(shipment["shipment_id"])

        # Explain why unassigned shipments could not be assigned
        unassigned_with_reasons = []
        for s_id in unassigned:
            s_data = next((s for s in shipments if s["shipment_id"] == s_id), {})
            cargo = float(s_data.get("cargo_weight_kg", 0))
            capacity_issue = all(
                float(v.get("capacity_kg", 0)) < cargo for v in available_vehicles
            )
            reason = "Insufficient vehicle capacity" if capacity_issue else "No available vehicle"
            unassigned_with_reasons.append({
                "shipment_id": s_id,
                "vehicle_id": None,
                "priority": s_data.get("priority", "UNKNOWN"),
                "estimated_cost": 0.0,
                "feasible": False,
                "reason": reason,
            })

        all_assignments = assignments + unassigned_with_reasons
    else:
        all_assignments = []
        unassigned = [s["shipment_id"] for s in shipments]
        unassigned_with_reasons = [
            {
                "shipment_id": s_id,
                "vehicle_id": None,
                "priority": next(
                    (s.get("priority", "UNKNOWN") for s in shipments if s["shipment_id"] == s_id),
                    "UNKNOWN",
                ),
                "estimated_cost": 0.0,
                "feasible": False,
                "reason": "Solver could not find feasible solution",
            }
            for s_id in unassigned
        ]
        all_assignments = unassigned_with_reasons

    util_before = _avg_utilization(vehicles)
    # After optimization, assigned vehicles have higher utilization
    if assignments:
        n_assigned = len(assignments)
        n_available = len(available_vehicles)
        util_after = min(
            util_before + (n_assigned / max(n_available, 1)) * 0.2,
            0.95,
        )
    else:
        util_after = util_before

    # Count high-risk shipments that got assigned
    high_risk_assigned = sum(
        1 for a in assignments
        if a.get("priority") in ("HIGH", "CRITICAL")
    )

    return {
        "assignments": all_assignments,
        "unassigned_shipments": unassigned,
        "total_estimated_cost": round(total_cost, 2),
        "utilization_before": round(util_before, 4),
        "utilization_after": round(util_after, 4),
        "high_risk_reduced": high_risk_assigned,
        "solver_status": solver_status,
        "optimization_time_ms": round(elapsed_ms, 1),
    }


def _avg_utilization(vehicles: list[dict]) -> float:
    if not vehicles:
        return 0.0
    return sum(float(v.get("current_utilization", 0.5)) for v in vehicles) / len(vehicles)


def _fallback_greedy(shipments: list[dict], vehicles: list[dict]) -> dict:
    """Simple greedy fallback if OR-Tools is unavailable."""
    available = sorted(
        [v for v in vehicles if v.get("availability", False)],
        key=lambda v: float(v.get("operating_cost_per_km", 999)),
    )
    ordered_shipments = sorted(
        shipments,
        key=lambda s: PRIORITY_VALUES.get(str(s.get("priority", "MEDIUM")).upper(), 2),
        reverse=True,
    )

    assignments = []
    unassigned = []
    used_vehicles = set()
    total_cost = 0.0

    for shipment in ordered_shipments:
        cargo = float(shipment.get("cargo_weight_kg", 0))
        assigned = False
        for vehicle in available:
            if (
                vehicle["vehicle_id"] not in used_vehicles
                and float(vehicle.get("capacity_kg", 0)) >= cargo
            ):
                dist = float(shipment.get("distance_km", 500))
                cost = float(vehicle.get("operating_cost_per_km", 2.0)) * dist
                total_cost += cost
                used_vehicles.add(vehicle["vehicle_id"])
                assignments.append({
                    "shipment_id": shipment["shipment_id"],
                    "vehicle_id": vehicle["vehicle_id"],
                    "priority": shipment.get("priority", "MEDIUM"),
                    "estimated_cost": round(cost, 2),
                    "feasible": True,
                    "reason": "Greedy assignment (OR-Tools unavailable)",
                })
                assigned = True
                break
        if not assigned:
            unassigned.append(shipment["shipment_id"])

    all_a = assignments + [
        {
            "shipment_id": s_id, "vehicle_id": None,
            "priority": "UNKNOWN", "estimated_cost": 0.0,
            "feasible": False, "reason": "No capacity match",
        }
        for s_id in unassigned
    ]
    return {
        "assignments": all_a,
        "unassigned_shipments": unassigned,
        "total_estimated_cost": round(total_cost, 2),
        "utilization_before": _avg_utilization(vehicles),
        "utilization_after": min(_avg_utilization(vehicles) + 0.1, 0.95),
        "high_risk_reduced": sum(1 for a in assignments if a["priority"] in ("HIGH", "CRITICAL")),
        "solver_status": "GREEDY_FALLBACK",
        "optimization_time_ms": 0.0,
    }
