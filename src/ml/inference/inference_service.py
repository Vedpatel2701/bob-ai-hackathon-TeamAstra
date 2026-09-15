"""ML inference service — loads trained model and runs predictions."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

logger = logging.getLogger(__name__)

ML_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = ML_DIR / "models"

FEATURE_NAMES = [
    "weather_severity",
    "traffic_level",
    "port_congestion",
    "warehouse_delay_hours",
    "supplier_risk",
    "vehicle_utilization",
    "historical_delay_hours",
    "delivery_deadline_hours",
    "distance_km",
    "cargo_weight_kg",
    "priority_encoded",
]

PRIORITY_MAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
FEATURE_LABELS = {
    "weather_severity": "Weather severity",
    "traffic_level": "Traffic level",
    "port_congestion": "Port congestion",
    "warehouse_delay_hours": "Warehouse delay",
    "supplier_risk": "Supplier risk",
    "vehicle_utilization": "Vehicle utilization",
    "historical_delay_hours": "Historical delay",
    "delivery_deadline_hours": "Delivery deadline pressure",
    "distance_km": "Route distance",
    "cargo_weight_kg": "Cargo weight",
    "priority_encoded": "Shipment priority",
}


def _rows_to_matrix(rows: list[dict]) -> np.ndarray:
    """Convert a list of feature dicts to a (N, 11) feature matrix."""
    out = np.empty((len(rows), len(FEATURE_NAMES)), dtype=np.float64)
    for i, r in enumerate(rows):
        p_enc = PRIORITY_MAP.get(str(r.get("priority", "MEDIUM")).upper(), 1)
        out[i] = [
            float(r.get("weather_severity", 0.0)),
            float(r.get("traffic_level", 0.0)),
            float(r.get("port_congestion", 0.0)),
            float(r.get("warehouse_delay_hours", 0.0)),
            float(r.get("supplier_risk", 0.0)),
            float(r.get("vehicle_utilization", 0.5)),
            float(r.get("historical_delay_hours", 0.0)),
            float(r.get("delivery_deadline_hours", 48.0)),
            float(r.get("distance_km", 500.0)),
            float(r.get("cargo_weight_kg", 5000.0)),
            float(p_enc),
        ]
    return out


class InferenceService:
    _clf = None
    _reg = None
    _explainer = None
    _metrics: Optional[dict] = None

    @classmethod
    def load(cls, model_dir: Optional[Path] = None) -> None:
        d = model_dir or MODEL_DIR
        clf_path = d / "classifier.pkl"
        reg_path = d / "regressor.pkl"
        metrics_path = d / "metrics.json"
        explainer_path = d / "shap_explainer.pkl"

        if not clf_path.exists():
            raise FileNotFoundError(
                f"Classifier not found at {clf_path}. "
                "Run: python src/ml/training/train_model.py"
            )

        cls._clf = joblib.load(clf_path)
        logger.info(f"Loaded classifier from {clf_path}")

        if reg_path.exists():
            cls._reg = joblib.load(reg_path)
            logger.info(f"Loaded regressor from {reg_path}")

        if metrics_path.exists():
            with open(metrics_path) as f:
                cls._metrics = json.load(f)

        if explainer_path.exists():
            try:
                cls._explainer = joblib.load(explainer_path)
                logger.info("Loaded SHAP explainer.")
            except Exception as e:
                logger.warning(f"Could not load SHAP explainer: {e}")

    @classmethod
    def _build_feature_vector(cls, features: dict) -> np.ndarray:
        return _rows_to_matrix([features])

    @classmethod
    def predict_batch(cls, rows: list[dict]) -> list[dict]:
        """Vectorized batch prediction — no SHAP (use for bulk operations)."""
        if cls._clf is None:
            raise RuntimeError("Model not loaded.")
        if not rows:
            return []

        X = _rows_to_matrix(rows)
        probs = cls._clf.predict_proba(X)[:, 1]

        if cls._reg is not None:
            delays = np.clip(cls._reg.predict(X), 0, 24)
        else:
            delays = np.clip(
                X[:, 3] * 0.8 + X[:, 0] * 6 + X[:, 1] * 4 + X[:, 2] * 5,
                0, 24,
            )

        return [
            {
                "disruption_probability": round(float(probs[i]), 4),
                "expected_delay_hours": round(float(delays[i]), 2),
                "shap_factors": [],  # SHAP not computed in bulk
            }
            for i in range(len(rows))
        ]

    @classmethod
    def predict(cls, features: dict) -> dict:
        """Single-row prediction with SHAP — use only for individual investigation."""
        if cls._clf is None:
            raise RuntimeError("Model not loaded. Call InferenceService.load() first.")

        X = cls._build_feature_vector(features)
        disruption_prob = float(cls._clf.predict_proba(X)[0, 1])

        if cls._reg is not None:
            expected_delay = float(np.clip(cls._reg.predict(X)[0], 0, 24))
        else:
            expected_delay = float(np.clip(
                features.get("warehouse_delay_hours", 0) * 0.8
                + features.get("weather_severity", 0) * 6
                + features.get("traffic_level", 0) * 4
                + features.get("port_congestion", 0) * 5,
                0, 24,
            ))

        shap_factors = cls._compute_shap_factors(X, features)

        return {
            "disruption_probability": round(disruption_prob, 4),
            "expected_delay_hours": round(expected_delay, 2),
            "shap_factors": shap_factors,
        }

    @classmethod
    def _compute_shap_factors(cls, X: np.ndarray, features: dict) -> list[dict]:
        """Return ranked SHAP factors for a single prediction."""
        if cls._explainer is not None:
            try:
                shap_vals = cls._explainer.shap_values(X)
                if isinstance(shap_vals, list):
                    raw = np.array(shap_vals[1])
                    vals = raw[0] if raw.ndim == 2 else raw
                elif isinstance(shap_vals, np.ndarray):
                    if shap_vals.ndim == 3:
                        vals = shap_vals[0, :, 1]
                    elif shap_vals.ndim == 2:
                        vals = shap_vals[0]
                    else:
                        vals = shap_vals
                else:
                    vals = shap_vals

                factors = [
                    {
                        "factor": name,
                        "value": float(X[0, i]),
                        "contribution": round(float(vals[i]), 4),
                        "label": FEATURE_LABELS.get(name, name),
                    }
                    for i, name in enumerate(FEATURE_NAMES)
                ]
                factors.sort(key=lambda x: abs(x["contribution"]), reverse=True)
                return factors
            except Exception as e:
                logger.warning(f"SHAP computation failed: {e}")

        # Fallback: feature importances
        importances = cls._clf.feature_importances_
        factors = [
            {
                "factor": name,
                "value": float(X[0, i]),
                "contribution": round(float(importances[i] * (X[0, i] - 0.5)), 4),
                "label": FEATURE_LABELS.get(name, name),
            }
            for i, name in enumerate(FEATURE_NAMES)
        ]
        factors.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        return factors

    @classmethod
    def get_metrics(cls) -> Optional[dict]:
        return cls._metrics
