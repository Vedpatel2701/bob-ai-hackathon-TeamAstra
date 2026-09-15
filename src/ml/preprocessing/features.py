"""ML feature preprocessing pipeline."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder

FEATURE_COLUMNS = [
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


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode categorical features and return a copy with all model features."""
    df = df.copy()
    df["priority_encoded"] = df["priority"].map(PRIORITY_MAP).fillna(1).astype(int)
    return df


def prepare_features(df: pd.DataFrame) -> np.ndarray:
    """Return a 2-D feature matrix for the given dataframe."""
    df = encode_features(df)
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")
    return df[FEATURE_COLUMNS].values.astype(float)


def prepare_labels(df: pd.DataFrame) -> np.ndarray:
    """Return binary disruption labels."""
    return df["disruption"].values.astype(int)
