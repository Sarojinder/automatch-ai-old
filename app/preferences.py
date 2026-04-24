from __future__ import annotations

import re
from typing import Any

from app.archetypes import apply_archetypes
from app.models import PreferenceProfile


ORIGIN_KEYWORDS = {
    "japanese": "Japanese",
    "japan": "Japanese",
    "german": "German",
    "germany": "German",
    "korean": "Korean",
    "korea": "Korean",
    "american": "American",
    "usa": "American",
    "swedish": "Swedish",
}

MAKE_KEYWORDS = {
    "acura": "Acura",
    "audi": "Audi",
    "bmw": "BMW",
    "buick": "Buick",
    "cadillac": "Cadillac",
    "chevrolet": "Chevrolet",
    "chevy": "Chevrolet",
    "chrysler": "Chrysler",
    "dodge": "Dodge",
    "ford": "Ford",
    "genesis": "Genesis",
    "gmc": "GMC",
    "honda": "Honda",
    "hyundai": "Hyundai",
    "infiniti": "Infiniti",
    "jeep": "Jeep",
    "kia": "Kia",
    "lexus": "Lexus",
    "lincoln": "Lincoln",
    "mazda": "Mazda",
    "mercedes": "Mercedes-Benz",
    "mercedes-benz": "Mercedes-Benz",
    "mini": "MINI",
    "nissan": "Nissan",
    "porsche": "Porsche",
    "subaru": "Subaru",
    "tesla": "Tesla",
    "toyota": "Toyota",
    "volkswagen": "Volkswagen",
    "vw": "Volkswagen",
    "volvo": "Volvo",
}

BODY_STYLE_KEYWORDS = {
    "coupe": "coupe",
    "sedan": "sedan",
    "suv": "suv",
    "crossover": "suv",
    "truck": "truck",
    "pickup": "truck",
    "van": "van",
    "minivan": "van",
    "convertible": "convertible",
    "hatch": "hatchback",
    "hatchback": "hatchback",
    "wagon": "wagon",
}

FUEL_TYPE_KEYWORDS = {
    "hybrid": "Hybrid",
    "electric": "EV",
    "ev": "EV",
    "diesel": "Diesel",
    "gas": "Gas",
    "gasoline": "Gas",
}

PRIORITY_KEYWORDS = {
    "fun": ("fun", 2.0),
    "sporty": ("fun", 2.0),
    "enthusiast": ("fun", 2.0),
    "quick": ("performance", 1.5),
    "fast": ("performance", 1.5),
    "performance": ("performance", 1.8),
    "reliable": ("reliability", 2.0),
    "reliability": ("reliability", 2.0),
    "low maintenance": ("ownership_cost", 1.6),
    "easy to maintain": ("ownership_cost", 1.8),
    "easy maintenance": ("ownership_cost", 1.8),
    "cheap to own": ("ownership_cost", 1.6),
    "low repair": ("ownership_cost", 1.4),
    "family": ("family", 2.0),
    "kids": ("family", 1.8),
    "practical": ("practicality", 1.6),
    "roomy": ("practicality", 1.6),
    "luxury": ("luxury", 1.8),
    "premium": ("luxury", 1.5),
    "comfortable": ("luxury", 1.2),
    "winter": ("winter", 1.8),
    "snow": ("winter", 1.8),
    "fuel efficient": ("ownership_cost", 1.3),
    "fuel economy": ("fuel_economy", 1.8),
    "gas mileage": ("fuel_economy", 1.8),
    "good on gas": ("fuel_economy", 1.8),
    "great on gas": ("fuel_economy", 2.0),
    "great fuel economy": ("fuel_economy", 2.0),
    "efficient": ("ownership_cost", 1.1),
    "good speakers": ("audio", 2.0),
    "good speaker": ("audio", 2.0),
    "great speakers": ("audio", 2.0),
    "great speaker": ("audio", 2.0),
    "premium audio": ("audio", 2.0),
    "sound system": ("audio", 1.8),
    "stereo": ("audio", 1.6),
    "value": ("value", 1.4),
}

LOCATION_KEYWORDS = (
    "toronto",
    "gta",
    "mississauga",
    "brampton",
    "markham",
    "vaughan",
    "scarborough",
    "oakville",
    "hamilton",
    "ottawa",
    "kitchener",
    "waterloo",
    "london",
    "barrie",
    "montreal",
    "vancouver",
    "calgary",
    "edmonton",
    "winnipeg",
)

CANADIAN_PROVINCE_KEYWORDS = {
    "ontario": "ON",
    "on": "ON",
    "quebec": "QC",
    "qc": "QC",
    "british columbia": "BC",
    "bc": "BC",
    "alberta": "AB",
    "ab": "AB",
    "manitoba": "MB",
    "mb": "MB",
    "saskatchewan": "SK",
    "sk": "SK",
    "nova scotia": "NS",
    "ns": "NS",
    "new brunswick": "NB",
    "nb": "NB",
    "newfoundland": "NL",
    "nl": "NL",
    "pei": "PE",
    "prince edward island": "PE",
}


def parse_preferences(query: str, overrides: dict[str, Any] | None = None) -> PreferenceProfile:
    profile = PreferenceProfile(query=query)
    lowered = query.lower()

    _parse_budget(lowered, profile)
    _parse_price_intent(lowered, profile)
    _parse_years(lowered, profile)
    _parse_mileage(lowered, profile)
    _parse_location(lowered, profile)
    _parse_origins(lowered, profile)
    _parse_makes(lowered, profile)
    _parse_body_styles(lowered, profile)
    _parse_listing_types(lowered, profile)
    _parse_fuel_types(lowered, profile)
    _parse_powertrain(lowered, profile)
    _parse_feature_requirements(lowered, profile)
    _parse_priorities(lowered, profile)
    _parse_financing(lowered, profile)
    _apply_common_intent(lowered, profile)
    apply_archetypes(lowered, profile)

    if overrides:
        _apply_overrides(profile, overrides)

    if not profile.priorities:
        profile.add_priority("value", 1.0)
        profile.add_priority("reliability", 0.8)

    return profile


def _parse_price_intent(text: str, profile: PreferenceProfile) -> None:
    no_budget = any(phrase in text for phrase in ("no budget", "unlimited budget", "money no object"))

    if any(phrase in text for phrase in ("dirt cheap", "beater", "as cheap as possible")):
        profile.budget_max = profile.budget_max or 10000
        profile.budget_flex_pct = max(profile.budget_flex_pct, 0.12)
        profile.add_priority("value", 2.0)
        profile.add_priority("ownership_cost", 1.6)
        profile.add_priority("reliability", 1.0)
        return

    if not no_budget and any(phrase in text for phrase in ("cheap", "budget", "affordable", "low cost")):
        profile.budget_max = profile.budget_max or 20000
        profile.budget_flex_pct = max(profile.budget_flex_pct, 0.10)
        profile.add_priority("value", 1.5)
        profile.add_priority("ownership_cost", 1.2)

    if any(
        phrase in text
        for phrase in (
            "high end",
            "high-end",
            "expensive",
            "really expensive",
            "premium luxury",
            "money no object",
        )
    ):
        profile.budget_min = profile.budget_min or 60000
        profile.add_priority("luxury", 2.0)
        profile.add_priority("performance", 1.0)

    if any(phrase in text for phrase in ("six figure", "six-figure", "exotic", "supercar")):
        profile.budget_min = profile.budget_min or 100000
        profile.add_priority("luxury", 2.5)
        profile.add_priority("performance", 1.8)


def _parse_budget(text: str, profile: PreferenceProfile) -> None:
    under_context = any(word in text for word in ("under", "below", "max", "maximum", "budget"))
    around_context = any(word in text for word in ("around", "about", "roughly", "near"))

    k_amounts = [
        int(match.group(1)) * 1000
        for match in re.finditer(r"\$?\s*(\d{2,3})\s*k\b", text)
        if not _looks_like_mileage_amount(text, match.start(), match.end())
    ]
    full_amounts = [
        int(match.group(1).replace(",", ""))
        for match in re.finditer(r"\$?\s*(\d{2,3},\d{3}|\d{5,6})\b", text)
        if not _looks_like_mileage_amount(text, match.start(), match.end())
    ]
    amounts = k_amounts + full_amounts

    if not amounts:
        return

    budget = max(amounts)
    profile.budget_max = budget
    if under_context:
        profile.budget_flex_pct = 0.02
    elif around_context:
        profile.budget_flex_pct = 0.10


def _looks_like_mileage_amount(text: str, start: int, end: int) -> bool:
    leading_context = text[max(0, start - 24) : start]
    trailing_context = text[end : end + 16]
    if re.match(r"\s*(?:km|kms|kilometers)\b", trailing_context):
        return True
    return "mileage" in leading_context or "odometer" in leading_context


def _parse_years(text: str, profile: PreferenceProfile) -> None:
    if re.search(r"\b2010s\b|\b2010's\b", text):
        profile.year_min = 2010
        profile.year_max = 2019
        return
    if re.search(r"\b2020s\b|\b2020's\b", text):
        profile.year_min = 2020
        profile.year_max = 2029
        return

    years = [int(year) for year in re.findall(r"\b(20[1-3]\d)\b", text)]
    if not years:
        if "old" in text or "older" in text or "older model" in text:
            profile.year_max = 2019
        return

    profile.year_min = min(years)
    profile.year_max = max(years)


def _parse_mileage(text: str, profile: PreferenceProfile) -> None:
    patterns = (
        r"(?:under|below|max|maximum)\s+(\d{1,3})\s*k\s*(?:km|kms|kilometers)\b",
        r"(?:under|below|max|maximum)\s+(\d{1,3}(?:,\d{3})?)\s*(?:km|kms|kilometers)\b",
        r"(?:mileage|odometer).{0,30}(?:under|below|max|maximum)?\s*(\d{1,3})\s*k\b",
        r"\b(\d{1,3})\s*k\s*(?:km|kms|kilometers)\b",
        r"\b(\d{1,3}(?:,\d{3}))\s*(?:km|kms|kilometers)\b",
    )

    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        raw = match.group(1).replace(",", "")
        amount = int(raw)
        profile.max_mileage_km = amount * 1000 if amount < 1000 else amount
        return


def _parse_location(text: str, profile: PreferenceProfile) -> None:
    province_location: str | None = None
    for keyword, province in CANADIAN_PROVINCE_KEYWORDS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            province_location = province
            break

    for keyword in LOCATION_KEYWORDS:
        if keyword in text:
            profile.location = "Toronto" if keyword == "gta" else keyword.title()
            return

    if province_location:
        profile.location = province_location
        return

    match = re.search(r"\b(?:near|around|in)\s+([a-z][a-z .-]{1,28})(?:\b|,)", text)
    if match:
        candidate = match.group(1).strip(" .-")
        stop_words = {
            "a",
            "an",
            "awd",
            "car",
            "cars",
            "coupe",
            "hatchback",
            "hybrid",
            "sedan",
            "suv",
            "truck",
            "van",
        }
        if candidate and candidate not in stop_words:
            profile.location = candidate.title()


def _parse_origins(text: str, profile: PreferenceProfile) -> None:
    for keyword, origin in ORIGIN_KEYWORDS.items():
        if f"no {keyword}" in text or f"not {keyword}" in text or f"avoid {keyword}" in text:
            profile.excluded_origins.add(origin)
        elif keyword in text:
            profile.origins.add(origin)
            if origin == "Japanese":
                profile.add_priority("reliability", 1.2)


def _parse_makes(text: str, profile: PreferenceProfile) -> None:
    for keyword, make in MAKE_KEYWORDS.items():
        pattern = rf"\b{re.escape(keyword)}\b"
        if (
            re.search(rf"\bno\s+{re.escape(keyword)}\b", text)
            or re.search(rf"\bnot\s+{re.escape(keyword)}\b", text)
            or re.search(rf"\bavoid\s+{re.escape(keyword)}\b", text)
        ):
            profile.excluded_makes.add(make)
        elif re.search(pattern, text):
            profile.makes.add(make)


def _parse_body_styles(text: str, profile: PreferenceProfile) -> None:
    for keyword, body_style in BODY_STYLE_KEYWORDS.items():
        if keyword in text:
            profile.body_styles.add(body_style)


def _parse_listing_types(text: str, profile: PreferenceProfile) -> None:
    if re.search(r"\b(?:brand\s+new|new)\b", text):
        profile.listing_types.add("New")
    if re.search(r"\b(?:used|pre-owned|preowned)\b", text):
        profile.listing_types.add("Used")
    if re.search(r"\b(?:cpo|certified|certified\s+pre-owned|certified\s+preowned)\b", text):
        profile.listing_types.add("Certified")


def _parse_fuel_types(text: str, profile: PreferenceProfile) -> None:
    for keyword, fuel_type in FUEL_TYPE_KEYWORDS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            profile.fuel_types.add(fuel_type)
            if fuel_type in {"Hybrid", "EV"}:
                profile.add_priority("fuel_economy", 1.5)
                profile.add_priority("ownership_cost", 0.7)


def _parse_powertrain(text: str, profile: PreferenceProfile) -> None:
    cylinder_patterns = {
        4: r"\b(?:v4|i4|inline\s*4|4\s*cyl(?:inder)?s?)\b",
        6: r"\b(?:v6|i6|inline\s*6|6\s*cyl(?:inder)?s?)\b",
        8: r"\b(?:v8|8\s*cyl(?:inder)?s?)\b",
    }
    for cylinders, pattern in cylinder_patterns.items():
        if re.search(pattern, text):
            profile.engine_cylinders.add(cylinders)

    if "turbo" in text:
        profile.required_features.add("turbocharged")
        profile.add_priority("performance", 0.8)


def _parse_feature_requirements(text: str, profile: PreferenceProfile) -> None:
    feature_keywords = {
        "premium audio": ("premium audio", "audio"),
        "good speakers": ("premium audio", "audio"),
        "good speaker": ("premium audio", "audio"),
        "great speakers": ("premium audio", "audio"),
        "great speaker": ("premium audio", "audio"),
        "sound system": ("premium audio", "audio"),
        "stereo": ("premium audio", "audio"),
        "sunroof": ("sunroof", "luxury"),
        "moonroof": ("sunroof", "luxury"),
        "leather": ("leather seats", "luxury"),
        "heated seats": ("heated seats", "winter"),
        "cooled seats": ("ventilated seats", "luxury"),
        "ventilated seats": ("ventilated seats", "luxury"),
        "carplay": ("apple carplay", "practicality"),
        "apple carplay": ("apple carplay", "practicality"),
        "backup camera": ("backup camera", "practicality"),
        "rear camera": ("rear camera", "practicality"),
        "blind spot": ("blind spot monitoring", "safety"),
        "adaptive cruise": ("adaptive cruise", "safety"),
        "remote start": ("remote start", "winter"),
        "paddle shifters": ("paddle shifters", "fun"),
        "winter tires": ("winter tire package", "winter"),
    }
    for keyword, (feature, priority) in feature_keywords.items():
        if keyword in text:
            profile.required_features.add(feature)
            profile.add_priority(priority, 0.8)

    if "no accident" in text or "no accidents" in text or "clean carfax" in text or "clean history" in text:
        profile.required_accident_history = "none_reported"


def _parse_priorities(text: str, profile: PreferenceProfile) -> None:
    for keyword, (priority, weight) in PRIORITY_KEYWORDS.items():
        if keyword in text:
            profile.add_priority(priority, weight)


def _parse_financing(text: str, profile: PreferenceProfile) -> None:
    down_match = re.search(r"(\d{1,3})\s*k\s+down", text)
    if down_match:
        profile.down_payment = int(down_match.group(1)) * 1000

    month_match = re.search(r"(\d{2,3})\s*(?:months|month|mo)", text)
    if month_match:
        profile.loan_months = int(month_match.group(1))

    rate_match = re.search(r"(\d{1,2}(?:\.\d+)?)\s*%", text)
    if rate_match:
        profile.annual_interest_rate = float(rate_match.group(1))


def _apply_common_intent(text: str, profile: PreferenceProfile) -> None:
    if "awd" in text or "all wheel" in text or "winter" in text or "snow" in text:
        profile.required_drivetrain = "AWD" if "awd" in text or "all wheel" in text else profile.required_drivetrain
        profile.add_priority("winter", 1.0)

    if "manual" in text:
        profile.add_priority("fun", 1.0)

    if "family" in text or "kids" in text:
        profile.seats_min = max(profile.seats_min or 0, 5)
        profile.add_priority("practicality", 1.0)

    if "daily" in text or "commute" in text or "commuter" in text:
        profile.add_priority("ownership_cost", 1.0)
        profile.add_priority("reliability", 0.8)

    if "fast but easy to maintain" in text or "fun but reliable" in text:
        profile.add_priority("performance", 1.0)
        profile.add_priority("reliability", 1.3)
        profile.add_priority("ownership_cost", 1.2)


def _apply_overrides(profile: PreferenceProfile, overrides: dict[str, Any]) -> None:
    scalar_fields = {
        "budget_min",
        "budget_max",
        "budget_flex_pct",
        "location",
        "year_min",
        "year_max",
        "max_mileage_km",
        "required_drivetrain",
        "seats_min",
        "down_payment",
        "annual_interest_rate",
        "loan_months",
    }
    set_fields = {
        "origins",
        "excluded_origins",
        "makes",
        "excluded_makes",
        "body_styles",
        "excluded_body_styles",
        "listing_types",
        "fuel_types",
        "engine_cylinders",
        "required_features",
        "archetypes",
    }

    for field_name in scalar_fields:
        if field_name in overrides and overrides[field_name] is not None:
            setattr(profile, field_name, overrides[field_name])

    for field_name in set_fields:
        if field_name in overrides and overrides[field_name] is not None:
            setattr(profile, field_name, set(overrides[field_name]))

    if "priorities" in overrides and overrides["priorities"]:
        for name, weight in overrides["priorities"].items():
            profile.add_priority(name, float(weight))

    if "required_accident_history" in overrides:
        profile.required_accident_history = overrides["required_accident_history"]
