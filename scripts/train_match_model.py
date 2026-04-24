from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.archetypes import score_archetype_fit
from app.data_loader import data_source_info, load_vehicles
from app.ml_features import FEATURE_NAMES, build_feature_vector
from app.ml_ranker import MODEL_PATH, reset_model_cache
from app.models import PreferenceProfile, Vehicle
from app.preferences import parse_preferences


TRAINING_QUERIES = [
    "dirt cheap reliable car in Ontario",
    "cheap first car good on gas under 12k",
    "budget reliable commuter under 20k",
    "used reliable suv from the 2010s under 30k",
    "hybrid suv with great fuel economy under 45k",
    "family suv under 45k reliable good in winter near Toronto",
    "fun but reliable Japanese car under 50k near Toronto",
    "fast but easy to maintain under 50k",
    "fast but easy to maintain Japanese car under 50k",
    "luxury sedan under 60k with good speakers",
    "car with good speakers under 45k",
    "old BMW under 25k",
    "certified pre-owned reliable awd suv under 45k",
    "six figure performance car awd",
    "no budget high-end performance suv",
    "expensive high-end luxury suv near Toronto",
    "manual enthusiast car under 45k",
    "Japanese sports car under 50k",
    "comfortable family car with premium audio",
    "low mileage reliable car around 35k",
    "German performance coupe no budget",
    "three row family suv under 60k",
    "v6 cars 30k 60k km ontario any year sedan",
    "v6 sedan under 30k under 60k km",
    "clean history sedan with sunroof under 35k",
    "comfortable car with leather heated seats and blind spot monitoring",
    "american muscle car",
    "american muscle under 40k",
    "v8 muscle car near Toronto",
    "tuner car under 30k",
    "jdm tuner car under 35k",
    "manual tuner hatchback under 30k",
    "german performance sedan under 50k",
    "winter daily under 25k awd reliable",
    "family hauler with 7 seats and safety features",
    "quiet luxury cruiser with premium audio",
    "cheap reliable first car under 15k",
    "off road suv for camping",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the AutoMatch AI vehicle match model.")
    parser.add_argument("--output", type=Path, default=MODEL_PATH)
    parser.add_argument("--card", type=Path, default=Path("models") / "model_card.json")
    args = parser.parse_args()

    vehicles = load_vehicles()
    source = data_source_info()
    features, labels = build_training_set(vehicles)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.25,
        random_state=42,
    )
    model = HistGradientBoostingRegressor(
        random_state=42,
        max_iter=180,
        learning_rate=0.08,
        max_leaf_nodes=31,
        l2_regularization=0.02,
    )
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    metrics = {
        "mae": round(float(mean_absolute_error(y_test, predictions)), 3),
        "r2": round(float(r2_score(y_test, predictions)), 3),
    }

    bundle = {
        "model": model,
        "model_type": "HistGradientBoostingRegressor",
        "feature_names": FEATURE_NAMES,
        "training_examples": int(len(labels)),
        "metrics": metrics,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_queries": TRAINING_QUERIES,
        "data_source": source,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, args.output)
    reset_model_cache()

    args.card.parent.mkdir(parents=True, exist_ok=True)
    args.card.write_text(json.dumps(_model_card(bundle), indent=2), encoding="utf-8")

    print(f"Trained match model with {len(labels)} examples")
    print(f"Saved model to {args.output}")
    print(f"Metrics: MAE={metrics['mae']} R2={metrics['r2']}")


def build_training_set(vehicles: list[Vehicle]) -> tuple[np.ndarray, np.ndarray]:
    rows: list[list[float]] = []
    labels: list[float] = []

    for query in TRAINING_QUERIES:
        profile = parse_preferences(query)
        for vehicle in vehicles:
            rows.append(build_feature_vector(vehicle, profile))
            labels.append(_label_match(vehicle, profile))

    return np.array(rows, dtype=float), np.array(labels, dtype=float)


def _label_match(vehicle: Vehicle, profile: PreferenceProfile) -> float:
    score = 45.0

    if profile.budget_max:
        max_with_flex = profile.budget_max * (1 + profile.budget_flex_pct)
        if vehicle.price_cad <= max_with_flex:
            score += 14.0
            score += max(0.0, 1 - abs(vehicle.price_cad - profile.budget_max) / max(profile.budget_max, 1)) * 5
        else:
            score -= min(35.0, (vehicle.price_cad - max_with_flex) / 1200)

    if profile.budget_min:
        score += 13.0 if vehicle.price_cad >= profile.budget_min else -28.0

    if profile.year_min is not None and vehicle.year < profile.year_min:
        score -= 20.0
    if profile.year_max is not None and vehicle.year > profile.year_max:
        score -= 20.0
    if profile.max_mileage_km and vehicle.mileage_km > profile.max_mileage_km:
        score -= 22.0
    if profile.required_drivetrain and vehicle.drivetrain.lower() != profile.required_drivetrain.lower():
        score -= 25.0
    if profile.seats_min and vehicle.seats < profile.seats_min:
        score -= 18.0
    if profile.origins:
        score += 10.0 if vehicle.origin in profile.origins else -22.0
    if profile.excluded_origins and vehicle.origin in profile.excluded_origins:
        score -= 30.0
    if profile.makes:
        score += 16.0 if vehicle.make in profile.makes else -30.0
    if profile.body_styles:
        score += 14.0 if vehicle.body_style in profile.body_styles else -26.0
    if profile.fuel_types:
        score += 12.0 if vehicle.fuel_type in profile.fuel_types else -22.0
    if profile.engine_cylinders:
        score += 12.0 if vehicle.cylinders in profile.engine_cylinders else -24.0
    if profile.required_features:
        matched = profile.required_features.intersection(set(vehicle.features))
        match_ratio = len(matched) / max(len(profile.required_features), 1)
        score += (match_ratio * 18.0) - ((1.0 - match_ratio) * 20.0)
    if profile.required_accident_history:
        score += 8.0 if vehicle.accident_history == profile.required_accident_history else -25.0
    if profile.listing_types:
        if vehicle.listing_type in profile.listing_types or (
            "Used" in profile.listing_types and vehicle.listing_type == "Certified"
        ):
            score += 8.0
        else:
            score -= 16.0

    score += _location_label(vehicle, profile)
    score += _archetype_label(vehicle, profile)
    score += _priority_label(vehicle, profile)

    if vehicle.cpo:
        score += 3.0
    if vehicle.accident_history == "none_reported":
        score += 2.0
    elif vehicle.accident_history == "minor_reported":
        score -= 5.0

    if vehicle.market_delta_cad is not None:
        if vehicle.market_delta_cad <= -1000:
            score += min(5.0, abs(vehicle.market_delta_cad) / 1000)
        elif vehicle.market_delta_cad >= 1500:
            score -= min(5.0, vehicle.market_delta_cad / 1000)

    return max(0.0, min(100.0, score))


def _location_label(vehicle: Vehicle, profile: PreferenceProfile) -> float:
    if not profile.location:
        return 0.0
    requested = profile.location.lower()
    if requested == vehicle.province.lower():
        return 7.0
    if requested in vehicle.location.lower() or requested == vehicle.city.lower():
        return 10.0
    if requested == "toronto" and vehicle.city.lower() in {
        "toronto",
        "mississauga",
        "brampton",
        "markham",
        "vaughan",
        "scarborough",
        "oakville",
    }:
        return 6.0
    return -6.0


def _archetype_label(vehicle: Vehicle, profile: PreferenceProfile) -> float:
    if not profile.archetypes:
        return 0.0
    fit_score, _, _ = score_archetype_fit(vehicle, profile)
    return max(-28.0, min(32.0, fit_score))


def _priority_label(vehicle: Vehicle, profile: PreferenceProfile) -> float:
    if not profile.priorities:
        return 0.0

    values = {
        "family": vehicle.family,
        "safety": (vehicle.practicality + vehicle.winter) / 2,
        "fun": vehicle.fun,
        "audio": 8.8 if "premium audio" in vehicle.features else 4.5,
        "fuel_economy": _fuel_economy_score(vehicle),
        "luxury": vehicle.luxury,
        "ownership_cost": vehicle.ownership_cost,
        "performance": vehicle.performance,
        "practicality": vehicle.practicality,
        "reliability": vehicle.reliability,
        "value": _value_score(vehicle),
        "winter": vehicle.winter,
    }
    total = 0.0
    total_weight = 0.0
    for name, weight in profile.priorities.items():
        total += values.get(name, 0.0) * weight
        total_weight += abs(weight)
    if total_weight <= 0:
        return 0.0
    return ((total / total_weight) - 5.0) * 4.0


def _fuel_economy_score(vehicle: Vehicle) -> float:
    if vehicle.fuel_type == "EV":
        return 9.5
    return max(1.0, min(9.5, 11.5 - vehicle.l_per_100km))


def _value_score(vehicle: Vehicle) -> float:
    quality = (
        vehicle.reliability
        + vehicle.performance
        + vehicle.practicality
        + vehicle.luxury
        + vehicle.ownership_cost
    ) / 5
    price_factor = max(0.5, 1 - (vehicle.price_cad / 100000))
    return quality * price_factor


def _model_card(bundle: dict[str, object]) -> dict[str, object]:
    return {
        "name": "AutoMatch AI match ranker",
        "purpose": "Scores how well a vehicle matches a natural-language buyer request after hard filters are applied.",
        "model_type": bundle["model_type"],
        "feature_count": len(FEATURE_NAMES),
        "training_examples": bundle["training_examples"],
        "metrics": bundle["metrics"],
        "trained_at": bundle["trained_at"],
        "data_source": bundle.get("data_source"),
        "data_boundary": _data_boundary(bundle),
        "features": FEATURE_NAMES,
    }


def _data_boundary(bundle: dict[str, object]) -> str:
    source = bundle.get("data_source")
    if isinstance(source, dict) and source.get("type") == "hybrid_marketplace":
        return (
            "Trained on a hybrid inventory combining the Kaggle Toronto used-vehicles dataset, "
            "manual curated seed listings, and simulated live-listing variants with synthetic match-quality labels."
        )
    if isinstance(source, dict) and source.get("type") == "kaggle_toronto_used_vehicles":
        return "Trained on the Kaggle Toronto used-vehicles dataset with synthetic match-quality labels."
    if isinstance(source, dict) and source.get("type") == "imported_real_listings":
        return (
            "Trained on imported Rebrowser AutoTrader sample listings with synthetic match-quality labels. "
            "Free sample prices may be KBB estimates when sale price is masked."
        )
    return "Trained on synthetic Canadian demo inventory and synthetic match-quality labels for portfolio use."


if __name__ == "__main__":
    main()
