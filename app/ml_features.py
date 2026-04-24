from __future__ import annotations

from app.archetypes import score_archetype_fit
from app.models import PreferenceProfile, Vehicle


FEATURE_NAMES = [
    "price_cad",
    "price_to_budget",
    "budget_room_pct",
    "budget_over_pct",
    "budget_min_fit",
    "mileage_km",
    "mileage_to_limit",
    "vehicle_age",
    "year_in_range",
    "make_match",
    "origin_match",
    "body_style_match",
    "fuel_type_match",
    "cylinders",
    "cylinder_match",
    "required_feature_count",
    "required_feature_match_ratio",
    "drivetrain_match",
    "listing_type_match",
    "seat_fit",
    "location_fit",
    "market_delta_pct",
    "price_drop_pct",
    "days_on_market",
    "cpo",
    "clean_history",
    "premium_audio",
    "reliability",
    "performance",
    "practicality",
    "luxury",
    "winter",
    "ownership_cost",
    "fun",
    "family",
    "archetype_count",
    "archetype_fit",
    "weighted_preference_fit",
]


def build_feature_row(vehicle: Vehicle, profile: PreferenceProfile) -> dict[str, float]:
    budget_max = float(profile.budget_max or 0)
    budget_min = float(profile.budget_min or 0)
    mileage_limit = float(profile.max_mileage_km or 0)
    market_average = float(vehicle.market_average_cad or vehicle.price_cad)
    first_price = float(vehicle.price_history_cad[0]) if vehicle.price_history_cad else float(vehicle.price_cad)
    price_drop = max(0.0, first_price - vehicle.price_cad)
    vehicle_features = set(vehicle.features)
    required_features = set(profile.required_features)
    matched_features = required_features.intersection(vehicle_features)

    archetype_score, _, _ = score_archetype_fit(vehicle, profile)

    return {
        "price_cad": float(vehicle.price_cad),
        "price_to_budget": _ratio(vehicle.price_cad, budget_max) if budget_max else 0.0,
        "budget_room_pct": _budget_room(vehicle, budget_max),
        "budget_over_pct": _budget_over(vehicle, budget_max),
        "budget_min_fit": 1.0 if not budget_min or vehicle.price_cad >= budget_min else 0.0,
        "mileage_km": float(vehicle.mileage_km),
        "mileage_to_limit": _ratio(vehicle.mileage_km, mileage_limit) if mileage_limit else 0.0,
        "vehicle_age": float(max(2026 - vehicle.year, 0)),
        "year_in_range": _year_in_range(vehicle, profile),
        "make_match": _contains_match(vehicle.make, profile.makes),
        "origin_match": _contains_match(vehicle.origin, profile.origins),
        "body_style_match": _contains_match(vehicle.body_style, profile.body_styles),
        "fuel_type_match": _contains_match(vehicle.fuel_type, profile.fuel_types),
        "cylinders": float(vehicle.cylinders if vehicle.cylinders is not None else -1),
        "cylinder_match": 1.0 if profile.engine_cylinders and vehicle.cylinders in profile.engine_cylinders else 0.0,
        "required_feature_count": float(len(required_features)),
        "required_feature_match_ratio": len(matched_features) / max(len(required_features), 1),
        "drivetrain_match": _drivetrain_match(vehicle, profile),
        "listing_type_match": _listing_type_match(vehicle, profile),
        "seat_fit": 1.0 if not profile.seats_min or vehicle.seats >= profile.seats_min else 0.0,
        "location_fit": _location_fit(vehicle, profile),
        "market_delta_pct": (vehicle.price_cad - market_average) / max(market_average, 1.0),
        "price_drop_pct": price_drop / max(first_price, 1.0),
        "days_on_market": float(vehicle.days_on_market or 0),
        "cpo": 1.0 if vehicle.cpo else 0.0,
        "clean_history": 1.0 if vehicle.accident_history == "none_reported" else 0.0,
        "premium_audio": 1.0 if "premium audio" in vehicle.features else 0.0,
        "reliability": vehicle.reliability,
        "performance": vehicle.performance,
        "practicality": vehicle.practicality,
        "luxury": vehicle.luxury,
        "winter": vehicle.winter,
        "ownership_cost": vehicle.ownership_cost,
        "fun": vehicle.fun,
        "family": vehicle.family,
        "archetype_count": float(len(profile.archetypes)),
        "archetype_fit": archetype_score,
        "weighted_preference_fit": _weighted_preference_fit(vehicle, profile),
    }


def build_feature_vector(vehicle: Vehicle, profile: PreferenceProfile) -> list[float]:
    row = build_feature_row(vehicle, profile)
    return [row[name] for name in FEATURE_NAMES]


def _ratio(value: float, target: float) -> float:
    return value / max(target, 1.0)


def _budget_room(vehicle: Vehicle, budget_max: float) -> float:
    if not budget_max:
        return 0.0
    return max(0.0, budget_max - vehicle.price_cad) / max(budget_max, 1.0)


def _budget_over(vehicle: Vehicle, budget_max: float) -> float:
    if not budget_max:
        return 0.0
    return max(0.0, vehicle.price_cad - budget_max) / max(budget_max, 1.0)


def _year_in_range(vehicle: Vehicle, profile: PreferenceProfile) -> float:
    if profile.year_min is None and profile.year_max is None:
        return 0.0
    if profile.year_min is not None and vehicle.year < profile.year_min:
        return 0.0
    if profile.year_max is not None and vehicle.year > profile.year_max:
        return 0.0
    return 1.0


def _contains_match(value: str, requested: set[str]) -> float:
    return 1.0 if requested and value in requested else 0.0


def _drivetrain_match(vehicle: Vehicle, profile: PreferenceProfile) -> float:
    if not profile.required_drivetrain:
        return 0.0
    return 1.0 if vehicle.drivetrain.lower() == profile.required_drivetrain.lower() else 0.0


def _listing_type_match(vehicle: Vehicle, profile: PreferenceProfile) -> float:
    if not profile.listing_types:
        return 0.0
    if vehicle.listing_type in profile.listing_types:
        return 1.0
    if "Used" in profile.listing_types and vehicle.listing_type == "Certified":
        return 0.8
    return 0.0


def _location_fit(vehicle: Vehicle, profile: PreferenceProfile) -> float:
    if not profile.location:
        return 0.0
    requested = profile.location.lower()
    if requested == vehicle.province.lower():
        return 0.8
    if requested in vehicle.location.lower() or requested == vehicle.city.lower():
        return 1.0
    if requested == "toronto" and vehicle.city.lower() in {
        "toronto",
        "mississauga",
        "brampton",
        "markham",
        "vaughan",
        "scarborough",
        "oakville",
    }:
        return 0.7
    return 0.0


def _weighted_preference_fit(vehicle: Vehicle, profile: PreferenceProfile) -> float:
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
    total_weight = sum(abs(weight) for weight in profile.priorities.values())
    if total_weight <= 0:
        return 0.0
    weighted = sum(values.get(name, 0.0) * weight for name, weight in profile.priorities.items())
    return weighted / total_weight


def _fuel_economy_score(vehicle: Vehicle) -> float:
    if vehicle.fuel_type == "EV":
        return 9.5
    if vehicle.l_per_100km <= 0:
        return 6.0
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
