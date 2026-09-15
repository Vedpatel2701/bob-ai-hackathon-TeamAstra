"""What-if simulation API routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from schemas.models import SimulateRequest, SimulateResponse, ScenarioMetrics
from services.data_service import DataService
from services.ml_service import MLService
from services.risk_engine import compute_risk_score
from services.simulation_service import run_simulation

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(request: SimulateRequest) -> SimulateResponse:
    shipments = DataService.get_shipments().to_dict(orient="records")
    fleet = DataService.get_fleet().to_dict(orient="records")

    try:
        result = run_simulation(
            shipments=shipments,
            fleet=fleet,
            ml_service=MLService,
            risk_engine_fn=compute_risk_score,
            weather_severity_delta=request.weather_severity_delta,
            traffic_level_delta=request.traffic_level_delta,
            port_congestion_delta=request.port_congestion_delta,
            vehicle_unavailable_ids=request.vehicle_unavailable_ids,
            apply_to_shipment_ids=request.apply_to_shipment_ids,
        )
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=503, detail=f"Simulation error: {str(e)}")

    return SimulateResponse(
        current=ScenarioMetrics(**result["current"]),
        simulated=ScenarioMetrics(**result["simulated"]),
        delta=result["delta"],
        affected_shipments=result["affected_shipments"],
        simulation_label=result["simulation_label"],
    )
