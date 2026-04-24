from __future__ import annotations

import re

from app.archetypes import alias_match, query_has_alias_intent, score_archetype_fit
from app.finance import estimate_financing
from app.ml_ranker import predict_match_score
from app.models import PreferenceProfile, Recommendation, Vehicle


FEATURES = {
    "family": "family",
    "fun": "fun",
    "luxury": "luxury",
    "ownership_cost": "ownership_cost",
    "performance": "performance",
    "practicality": "practicality",
    "reliability": "reliability",
    "winter": "winter",
}

GTA_CITIES = {
    "toronto",
    "mississauga",
    "brampton",
    "markham",
    "vaughan",
    "scarborough",
    "oakville",
}

MODEL_STOP_WORDS = {
    "base",
    "car",
    "cars",
    "certified",
    "cheap",
    "good",
    "great",
    "high",
    "luxury",
    "new",
    "old",
    "performance",
    "reliable",
    "sedan",
    "suv",
    "truck",
    "used",
}


def recommend_vehicles(
    vehicles: list[Vehicle],
    profile: PreferenceProfile,
    limit: int = 5,
) -> list[Recommendation]:
    scored: list[Recommendation] = []
    has_model_intent = _query_has_model_intent(vehicles, profile)
    if not has_model_intent and _query_looks_like_specific_unknown_name(profile):
        return []

    for vehicle in vehicles:
        if not _passes_hard_filters(vehicle, profile):
            continue

        score, reasons, cautions = _score_vehicle(vehicle, profile)
        name_score, name_reason = _name_match_score(vehicle, profile)
        if has_model_intent and name_score <= 0:
            continue
        if name_score:
            score += name_score
            reasons.insert(0, name_reason)
        ml_score = predict_match_score(vehicle, profile)
        if ml_score is not None:
            score = _blend_scores(score, ml_score)
            if ml_score >= 82:
                reasons.append(f"ML match model also rates this as a {ml_score:.0f}/100 fit.")
        finance = estimate_financing(
            vehicle,
            down_payment=profile.down_payment,
            annual_rate=profile.annual_interest_rate,
            months=profile.loan_months,
        )
        scored.append(
            Recommendation(
                vehicle=vehicle,
                score=score,
                reasons=tuple(reasons),
                cautions=tuple(cautions),
                finance=finance,
                ml_score=ml_score,
            )
        )

    return sorted(scored, key=lambda recommendation: recommendation.score, reverse=True)[:limit]


def _query_has_model_intent(vehicles: list[Vehicle], profile: PreferenceProfile) -> bool:
    query = _normalized_search_text(profile.query)
    if not query:
        return False
    if query_has_alias_intent(profile.query):
        return True

    for vehicle in vehicles:
        model = _normalized_search_text(vehicle.model)
        if _is_useful_model_phrase(model) and _phrase_in_query(model, query):
            return True
    return False


def _name_match_score(vehicle: Vehicle, profile: PreferenceProfile) -> tuple[float, str]:
    query = _normalized_search_text(profile.query)
    if not query:
        return 0.0, ""

    alias_result = alias_match(vehicle, profile.query)
    if alias_result is not None:
        return alias_result

    make = _normalized_search_text(vehicle.make)
    model = _normalized_search_text(vehicle.model)
    trim = _normalized_search_text(vehicle.trim)

    if _is_useful_model_phrase(model) and _phrase_in_query(model, query):
        return 45.0, f"Matches the requested {vehicle.make} {vehicle.model} model."

    if trim and _phrase_in_query(trim, query):
        return 16.0, f"Matches the requested {vehicle.trim} trim."

    if make and _phrase_in_query(make, query):
        return 12.0, f"Matches the requested {vehicle.make} make."

    return 0.0, ""


def _normalized_search_text(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _phrase_in_query(phrase: str, query: str) -> bool:
    if not phrase:
        return False
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", query) is not None


def _is_useful_model_phrase(model: str) -> bool:
    if not model:
        return False
    tokens = [token for token in model.split() if token not in MODEL_STOP_WORDS]
    if not tokens:
        return False
    return any(len(token) >= 3 or token.isdigit() for token in tokens)


def _query_looks_like_specific_unknown_name(profile: PreferenceProfile) -> bool:
    if (
        profile.budget_min
        or profile.budget_max
        or profile.location
        or profile.year_min
        or profile.year_max
        or profile.max_mileage_km
        or profile.origins
        or profile.excluded_origins
        or profile.makes
        or profile.excluded_makes
        or profile.body_styles
        or profile.listing_types
        or profile.fuel_types
        or profile.engine_cylinders
        or profile.required_features
        or profile.required_accident_history
        or profile.required_drivetrain
        or profile.seats_min
    ):
        return False

    if profile.priorities != {"reliability": 0.8, "value": 1.0}:
        return False

    tokens = [
        token
        for token in _normalized_search_text(profile.query).split()
        if token not in MODEL_STOP_WORDS and token not in {"find", "show", "me"}
    ]
    return 1 <= len(tokens) <= 3


def _blend_scores(rule_score: float, ml_score: float) -> float:
    # Keep deterministic rules dominant, while letting the trained model nudge close calls.
    return rule_score + ((ml_score - 50.0) * 0.25)


def _passes_hard_filters(vehicle: Vehicle, profile: PreferenceProfile) -> bool:
    if profile.excluded_origins and vehicle.origin in profile.excluded_origins:
        return False
    if profile.excluded_makes and vehicle.make in profile.excluded_makes:
        return False
    if profile.origins and vehicle.origin not in profile.origins:
        return False
    if profile.makes and vehicle.make not in profile.makes:
        return False
    if profile.year_min and vehicle.year < profile.year_min:
        return False
    if profile.year_max and vehicle.year > profile.year_max:
        return False
    if profile.max_mileage_km and vehicle.mileage_km > profile.max_mileage_km:
        return False
    if profile.required_drivetrain and vehicle.drivetrain.lower() != profile.required_drivetrain.lower():
        return False
    if profile.seats_min and vehicle.seats < profile.seats_min:
        return False
    if profile.body_styles and vehicle.body_style not in profile.body_styles:
        return False
    if profile.excluded_body_styles and vehicle.body_style in profile.excluded_body_styles:
        return False
    if profile.listing_types and not _matches_listing_type(vehicle, profile.listing_types):
        return False
    if profile.fuel_types and vehicle.fuel_type not in profile.fuel_types:
        return False
    if profile.engine_cylinders and vehicle.cylinders not in profile.engine_cylinders:
        return False
    if profile.required_features and not profile.required_features.issubset(set(vehicle.features)):
        return False
    if profile.required_accident_history and vehicle.accident_history != profile.required_accident_history:
        return False

    if profile.budget_max:
        max_with_flex = profile.budget_max * (1 + profile.budget_flex_pct)
        if vehicle.price_cad > max_with_flex:
            return False
    if profile.budget_min and vehicle.price_cad < profile.budget_min:
        return False

    return True


def _matches_listing_type(vehicle: Vehicle, listing_types: set[str]) -> bool:
    if vehicle.listing_type in listing_types:
        return True
    if "Used" in listing_types and vehicle.listing_type == "Certified":
        return True
    return False


def _score_vehicle(vehicle: Vehicle, profile: PreferenceProfile) -> tuple[float, list[str], list[str]]:
    score = 45.0
    reasons: list[str] = []
    cautions: list[str] = []

    score += _budget_score(vehicle, profile, reasons, cautions)
    score += _location_score(vehicle, profile, reasons)
    score += _listing_type_score(vehicle, profile, reasons)
    score += _fuel_type_score(vehicle, profile, reasons)
    score += _powertrain_score(vehicle, profile, reasons)
    score += _feature_match_score(vehicle, profile, reasons)
    score += _year_score(vehicle, profile, reasons)
    score += _mileage_score(vehicle, profile, reasons, cautions)
    score += _origin_score(vehicle, profile, reasons)
    archetype_score, archetype_reasons, archetype_cautions = score_archetype_fit(vehicle, profile)
    score += archetype_score
    reasons = archetype_reasons + reasons
    cautions.extend(archetype_cautions)
    score += _market_score(vehicle, reasons, cautions)
    score += _listing_quality_score(vehicle, reasons, cautions)
    score += _preference_score(vehicle, profile, reasons)
    score += _value_score(vehicle, profile, reasons)

    if vehicle.drivetrain.upper() == "AWD" and ("winter" in profile.priorities or "family" in profile.priorities):
        score += 4
        reasons.append("AWD adds confidence for Canadian winter driving.")

    if vehicle.origin == "German" and "ownership_cost" in profile.priorities:
        score -= 4
        cautions.append("German performance cars can carry higher maintenance and repair costs.")

    if vehicle.performance >= 8.5 and vehicle.reliability < 7.2:
        cautions.append("Strong performance score, but reliability is not the main strength.")

    return max(score, 0), _dedupe(reasons)[:5], _dedupe(cautions)[:3]


def _budget_score(
    vehicle: Vehicle,
    profile: PreferenceProfile,
    reasons: list[str],
    cautions: list[str],
) -> float:
    if not profile.budget_max:
        if profile.budget_min:
            reasons.append(f"Fits the high-end search at ${vehicle.price_cad:,}.")
            return min(10.0, vehicle.price_cad / 20000)
        return 0.0

    delta = profile.budget_max - vehicle.price_cad
    if delta >= 0:
        closeness = 1 - min(delta / max(profile.budget_max, 1), 1)
        reasons.append(f"Fits the ${profile.budget_max:,} budget at ${vehicle.price_cad:,}.")
        return 10 + closeness * 8

    over_by = abs(delta)
    cautions.append(f"Comes in ${over_by:,} above the target budget before taxes and fees.")
    return -min(10, over_by / 1000)


def _location_score(vehicle: Vehicle, profile: PreferenceProfile, reasons: list[str]) -> float:
    if not profile.location:
        return 0.0

    vehicle_location = vehicle.location.lower()
    requested = profile.location.lower()
    requested_upper = profile.location.upper()
    if requested_upper == vehicle.province.upper():
        reasons.append(f"Located in {vehicle.province}.")
        return 5.0

    if requested in vehicle_location or vehicle_location in requested:
        reasons.append(f"Located near {profile.location}.")
        return 10.0

    vehicle_city = (vehicle.city or vehicle_location.split(",")[0]).lower().strip()
    if requested == "toronto" and vehicle_city in GTA_CITIES:
        reasons.append("Located in the GTA search area.")
        return 6.0

    if "," in vehicle_location and "," in requested:
        vehicle_region = vehicle_location.split(",")[-1].strip()
        requested_region = requested.split(",")[-1].strip()
        if vehicle_region == requested_region:
            reasons.append(f"Located in the same region as {profile.location}.")
            return 3.0

    return 0.0


def _listing_type_score(vehicle: Vehicle, profile: PreferenceProfile, reasons: list[str]) -> float:
    if not profile.listing_types:
        return 0.0
    if vehicle.listing_type == "Certified":
        reasons.append("Matches the certified pre-owned preference.")
        return 5.0
    if vehicle.listing_type in profile.listing_types:
        reasons.append(f"Matches the requested {vehicle.listing_type.lower()} listing type.")
        return 3.0
    return 0.0


def _fuel_type_score(vehicle: Vehicle, profile: PreferenceProfile, reasons: list[str]) -> float:
    if profile.fuel_types and vehicle.fuel_type in profile.fuel_types:
        reasons.append(f"Matches the requested {vehicle.fuel_type.lower()} fuel type.")
        return 5.0
    return 0.0


def _powertrain_score(vehicle: Vehicle, profile: PreferenceProfile, reasons: list[str]) -> float:
    if profile.engine_cylinders and vehicle.cylinders in profile.engine_cylinders:
        reasons.append(f"Matches the requested {vehicle.cylinders}-cylinder engine.")
        return 5.0
    return 0.0


def _feature_match_score(vehicle: Vehicle, profile: PreferenceProfile, reasons: list[str]) -> float:
    if not profile.required_features:
        return 0.0

    matched = sorted(profile.required_features.intersection(set(vehicle.features)))
    if matched:
        reasons.append(f"Has requested features: {', '.join(matched[:3])}.")
    return len(matched) * 2.0


def _year_score(vehicle: Vehicle, profile: PreferenceProfile, reasons: list[str]) -> float:
    if profile.year_min is None and profile.year_max is None:
        return 0.0

    reasons.append(f"Matches the requested model year range with a {vehicle.year}.")
    return 4.0


def _mileage_score(
    vehicle: Vehicle,
    profile: PreferenceProfile,
    reasons: list[str],
    cautions: list[str],
) -> float:
    if vehicle.mileage_km <= 30000:
        reasons.append("Low mileage for the model year.")
        return 4.0

    if vehicle.mileage_km <= 60000:
        return 2.0

    if profile.max_mileage_km and vehicle.mileage_km > profile.max_mileage_km * 0.85:
        cautions.append("Mileage is close to the maximum requested.")
        return -1.0

    vehicle_age = max(2026 - vehicle.year, 1)
    expected_mileage = vehicle_age * 20000
    if vehicle.mileage_km > expected_mileage * 1.35:
        cautions.append("Mileage is high for the model year.")
        return -3.0

    return 1.0


def _origin_score(vehicle: Vehicle, profile: PreferenceProfile, reasons: list[str]) -> float:
    if profile.origins and vehicle.origin in profile.origins:
        reasons.append(f"Matches the requested {vehicle.origin.lower()} brand origin.")
        return 5.0
    return 0.0


def _market_score(vehicle: Vehicle, reasons: list[str], cautions: list[str]) -> float:
    score = 0.0
    delta = vehicle.market_delta_cad
    if delta is not None:
        if delta <= -1000:
            score += min(6.0, abs(delta) / 700)
            reasons.append(f"Priced ${abs(delta):,} below the estimated local market average.")
        elif delta >= 1500:
            score -= min(5.0, delta / 900)
            cautions.append(f"Priced ${delta:,} above the estimated local market average.")

    if vehicle.price_history_cad:
        first_price = vehicle.price_history_cad[0]
        last_price = vehicle.price_history_cad[-1]
        drop = first_price - last_price
        if drop >= 1000:
            score += 1.5
            reasons.append(f"Price has dropped ${drop:,} since the first tracked listing snapshot.")

    if vehicle.days_on_market is not None:
        if 35 <= vehicle.days_on_market <= 90:
            score += 1.0
            reasons.append("Has been listed long enough that there may be negotiation room.")
        elif vehicle.days_on_market > 120:
            cautions.append("Has been listed for a long time, so it may need a closer inspection.")

    return score


def _listing_quality_score(vehicle: Vehicle, reasons: list[str], cautions: list[str]) -> float:
    score = 0.0
    if vehicle.cpo:
        score += 3.0
        reasons.append("Certified pre-owned listing adds warranty and inspection confidence.")

    if vehicle.accident_history == "none_reported":
        score += 1.0
    elif vehicle.accident_history == "minor_reported":
        score -= 3.0
        cautions.append("Minor accident history is reported, so the inspection matters.")
    elif vehicle.accident_history == "unknown":
        score -= 1.0
        cautions.append("Accident history is unknown in the demo inventory.")

    return score


def _preference_score(vehicle: Vehicle, profile: PreferenceProfile, reasons: list[str]) -> float:
    score = 0.0
    ranked_matches: list[tuple[float, str]] = []

    for priority, weight in profile.priorities.items():
        if priority == "value":
            continue
        if priority == "fuel_economy":
            economy_score = _fuel_economy_score(vehicle)
            score += economy_score * weight * 1.8
            if economy_score >= 8:
                ranked_matches.append((economy_score * weight, "Scores well for fuel economy."))
            continue
        if priority == "audio":
            audio_score = _audio_score(vehicle)
            score += audio_score * weight * 1.5
            if audio_score >= 8:
                ranked_matches.append((audio_score * weight, "Has a premium audio setup."))
            continue
        if priority == "safety":
            safety_score = (vehicle.practicality + vehicle.winter) / 2
            score += safety_score * weight * 1.4
            if safety_score >= 7.5:
                ranked_matches.append((safety_score * weight, "Scores well for safety-minded features."))
            continue
        feature_name = FEATURES.get(priority)
        if feature_name is None:
            continue
        feature_value = float(getattr(vehicle, feature_name))
        score += feature_value * weight * 1.7
        if feature_value >= 7.5:
            ranked_matches.append((feature_value * weight, _reason_for(priority, feature_value)))

    for _, reason in sorted(ranked_matches, reverse=True)[:3]:
        reasons.append(reason)

    return score


def _fuel_economy_score(vehicle: Vehicle) -> float:
    if vehicle.fuel_type == "EV":
        return 9.5
    if vehicle.l_per_100km <= 0:
        return 6.0
    return max(1.0, min(9.5, 11.5 - vehicle.l_per_100km))


def _audio_score(vehicle: Vehicle) -> float:
    return 8.8 if "premium audio" in vehicle.features else 4.5


def _value_score(vehicle: Vehicle, profile: PreferenceProfile, reasons: list[str]) -> float:
    if "value" not in profile.priorities:
        return 0.0

    quality = (
        vehicle.reliability
        + vehicle.performance
        + vehicle.practicality
        + vehicle.luxury
        + vehicle.ownership_cost
    ) / 5
    price_factor = max(0.5, 1 - (vehicle.price_cad / 100000))
    value = quality * price_factor * 3
    if value >= 10:
        reasons.append("Strong value score for the mix of price, features, and ownership profile.")
    return value


def _reason_for(priority: str, feature_value: float) -> str:
    labels = {
        "family": "Scores well for family practicality.",
        "fun": "Scores well for fun-to-drive character.",
        "luxury": "Scores well for comfort and luxury.",
        "ownership_cost": "Scores well for lower ownership cost.",
        "performance": "Scores well for performance.",
        "practicality": "Scores well for everyday practicality.",
        "reliability": "Scores well for reliability.",
        "winter": "Scores well for winter suitability.",
    }
    label = labels.get(priority, f"Scores well for {priority}.")
    if feature_value >= 9:
        return label.replace("Scores well", "Scores extremely well")
    return label


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output
