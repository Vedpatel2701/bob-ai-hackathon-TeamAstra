"""Pydantic schemas for SupplyChainAI API."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DeliveryStatus(str, Enum):
    ON_TIME = "ON_TIME"
    AT_RISK = "AT_RISK"
    DELAYED = "DELAYED"


class VehicleType(str, Enum):
    TRUCK = "TRUCK"
    VAN = "VAN"
    SEMI = "SEMI"
    REFRIGERATED = "REFRIGERATED"


# ── Shipment schemas ──────────────────────────────────────────────────────────

class Shipment(BaseModel):
    shipment_id: str
    vehicle_id: Optional[str] = None
    origin: str
    destination: str
    distance_km: float
    cargo_weight_kg: float
    priority: Priority
    weather_severity: float = Field(ge=0.0, le=1.0)
    traffic_level: float = Field(ge=0.0, le=1.0)
    port_congestion: float = Field(ge=0.0, le=1.0)
    warehouse_delay_hours: float
    supplier_risk: float = Field(ge=0.0, le=1.0)
    vehicle_utilization: float = Field(ge=0.0, le=1.0)
    historical_delay_hours: float
    delivery_deadline_hours: float
    actual_delay_hours: float
    disruption: int  # 0 or 1
    delivery_status: DeliveryStatus
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    disruption_probability: Optional[float] = None
    expected_delay_hours: Optional[float] = None


class ShipmentListResponse(BaseModel):
    total: int
    shipments: list[Shipment]


# ── Prediction schemas ────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    shipment_id: Optional[str] = None
    weather_severity: float = Field(ge=0.0, le=1.0)
    traffic_level: float = Field(ge=0.0, le=1.0)
    port_congestion: float = Field(ge=0.0, le=1.0)
    warehouse_delay_hours: float = Field(ge=0.0)
    supplier_risk: float = Field(ge=0.0, le=1.0)
    vehicle_utilization: float = Field(ge=0.0, le=1.0)
    historical_delay_hours: float = Field(ge=0.0)
    delivery_deadline_hours: float = Field(ge=1.0)
    distance_km: float = Field(ge=0.0)
    cargo_weight_kg: float = Field(ge=0.0)
    priority: Priority = Priority.MEDIUM


class RiskFactor(BaseModel):
    factor: str
    value: float
    contribution: float
    label: str


class PredictResponse(BaseModel):
    shipment_id: Optional[str]
    disruption_probability: float
    expected_delay_hours: float
    risk_score: float
    risk_level: RiskLevel
    risk_factors: list[RiskFactor]
    recommended_action: str


# ── Fleet schemas ─────────────────────────────────────────────────────────────

class Vehicle(BaseModel):
    vehicle_id: str
    vehicle_type: VehicleType
    capacity_kg: float
    current_location: str
    availability: bool
    current_utilization: float = Field(ge=0.0, le=1.0)
    operating_cost_per_km: float
    reliability_score: float = Field(ge=0.0, le=1.0)


class FleetListResponse(BaseModel):
    total: int
    available: int
    vehicles: list[Vehicle]


# ── Optimization schemas ──────────────────────────────────────────────────────

class OptimizeRequest(BaseModel):
    shipment_ids: Optional[list[str]] = None  # None = optimize all


class Assignment(BaseModel):
    shipment_id: str
    vehicle_id: Optional[str] = None
    priority: Priority
    estimated_cost: float
    feasible: bool
    reason: Optional[str] = None


class OptimizeResponse(BaseModel):
    assignments: list[Assignment]
    unassigned_shipments: list[str]
    total_estimated_cost: float
    utilization_before: float
    utilization_after: float
    high_risk_reduced: int
    solver_status: str
    optimization_time_ms: float


# ── Simulation schemas ────────────────────────────────────────────────────────

class SimulateRequest(BaseModel):
    weather_severity_delta: float = Field(default=0.0, ge=-1.0, le=1.0)
    traffic_level_delta: float = Field(default=0.0, ge=-1.0, le=1.0)
    port_congestion_delta: float = Field(default=0.0, ge=-1.0, le=1.0)
    vehicle_unavailable_ids: list[str] = Field(default_factory=list)
    apply_to_shipment_ids: Optional[list[str]] = None  # None = apply globally


class ScenarioMetrics(BaseModel):
    disruption_probability_avg: float
    expected_delay_avg_hours: float
    high_risk_count: int
    critical_risk_count: int
    estimated_fleet_cost: float
    fleet_utilization_avg: float


class SimulateResponse(BaseModel):
    current: ScenarioMetrics
    simulated: ScenarioMetrics
    delta: dict[str, float]
    affected_shipments: int
    simulation_label: str


# ── Copilot schemas ───────────────────────────────────────────────────────────

class CopilotRequest(BaseModel):
    message: str
    context: Optional[dict[str, Any]] = None


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    result_summary: str


class CopilotResponse(BaseModel):
    answer: str
    tools_used: list[ToolCall]
    sources: list[str]
    confidence: float


# ── Metrics schemas ───────────────────────────────────────────────────────────

class KPIMetrics(BaseModel):
    total_shipments: int
    high_risk_count: int
    critical_risk_count: int
    on_time_rate: float
    fleet_utilization_avg: float
    avg_disruption_probability: float
    avg_expected_delay_hours: float
    disrupted_count: int
    at_risk_count: int


class RiskDistributionItem(BaseModel):
    risk_level: RiskLevel
    count: int
    percentage: float


class DelayTrendItem(BaseModel):
    label: str
    avg_delay_hours: float
    disruption_rate: float


class RegionRiskItem(BaseModel):
    region: str
    avg_risk_score: float
    shipment_count: int


class MetricsResponse(BaseModel):
    kpis: KPIMetrics
    risk_distribution: list[RiskDistributionItem]
    delay_trend: list[DelayTrendItem]
    region_risk: list[RegionRiskItem]
