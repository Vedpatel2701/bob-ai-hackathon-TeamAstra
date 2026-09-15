"""Prediction API routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from schemas.models import PredictRequest, PredictResponse, RiskFactor, RiskLevel
from services.data_service import DataService
from services.ml_service import MLService
from services.risk_engine import compute_risk_score

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest) -> PredictResponse:
    features = request.model_dump()

    # If shipment_id provided, merge stored data as defaults
    if request.shipment_id:
        stored = DataService.get_shipment_by_id(request.shipment_id)
        if stored:
            for k, v in stored.items():
                if k not in features or features[k] is None:
                    features[k] = v

    try:
        pred = MLService.predict(features)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=503, detail=f"ML service error: {str(e)}")

    risk_result = compute_risk_score(
        disruption_probability=pred["disruption_probability"],
        weather_severity=float(features.get("weather_severity", 0)),
        traffic_level=float(features.get("traffic_level", 0)),
        port_congestion=float(features.get("port_congestion", 0)),
        warehouse_delay_hours=float(features.get("warehouse_delay_hours", 0)),
        supplier_risk=float(features.get("supplier_risk", 0)),
        vehicle_utilization=float(features.get("vehicle_utilization", 0.5)),
        priority=str(features.get("priority", "MEDIUM")),
        delivery_deadline_hours=float(features.get("delivery_deadline_hours", 48)),
        expected_delay_hours=pred["expected_delay_hours"],
    )

    risk_factors = [
        RiskFactor(
            factor=f["factor"],
            value=f["value"],
            contribution=f["contribution"],
            label=f["label"],
        )
        for f in pred.get("shap_factors", [])[:8]
    ]

    return PredictResponse(
        shipment_id=request.shipment_id,
        disruption_probability=pred["disruption_probability"],
        expected_delay_hours=pred["expected_delay_hours"],
        risk_score=risk_result["risk_score"],
        risk_level=RiskLevel(risk_result["risk_level"]),
        risk_factors=risk_factors,
        recommended_action=risk_result["recommended_action"],
    )
