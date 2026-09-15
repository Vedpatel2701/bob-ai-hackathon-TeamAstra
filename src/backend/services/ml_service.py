"""ML service — wraps inference service for use by API routes."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ML_DIR = _PROJECT_ROOT / "src" / "ml"


class MLService:
    _initialized = False

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return
        ml_path = str(_ML_DIR)
        if ml_path not in sys.path:
            sys.path.insert(0, ml_path)

        model_dir = _ML_DIR / "models"
        if not model_dir.exists() or not (model_dir / "classifier.pkl").exists():
            logger.warning("ML models not found. Attempting to train...")
            try:
                cls._train_models()
            except Exception as e:
                logger.error(f"Model training failed: {e}")
                raise RuntimeError(
                    "ML models not found. Run: python src/ml/training/train_model.py"
                ) from e

        try:
            from inference.inference_service import InferenceService
            InferenceService.load(model_dir)
            cls._initialized = True
            logger.info("ML service initialized.")
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")
            raise

    @classmethod
    def _train_models(cls) -> None:
        import subprocess
        import sys as _sys
        script = str(_ML_DIR / "training" / "train_model.py")
        result = subprocess.run([_sys.executable, script], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)

    @classmethod
    def predict(cls, features: dict) -> dict:
        """Single prediction with SHAP — for individual shipment investigation."""
        if not cls._initialized:
            cls.initialize()
        from inference.inference_service import InferenceService
        return InferenceService.predict(features)

    @classmethod
    def predict_batch(cls, rows: list[dict]) -> list[dict]:
        """Vectorized batch prediction — no SHAP, fast for bulk use."""
        if not cls._initialized:
            cls.initialize()
        from inference.inference_service import InferenceService
        return InferenceService.predict_batch(rows)

    @classmethod
    def get_metrics(cls) -> Optional[dict]:
        if not cls._initialized:
            return None
        from inference.inference_service import InferenceService
        return InferenceService.get_metrics()
