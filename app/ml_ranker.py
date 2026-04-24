from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import joblib

from app.ml_features import FEATURE_NAMES, build_feature_vector
from app.models import PreferenceProfile, Vehicle


MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "match_ranker.joblib"


def predict_match_score(vehicle: Vehicle, profile: PreferenceProfile) -> float | None:
    bundle = load_model_bundle()
    if not bundle:
        return None

    model = bundle["model"]
    features = [build_feature_vector(vehicle, profile)]
    score = float(model.predict(features)[0])
    return max(0.0, min(100.0, score))


def model_status() -> dict[str, Any]:
    bundle = load_model_bundle()
    if not bundle:
        return {
            "available": False,
            "path": str(MODEL_PATH),
            "feature_count": len(FEATURE_NAMES),
        }

    return {
        "available": True,
        "path": str(MODEL_PATH),
        "feature_count": len(bundle.get("feature_names", FEATURE_NAMES)),
        "training_examples": bundle.get("training_examples"),
        "metrics": bundle.get("metrics", {}),
        "trained_at": bundle.get("trained_at"),
        "model_type": bundle.get("model_type", type(bundle.get("model")).__name__),
    }


@lru_cache(maxsize=1)
def load_model_bundle() -> dict[str, Any] | None:
    if not MODEL_PATH.exists():
        return None
    bundle = joblib.load(MODEL_PATH)
    if bundle.get("feature_names") != FEATURE_NAMES:
        return None
    return bundle


def reset_model_cache() -> None:
    load_model_bundle.cache_clear()
