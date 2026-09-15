"""Shipments API routes."""
from __future__ import annotations

import logging
import math
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from schemas.models import (
    Shipment, ShipmentListResponse, Priority, RiskLevel, DeliveryStatus,
)
from services.data_service import DataService
from services.ml_service import MLService
from services.risk_engine import compute_risk_score

logger = logging.getLogger(__name__)
router = APIRouter()

_VALID_STATUSES = {"ON_TIME", "AT_RISK", "DELAYED"}


def _nan_to_none(v):
    """Return None if v is NaN (pandas float NaN), else v."""
    if v is None:
        return None
    try:
        if isinstance(v, float) and math.isnan(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def _row_to_shipment(row: dict, risk: Optional[dict]) -> Shipment:
    """Build a Shipment Pydantic model from a raw CSV row + cached risk."""
    status = str(row.get("delivery_status", "ON_TIME"))
    if status not in _VALID_STATUSES:
        status = "ON_TIME"

    vid = _nan_to_none(row.get("vehicle_id"))
    vid = str(vid) if vid is not None else None

    return Shipment(
        shipment_id=str(row.get("shipment_id", "")),
        vehicle_id=vid,
        origin=str(row.get("origin", "")),
        destination=str(row.get("destination", "")),
        distance_km=float(row.get("distance_km", 0)),
        cargo_weight_kg=float(row.get("cargo_weight_kg", 0)),
        priority=Priority(str(row.get("priority", "MEDIUM")).upper()),
        weather_severity=float(row.get("weather_severity", 0)),
        traffic_level=float(row.get("traffic_level", 0)),
        port_congestion=float(row.get("port_congestion", 0)),
        warehouse_delay_hours=float(row.get("warehouse_delay_hours", 0)),
        supplier_risk=float(row.get("supplier_risk", 0)),
        vehicle_utilization=float(row.get("vehicle_utilization", 0.5)),
        historical_delay_hours=float(row.get("historical_delay_hours", 0)),
        delivery_deadline_hours=float(row.get("delivery_deadline_hours", 48)),
        actual_delay_hours=float(row.get("actual_delay_hours", 0)),
        disruption=int(row.get("disruption", 0)),
        delivery_status=DeliveryStatus(status),
        risk_score=risk["risk_score"] if risk else None,
        risk_level=RiskLevel(risk["risk_level"]) if risk else None,
        disruption_probability=risk["disruption_probability"] if risk else None,
        expected_delay_hours=risk["expected_delay_hours"] if risk else None,
    )


# NOTE: /shipments/high-risk MUST be registered before /shipments/{shipment_id}
# to prevent FastAPI matching "high-risk" as a shipment_id.

@router.get("/shipments/high-risk")
async def get_high_risk_shipments(limit: int = Query(default=20, ge=1, le=100)):
    """Return high/critical risk shipments sorted by risk score — uses cache."""
    df = DataService.get_shipments()
    risk_cache = DataService.get_all_risk()

    results = []
    for _, row in df.iterrows():
        sid = str(row.get("shipment_id", ""))
        risk = risk_cache.get(sid)
        if risk and risk["risk_level"] in ("HIGH", "CRITICAL"):
            results.append({**row.to_dict(), **risk})

    results.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    # Sanitize NaN vehicle_id before returning
    for r in results:
        if isinstance(r.get("vehicle_id"), float) and math.isnan(r["vehicle_id"]):
            r["vehicle_id"] = None
    return {"total": len(results), "shipments": results[:limit]}


@router.get("/shipments", response_model=ShipmentListResponse)
async def get_shipments(
    limit: int = Query(default=50, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    priority: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
) -> ShipmentListResponse:
    """Return paginated shipment list with precomputed risk — uses cache."""
    df = DataService.get_shipments()
    risk_cache = DataService.get_all_risk()

    if priority:
        df = df[df["priority"] == priority.upper()]

    # Filter by risk_level using cache (no ML calls needed)
    if risk_level:
        rl = risk_level.upper()
        keep = {sid for sid, r in risk_cache.items() if r["risk_level"] == rl}
        df = df[df["shipment_id"].astype(str).isin(keep)]

    total = len(df)
    page = df.iloc[offset: offset + limit]

    shipments = []
    for _, row in page.iterrows():
        sid = str(row.get("shipment_id", ""))
        risk = risk_cache.get(sid)
        shipments.append(_row_to_shipment(row.to_dict(), risk))

    return ShipmentListResponse(total=total, shipments=shipments)


@router.get("/shipments/{shipment_id}")
async def get_shipment(shipment_id: str):
    """Return single shipment with cached risk data."""
    row = DataService.get_shipment_by_id(shipment_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Shipment {shipment_id} not found")
    risk = DataService.get_risk(shipment_id)
    # Sanitize vehicle_id
    if isinstance(row.get("vehicle_id"), float) and math.isnan(row["vehicle_id"]):
        row["vehicle_id"] = None
    return {**row, **(risk or {})}
