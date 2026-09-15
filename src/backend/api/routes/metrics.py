"""Metrics/KPI API routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter

from schemas.models import (
    MetricsResponse, KPIMetrics, RiskDistributionItem,
    DelayTrendItem, RegionRiskItem, RiskLevel,
)
from services.data_service import DataService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """Return KPIs and chart data — fully precomputed from risk cache."""
    df = DataService.get_shipments()
    fleet_df = DataService.get_fleet()
    risk_cache = DataService.get_all_risk()

    # Aggregate from cache — O(n) dict lookups, no ML calls
    probs, delays, scores, risk_levels = [], [], [], []
    for _, row in df.iterrows():
        sid = str(row.get("shipment_id", ""))
        r = risk_cache.get(sid)
        if r:
            probs.append(r["disruption_probability"])
            delays.append(r["expected_delay_hours"])
            scores.append(r["risk_score"])
            risk_levels.append(r["risk_level"])
        else:
            probs.append(0.0)
            delays.append(0.0)
            scores.append(0.0)
            risk_levels.append("LOW")

    n = max(len(df), 1)
    high_risk = sum(1 for r in risk_levels if r in ("HIGH", "CRITICAL"))
    critical_risk = sum(1 for r in risk_levels if r == "CRITICAL")
    on_time = int((df["delivery_status"] == "ON_TIME").sum())
    disrupted = int(df["disruption"].sum())
    at_risk = int((df["delivery_status"] == "AT_RISK").sum())
    fleet_util = float(fleet_df["current_utilization"].mean()) if len(fleet_df) > 0 else 0.0

    kpis = KPIMetrics(
        total_shipments=n,
        high_risk_count=high_risk,
        critical_risk_count=critical_risk,
        on_time_rate=round(on_time / n, 4),
        fleet_utilization_avg=round(fleet_util, 4),
        avg_disruption_probability=round(sum(probs) / n, 4),
        avg_expected_delay_hours=round(sum(delays) / n, 4),
        disrupted_count=disrupted,
        at_risk_count=at_risk,
    )

    # Risk distribution
    level_counts = {level: risk_levels.count(level) for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")}
    risk_distribution = [
        RiskDistributionItem(
            risk_level=RiskLevel(level),
            count=count,
            percentage=round(count / n * 100, 1),
        )
        for level, count in level_counts.items()
    ]

    # Delay and region metrics — group by origin
    import pandas as pd
    df_copy = df.copy()
    df_copy["_prob"] = probs
    df_copy["_delay"] = delays
    df_copy["_score"] = scores
    region_groups = df_copy.groupby("origin").agg(
        avg_delay=("_delay", "mean"),
        disruption_rate=("disruption", "mean"),
        count=("shipment_id", "count"),
        avg_score=("_score", "mean"),
    ).reset_index().sort_values("count", ascending=False)

    delay_trend = [
        DelayTrendItem(
            label=str(row["origin"]),
            avg_delay_hours=round(float(row["avg_delay"]), 2),
            disruption_rate=round(float(row["disruption_rate"]), 4),
        )
        for _, row in region_groups.head(10).iterrows()
    ]

    region_risk = [
        RegionRiskItem(
            region=str(row["origin"]),
            avg_risk_score=round(float(row["avg_score"]), 4),
            shipment_count=int(row["count"]),
        )
        for _, row in region_groups.head(10).iterrows()
    ]

    return MetricsResponse(
        kpis=kpis,
        risk_distribution=risk_distribution,
        delay_trend=delay_trend,
        region_risk=region_risk,
    )
