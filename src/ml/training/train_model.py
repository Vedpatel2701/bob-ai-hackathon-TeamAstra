"""ML model training script for SupplyChainAI."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score, classification_report, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split

# Add ml/ directory to path so preprocessing is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preprocessing.features import prepare_features, prepare_labels

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MODEL_DIR = Path(__file__).resolve().parents[1] / "models"


def train_model():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    shipments_path = DATA_DIR / "shipments.csv"

    if not shipments_path.exists():
        print(f"Dataset not found at {shipments_path}. Generating...")
        from data.generate_dataset import main as gen_main
        gen_main()

    df = pd.read_csv(shipments_path)
    print(f"Loaded {len(df)} shipments for training.")

    X = prepare_features(df)
    y = prepare_labels(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Classification model: disruption probability
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=5,
        random_state=42,
        class_weight="balanced",
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "disruption_rate_train": round(float(y_train.mean()), 4),
    }
    print("Classification metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    # Regression model: expected delay hours (trained on disrupted + non-disrupted)
    delay_col = "actual_delay_hours"
    y_delay = df[delay_col].values.astype(float)
    X_train_d, X_test_d, y_train_d, y_test_d = train_test_split(
        X, y_delay, test_size=0.20, random_state=42
    )
    reg = GradientBoostingRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
    )
    reg.fit(X_train_d, y_train_d)

    # Save models
    clf_path = MODEL_DIR / "classifier.pkl"
    reg_path = MODEL_DIR / "regressor.pkl"
    metrics_path = MODEL_DIR / "metrics.json"

    joblib.dump(clf, clf_path)
    joblib.dump(reg, reg_path)

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Saved classifier to {clf_path}")
    print(f"Saved regressor  to {reg_path}")
    print(f"Saved metrics    to {metrics_path}")

    # Build SHAP explainer
    try:
        import shap
        explainer = shap.TreeExplainer(clf)
        explainer_path = MODEL_DIR / "shap_explainer.pkl"
        joblib.dump(explainer, explainer_path)
        print(f"Saved SHAP explainer to {explainer_path}")
    except ImportError:
        print("SHAP not installed — skipping explainer. Install with: pip install shap")
    except Exception as e:
        print(f"SHAP explainer failed: {e}")

    return clf, reg, metrics


if __name__ == "__main__":
    train_model()
