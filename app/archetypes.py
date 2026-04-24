from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import PreferenceProfile, Vehicle


@dataclass(frozen=True)
class Archetype:
    key: str
    label: str
    phrases: tuple[str, ...]
    origins: frozenset[str] = frozenset()
    soft_origins: frozenset[str] = frozenset()
    makes: frozenset[str] = frozenset()
    soft_makes: frozenset[str] = frozenset()
    body_styles: frozenset[str] = frozenset()
    soft_body_styles: frozenset[str] = frozenset()
    excluded_body_styles: frozenset[str] = frozenset()
    preferred_models: tuple[tuple[str, str], ...] = ()
    preferred_cylinders: frozenset[int] = frozenset()
    preferred_features: frozenset[str] = frozenset()
    priority_weights: dict[str, float] = field(default_factory=dict)
    seats_min: int | None = None
    budget_max: int | None = None
    budget_flex_pct: float | None = None


ARCHETYPES: dict[str, Archetype] = {
    "american_muscle": Archetype(
        key="american_muscle",
        label="American muscle",
        phrases=(
            "american muscle",
            "muscle car",
            "pony car",
            "mustang or camaro",
            "camaro or mustang",
        ),
        origins=frozenset({"American"}),
        soft_makes=frozenset({"Ford", "Chevrolet", "Dodge"}),
        body_styles=frozenset({"coupe", "convertible", "sedan"}),
        excluded_body_styles=frozenset({"suv", "truck", "van", "wagon", "unknown"}),
        preferred_models=(
            ("Ford", "Mustang"),
            ("Chevrolet", "Camaro"),
            ("Chevrolet", "Corvette"),
            ("Dodge", "Challenger"),
            ("Dodge", "Charger"),
        ),
        preferred_cylinders=frozenset({8}),
        priority_weights={"performance": 2.8, "fun": 2.4},
    ),
    "tuner": Archetype(
        key="tuner",
        label="Tuner car",
        phrases=(
            "tuner",
            "tuner car",
            "mod friendly",
            "project car",
            "track build",
            "street build",
        ),
        soft_origins=frozenset({"Japanese", "German", "Korean"}),
        soft_makes=frozenset(
            {
                "Acura",
                "BMW",
                "Honda",
                "Hyundai",
                "Infiniti",
                "Mazda",
                "Nissan",
                "Subaru",
                "Toyota",
                "Volkswagen",
            }
        ),
        body_styles=frozenset({"coupe", "sedan", "hatchback", "convertible", "roadster", "wagon"}),
        excluded_body_styles=frozenset({"suv", "truck", "van"}),
        preferred_models=(
            ("Acura", "Integra"),
            ("BMW", "335i"),
            ("BMW", "340i"),
            ("BMW", "M3"),
            ("Honda", "Civic"),
            ("Honda", "Civic Type R"),
            ("Hyundai", "Elantra N"),
            ("Mazda", "MX-5"),
            ("Mazda", "Miata"),
            ("Nissan", "350Z"),
            ("Nissan", "370Z"),
            ("Subaru", "BRZ"),
            ("Subaru", "WRX"),
            ("Toyota", "86"),
            ("Toyota", "GR Corolla"),
            ("Toyota", "Supra"),
            ("Volkswagen", "GTI"),
            ("Volkswagen", "Golf R"),
        ),
        preferred_features=frozenset({"turbocharged", "sport suspension"}),
        priority_weights={"fun": 2.5, "performance": 1.8, "ownership_cost": 0.8},
    ),
    "jdm": Archetype(
        key="jdm",
        label="JDM / Japanese enthusiast",
        phrases=("jdm", "japanese sports car", "japanese tuner"),
        origins=frozenset({"Japanese"}),
        soft_makes=frozenset({"Acura", "Honda", "Infiniti", "Lexus", "Mazda", "Nissan", "Subaru", "Toyota"}),
        preferred_models=(
            ("Acura", "Integra"),
            ("Honda", "Civic"),
            ("Honda", "Civic Type R"),
            ("Lexus", "IS 350"),
            ("Mazda", "MX-5"),
            ("Mazda", "Miata"),
            ("Nissan", "350Z"),
            ("Nissan", "370Z"),
            ("Subaru", "BRZ"),
            ("Subaru", "WRX"),
            ("Toyota", "86"),
            ("Toyota", "GR Corolla"),
            ("Toyota", "Supra"),
        ),
        priority_weights={"reliability": 1.8, "fun": 1.5, "value": 0.8},
    ),
    "german_performance": Archetype(
        key="german_performance",
        label="German performance",
        phrases=("german performance", "bimmer", "beamer", "bahn burner"),
        origins=frozenset({"German"}),
        soft_makes=frozenset({"Audi", "BMW", "Mercedes-Benz", "Porsche", "Volkswagen"}),
        body_styles=frozenset({"coupe", "sedan", "hatchback", "wagon", "suv", "convertible"}),
        preferred_models=(
            ("Audi", "S4"),
            ("Audi", "S5"),
            ("BMW", "335i"),
            ("BMW", "340i"),
            ("BMW", "M3"),
            ("BMW", "M4"),
            ("BMW", "M440i"),
            ("Porsche", "911"),
            ("Volkswagen", "GTI"),
            ("Volkswagen", "Golf R"),
        ),
        preferred_features=frozenset({"turbocharged", "sport suspension", "premium audio"}),
        priority_weights={"performance": 2.2, "luxury": 1.4, "fun": 1.8},
    ),
    "family_hauler": Archetype(
        key="family_hauler",
        label="Family hauler",
        phrases=("family hauler", "family car", "for the family", "kids", "car seats"),
        soft_body_styles=frozenset({"suv", "van", "wagon", "sedan"}),
        excluded_body_styles=frozenset({"coupe", "convertible", "roadster"}),
        preferred_features=frozenset(
            {"blind spot monitoring", "adaptive cruise", "backup camera", "heated rear seats"}
        ),
        priority_weights={"family": 2.4, "practicality": 2.0, "safety": 1.4, "reliability": 1.3},
        seats_min=5,
    ),
    "winter_daily": Archetype(
        key="winter_daily",
        label="Canadian winter daily",
        phrases=("winter daily", "winter beater", "snow daily", "good in snow", "canadian winter"),
        soft_body_styles=frozenset({"suv", "sedan", "hatchback", "wagon"}),
        preferred_features=frozenset({"heated seats", "heated steering wheel", "remote start", "winter tire package"}),
        priority_weights={"winter": 2.6, "reliability": 1.6, "ownership_cost": 1.2},
    ),
    "commuter": Archetype(
        key="commuter",
        label="Commuter",
        phrases=("commuter", "daily driver", "daily", "long commute", "highway driving"),
        soft_body_styles=frozenset({"sedan", "hatchback", "suv", "wagon"}),
        preferred_features=frozenset({"adaptive cruise", "apple carplay", "backup camera"}),
        priority_weights={"ownership_cost": 1.8, "reliability": 1.8, "fuel_economy": 1.5, "practicality": 1.0},
    ),
    "luxury_cruiser": Archetype(
        key="luxury_cruiser",
        label="Luxury cruiser",
        phrases=("luxury cruiser", "comfortable cruiser", "quiet ride", "comfortable car", "nice interior"),
        soft_makes=frozenset({"Acura", "Audi", "BMW", "Genesis", "Lexus", "Mercedes-Benz", "Porsche", "Volvo"}),
        preferred_features=frozenset({"premium audio", "leather seats", "ventilated seats", "adaptive cruise"}),
        priority_weights={"luxury": 2.4, "audio": 1.2, "practicality": 0.8},
    ),
    "cheap_reliable": Archetype(
        key="cheap_reliable",
        label="Cheap reliable",
        phrases=("cheap reliable", "dirt cheap", "beater", "first car", "low maintenance"),
        soft_origins=frozenset({"Japanese", "Korean"}),
        soft_makes=frozenset({"Honda", "Hyundai", "Kia", "Lexus", "Mazda", "Toyota"}),
        soft_body_styles=frozenset({"sedan", "hatchback", "suv"}),
        priority_weights={"value": 2.3, "reliability": 2.2, "ownership_cost": 2.0},
        budget_max=15000,
        budget_flex_pct=0.12,
    ),
    "offroad": Archetype(
        key="offroad",
        label="Off-road / trail",
        phrases=("off road", "off-road", "overland", "trail", "camping suv"),
        soft_body_styles=frozenset({"suv", "truck"}),
        soft_makes=frozenset({"Ford", "Jeep", "Land Rover", "Lexus", "Subaru", "Toyota"}),
        preferred_models=(("Jeep", "Wrangler"), ("Toyota", "4Runner"), ("Toyota", "Tacoma"), ("Ford", "Bronco")),
        priority_weights={"winter": 1.8, "practicality": 1.2, "reliability": 1.0},
    ),
}


MODEL_ALIASES: dict[str, tuple[tuple[str, str], ...]] = {
    "mustand": (("Ford", "Mustang"),),
    "mustang": (("Ford", "Mustang"),),
    "camero": (("Chevrolet", "Camaro"),),
    "camaro": (("Chevrolet", "Camaro"),),
    "vette": (("Chevrolet", "Corvette"),),
    "corvette": (("Chevrolet", "Corvette"),),
    "challenger": (("Dodge", "Challenger"),),
    "charger": (("Dodge", "Charger"),),
    "type r": (("Honda", "Civic Type R"), ("Honda", "Civic")),
    "civic type r": (("Honda", "Civic Type R"), ("Honda", "Civic")),
    "gr corolla": (("Toyota", "GR Corolla"),),
    "supra": (("Toyota", "Supra"),),
    "brz": (("Subaru", "BRZ"),),
    "wrx": (("Subaru", "WRX"),),
    "sti": (("Subaru", "WRX"),),
    "miata": (("Mazda", "Miata"), ("Mazda", "MX-5")),
    "mx5": (("Mazda", "MX-5"), ("Mazda", "Miata")),
    "mx-5": (("Mazda", "MX-5"), ("Mazda", "Miata")),
    "gti": (("Volkswagen", "GTI"), ("Volkswagen", "Golf")),
    "golf r": (("Volkswagen", "Golf R"), ("Volkswagen", "Golf")),
    "m3": (("BMW", "M3"),),
    "m4": (("BMW", "M4"),),
    "m340": (("BMW", "M340i"), ("BMW", "340i")),
    "m340i": (("BMW", "M340i"), ("BMW", "340i")),
    "m440": (("BMW", "M440i"),),
    "m440i": (("BMW", "M440i"),),
    "335i": (("BMW", "335i"),),
    "340i": (("BMW", "340i"),),
}


def apply_archetypes(text: str, profile: "PreferenceProfile") -> None:
    for key in detect_archetypes(text):
        archetype = ARCHETYPES[key]
        profile.archetypes.add(key)
        profile.origins.update(archetype.origins)
        profile.body_styles.update(archetype.body_styles)
        profile.excluded_body_styles.update(archetype.excluded_body_styles)
        if archetype.seats_min is not None:
            profile.seats_min = max(profile.seats_min or 0, archetype.seats_min)
        if archetype.budget_max is not None and profile.budget_max is None:
            profile.budget_max = archetype.budget_max
        if archetype.budget_flex_pct is not None:
            profile.budget_flex_pct = max(profile.budget_flex_pct, archetype.budget_flex_pct)
        for priority, weight in archetype.priority_weights.items():
            profile.add_priority(priority, weight)


def detect_archetypes(text: str) -> set[str]:
    normalized = _normalize(text)
    detected: set[str] = set()
    for key, archetype in ARCHETYPES.items():
        if any(_phrase_present(phrase, normalized) for phrase in archetype.phrases):
            detected.add(key)

    if "american" in normalized and "muscle" in normalized:
        detected.add("american_muscle")
    if "jdm" in normalized:
        detected.add("jdm")
    if "tuner" in normalized:
        detected.add("tuner")
    if "luxury" in normalized and ("comfortable" in normalized or "cruiser" in normalized):
        detected.add("luxury_cruiser")
    if "winter" in normalized or "snow" in normalized:
        detected.add("winter_daily")
    if "family" in normalized or "kids" in normalized:
        detected.add("family_hauler")
    return detected


def alias_match(vehicle: "Vehicle", query: str) -> tuple[float, str] | None:
    normalized = _normalize(query)
    for alias, targets in MODEL_ALIASES.items():
        if not _phrase_present(alias, normalized):
            continue
        for make, model in targets:
            if _vehicle_model_matches(vehicle, make, model):
                return 48.0, f"Matches the requested {make} {model} intent."
    return None


def query_has_alias_intent(query: str) -> bool:
    normalized = _normalize(query)
    return any(_phrase_present(alias, normalized) for alias in MODEL_ALIASES)


def score_archetype_fit(vehicle: "Vehicle", profile: "PreferenceProfile") -> tuple[float, list[str], list[str]]:
    if not profile.archetypes:
        return 0.0, [], []

    score = 0.0
    reasons: list[str] = []
    cautions: list[str] = []
    features = set(vehicle.features).union(vehicle.tags)

    for key in profile.archetypes:
        archetype = ARCHETYPES.get(key)
        if not archetype:
            continue

        strong_model = _matches_any_preferred_model(vehicle, archetype)
        if strong_model:
            score += 30.0
            reasons.append(f"Fits the {archetype.label.lower()} archetype by model.")

        if archetype.makes:
            score += 7.0 if vehicle.make in archetype.makes else -18.0
        elif archetype.soft_makes and vehicle.make in archetype.soft_makes:
            score += 5.0

        if archetype.origins:
            score += 5.0 if vehicle.origin in archetype.origins else -18.0
        elif archetype.soft_origins and vehicle.origin in archetype.soft_origins:
            score += 3.0

        if archetype.body_styles:
            if vehicle.body_style in archetype.body_styles:
                score += 7.0
            else:
                score -= 16.0
        elif archetype.soft_body_styles and vehicle.body_style in archetype.soft_body_styles:
            score += 4.0

        if vehicle.body_style in archetype.excluded_body_styles:
            score -= 26.0
            cautions.append(f"{vehicle.body_style.title()} body style is a weak fit for {archetype.label.lower()}.")

        if archetype.preferred_cylinders and vehicle.cylinders in archetype.preferred_cylinders:
            score += 5.0

        matched_features = sorted(features.intersection(archetype.preferred_features))
        if matched_features:
            score += min(6.0, len(matched_features) * 2.0)

        if key == "american_muscle" and vehicle.fuel_type in {"Hybrid", "EV"}:
            score -= 16.0
            cautions.append("Hybrid/EV powertrain is a weak fit for a traditional muscle-car request.")

    return score, _dedupe(reasons)[:3], _dedupe(cautions)[:2]


def _matches_any_preferred_model(vehicle: "Vehicle", archetype: Archetype) -> bool:
    return any(_vehicle_model_matches(vehicle, make, model) for make, model in archetype.preferred_models)


def _vehicle_model_matches(vehicle: "Vehicle", make: str, model: str) -> bool:
    vehicle_make = vehicle.make.lower()
    vehicle_model = _normalize(f"{vehicle.model} {vehicle.trim}")
    return vehicle_make == make.lower() and _phrase_present(_normalize(model), vehicle_model)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def _phrase_present(phrase: str, text: str) -> bool:
    normalized_phrase = _normalize(phrase)
    return re.search(rf"(?<![a-z0-9]){re.escape(normalized_phrase)}(?![a-z0-9])", text) is not None


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output
