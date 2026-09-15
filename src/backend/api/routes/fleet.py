"""Fleet API routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from schemas.models import FleetListResponse, Vehicle, VehicleType
from services.data_service import DataService

router = APIRouter()


@router.get("/fleet", response_model=FleetListResponse)
async def get_fleet(
    available_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
) -> FleetListResponse:
    df = DataService.get_fleet()
    if available_only:
        df = df[df["availability"] == True]

    total = len(DataService.get_fleet())
    available_count = int(DataService.get_fleet()["availability"].sum())

    vehicles = []
    for _, row in df.head(limit).iterrows():
        availability = bool(row.get("availability", False))
        vtype = str(row.get("vehicle_type", "TRUCK")).upper()
        if vtype not in ("TRUCK", "VAN", "SEMI", "REFRIGERATED"):
            vtype = "TRUCK"
        vehicles.append(Vehicle(
            vehicle_id=str(row.get("vehicle_id", "")),
            vehicle_type=VehicleType(vtype),
            capacity_kg=float(row.get("capacity_kg", 0)),
            current_location=str(row.get("current_location", "")),
            availability=availability,
            current_utilization=float(row.get("current_utilization", 0)),
            operating_cost_per_km=float(row.get("operating_cost_per_km", 0)),
            reliability_score=float(row.get("reliability_score", 0)),
        ))

    return FleetListResponse(
        total=total,
        available=available_count,
        vehicles=vehicles,
    )


@router.get("/fleet/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    row = DataService.get_vehicle_by_id(vehicle_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
    return row
