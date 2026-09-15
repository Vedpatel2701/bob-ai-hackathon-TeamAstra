"""Data service — loads, caches, and enriches shipment and fleet data."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = _BACKEND_DIR.parents[1]
_env_data_path = os.getenv("DATA_PATH", "")
_DATA_DIR = Path(_env_data_path) if _env_data_path else (_PROJECT_ROOT / "src" / "ml" / "data")

PRIORITY_MAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


class DataService:
    _shipments_df: Optional[pd.DataFrame] = None
    _fleet_df: Optional[pd.DataFrame] = None
    # Precomputed risk cache: shipment_id -> {disruption_probability, expected_delay_hours, risk_score, risk_level}
    _risk_cache: dict[str, dict] = {}

    @classmethod
    def initialize(cls) -> None:
        """Load datasets at application startup."""
        shipments_path = _DATA_DIR / "shipments.csv"
        fleet_path = _DATA_DIR / "fleet.csv"

        if not shipments_path.exists():
            logger.warning(f"Shipments dataset not found at {shipments_path}. Generating...")
            cls._generate_data()

        cls._shipments_df = pd.read_csv(shipments_path)
        cls._fleet_df = pd.read_csv(fleet_path)
        logger.info(
            f"Loaded {len(cls._shipments_df)} shipments, "
            f"{len(cls._fleet_df)} fleet vehicles."
        )

    @classmethod
    def build_risk_cache(cls) -> None:
        """
        Precompute ML risk for all shipments using batch prediction.
        Called once after MLService is initialized. Results cached in memory.
        """
        from services.ml_service import MLService
        from services.risk_engine import compute_risk_score

        df = cls.get_shipments()
        rows = df.to_dict(orient="records")

        logger.info(f"Building risk cache for {len(rows)} shipments...")
        try:
            predictions = MLService.predict_batch(rows)
        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            return

        cache = {}
        for row, pred in zip(rows, predictions):
            sid = str(row.get("shipment_id", ""))
            try:
                risk_result = compute_risk_score(
                    disruption_probability=pred["disruption_probability"],
                    weather_severity=float(row.get("weather_severity", 0)),
                    traffic_level=float(row.get("traffic_level", 0)),
                    port_congestion=float(row.get("port_congestion", 0)),
                    warehouse_delay_hours=float(row.get("warehouse_delay_hours", 0)),
                    supplier_risk=float(row.get("supplier_risk", 0)),
                    vehicle_utilization=float(row.get("vehicle_utilization", 0.5)),
                    priority=str(row.get("priority", "MEDIUM")),
                    delivery_deadline_hours=float(row.get("delivery_deadline_hours", 48)),
                )
                cache[sid] = {
                    "disruption_probability": pred["disruption_probability"],
                    "expected_delay_hours": pred["expected_delay_hours"],
                    "risk_score": risk_result["risk_score"],
                    "risk_level": risk_result["risk_level"],
                    "recommended_action": risk_result["recommended_action"],
                }
            except Exception as e:
                logger.warning(f"Risk cache error for {sid}: {e}")

        cls._risk_cache = cache
        logger.info(f"Risk cache built: {len(cache)} entries.")

    @classmethod
    def _generate_data(cls) -> None:
        import sys
        sys.path.insert(0, str(_PROJECT_ROOT / "src" / "ml"))
        from data.generate_dataset import main as gen_main
        gen_main()

    @classmethod
    def get_shipments(cls) -> pd.DataFrame:
        if cls._shipments_df is None:
            cls.initialize()
        return cls._shipments_df.copy()

    @classmethod
    def get_fleet(cls) -> pd.DataFrame:
        if cls._fleet_df is None:
            cls.initialize()
        return cls._fleet_df.copy()

    @classmethod
    def get_shipment_by_id(cls, shipment_id: str) -> Optional[dict]:
        df = cls.get_shipments()
        rows = df[df["shipment_id"] == shipment_id]
        if rows.empty:
            return None
        return rows.iloc[0].to_dict()

    @classmethod
    def get_vehicle_by_id(cls, vehicle_id: str) -> Optional[dict]:
        df = cls.get_fleet()
        rows = df[df["vehicle_id"] == vehicle_id]
        if rows.empty:
            return None
        return rows.iloc[0].to_dict()

    @classmethod
    def get_risk(cls, shipment_id: str) -> Optional[dict]:
        """Return precomputed risk entry, or None if not cached."""
        return cls._risk_cache.get(str(shipment_id))

    @classmethod
    def get_all_risk(cls) -> dict[str, dict]:
        return cls._risk_cache
