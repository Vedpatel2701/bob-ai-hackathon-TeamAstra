"""Fleet optimization API routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from schemas.models import OptimizeRequest, OptimizeResponse, Assignment, Priority
from services.data_service import DataService
from optimization.fleet_optimizer import optimize_fleet

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize(request: OptimizeRequest) -> OptimizeResponse:
    shipments_df = DataService.get_shipments()
    fleet_df = DataService.get_fleet()

    shipments = shipments_df.to_dict(orient="records")
    fleet = fleet_df.to_dict(orient="records")

    if request.shipment_ids:
        shipments = [s for s in shipments if s["shipment_id"] in request.shipment_ids]

    if not shipments:
        raise HTTPException(status_code=400, detail="No shipments to optimize")

    try:
        result = optimize_fleet(shipments, fleet)
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise HTTPException(status_code=503, detail=f"Optimization error: {str(e)}")

    assignments = [
        Assignment(
            shipment_id=a["shipment_id"],
            vehicle_id=a.get("vehicle_id") or None,
            priority=Priority(str(a.get("priority", "MEDIUM")).upper()),
            estimated_cost=float(a.get("estimated_cost", 0)),
            feasible=bool(a.get("feasible", False)),
            reason=a.get("reason"),
        )
        for a in result["assignments"]
    ]

    return OptimizeResponse(
        assignments=assignments,
        unassigned_shipments=result["unassigned_shipments"],
        total_estimated_cost=result["total_estimated_cost"],
        utilization_before=result["utilization_before"],
        utilization_after=result["utilization_after"],
        high_risk_reduced=result["high_risk_reduced"],
        solver_status=result["solver_status"],
        optimization_time_ms=result["optimization_time_ms"],
    )
