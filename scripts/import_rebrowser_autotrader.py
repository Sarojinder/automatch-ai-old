from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "raw" / "autotrader-dataset" / "car-listings" / "data"
DEFAULT_OUTPUT = ROOT / "data" / "private" / "vehicles.rebrowser.json"

USD_TO_CAD = 1.35
MILES_TO_KM = 1.60934
MIN_VALID_PRICE_USD = 2500

ORIGIN_BY_MAKE = {
    "Acura": "Japanese",
    "Audi": "German",
    "BMW": "German",
    "Buick": "American",
    "Cadillac": "American",
    "Chevrolet": "American",
    "Chrysler": "American",
    "Dodge": "American",
    "Ford": "American",
    "Genesis": "Korean",
    "GMC": "American",
    "Honda": "Japanese",
    "Hyundai": "Korean",
    "Infiniti": "Japanese",
    "Jeep": "American",
    "Kia": "Korean",
    "Lexus": "Japanese",
    "Lincoln": "American",
    "Mazda": "Japanese",
    "Mercedes-Benz": "German",
    "MINI": "British",
    "Nissan": "Japanese",
    "Porsche": "German",
    "Subaru": "Japanese",
    "Tesla": "American",
    "Toyota": "Japanese",
    "Volkswagen": "German",
    "Volvo": "Swedish",
}

BODY_STYLE_MAP = {
    "CONVERTIBLE": "convertible",
    "CONVERT": "convertible",
    "COUPE": "coupe",
    "HATCH": "hatchback",
    "HATCHBACK": "hatchback",
    "SEDAN": "sedan",
    "SUV": "suv",
    "SPORT UTILITY": "suv",
    "TRUCK": "truck",
    "TRUCKS": "truck",
    "VAN": "van",
    "VANS": "van",
    "WAGON": "wagon",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize Rebrowser AutoTrader CSV exports into AutoMatch inventory JSON."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="CSV file or directory of CSV files.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSON file.")
    parser.add_argument("--limit", type=int, default=2000, help="Maximum normalized listings to write.")
    parser.add_argument(
        "--states",
        default="NY,MI,PA,OH,IL,MA,VT,NH,ME",
        help="Comma-separated seller states to keep. Use '*' for all states.",
    )
    parser.add_argument("--usd-to-cad", type=float, default=USD_TO_CAD, help="USD to CAD conversion rate.")
    args = parser.parse_args()

    states = None if args.states.strip() == "*" else {state.strip().upper() for state in args.states.split(",")}
    records = list(load_rows(args.input))
    vehicles = normalize_rows(records, limit=args.limit, states=states, usd_to_cad=args.usd_to_cad)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(vehicles, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(vehicles)} normalized Rebrowser listings to {args.output}")


def load_rows(path: Path) -> Iterable[dict[str, str]]:
    files = [path] if path.is_file() else sorted([*path.glob("*.csv"), *path.glob("*.parquet")])
    if not files:
        raise FileNotFoundError(f"No CSV or Parquet files found at {path}")

    for data_path in files:
        if data_path.suffix.lower() == ".parquet":
            yield from load_parquet_rows(data_path)
            continue

        with data_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row:
                    yield row


def load_parquet_rows(path: Path) -> Iterable[dict[str, str]]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("Install pandas and pyarrow to import Parquet listing files.") from exc

    try:
        frame = pd.read_parquet(path)
    except ImportError as exc:
        raise RuntimeError("Install pyarrow to import Parquet listing files.") from exc

    for row in frame.to_dict(orient="records"):
        yield {key: "" if value is None else value for key, value in row.items()}


def normalize_rows(
    rows: Iterable[dict[str, str]],
    limit: int,
    states: set[str] | None,
    usd_to_cad: float,
) -> list[dict[str, Any]]:
    vehicles: list[dict[str, Any]] = []
    seen_listing_ids: set[str] = set()
    seen_inventory_keys: set[tuple[Any, ...]] = set()

    for row in rows:
        if len(vehicles) >= limit:
            break
        if not should_keep(row, states):
            continue

        listing_id = text(row, "listingId") or text(row, "_primaryKey")
        if listing_id in seen_listing_ids:
            continue
        seen_listing_ids.add(listing_id)

        vehicle = normalize_row(row, usd_to_cad)
        if not vehicle:
            continue

        inventory_key = (
            vehicle["year"],
            vehicle["make"],
            vehicle["model"],
            vehicle["trim"],
            vehicle["city"],
            vehicle["mileage_km"],
            vehicle["price_cad"],
        )
        if inventory_key in seen_inventory_keys:
            continue
        seen_inventory_keys.add(inventory_key)
        vehicles.append(vehicle)

    return vehicles


def should_keep(row: dict[str, str], states: set[str] | None) -> bool:
    if states is not None and text(row, "sellerState").upper() not in states:
        return False
    if listing_price_usd(row) is None:
        return False
    if int_or_none(row, "year") is None:
        return False
    if not text(row, "makeName") or not text(row, "modelName"):
        return False
    return True


def normalize_row(row: dict[str, str], usd_to_cad: float) -> dict[str, Any] | None:
    year = int_or_none(row, "year")
    sale_price_usd = listing_price_usd(row)
    mileage_miles = numeric(row, "mileage")
    if year is None or sale_price_usd is None or mileage_miles is None:
        return None

    make = normalize_make(text(row, "makeName"))
    model = text(row, "modelName") or text(row, "modelCode")
    trim = clean_premium(text(row, "trim")) or "Base"
    body_style = normalize_body_style(text(row, "bodyStyle"))
    fuel_type = normalize_fuel_type(text(row, "fuelTypeGroup") or text(row, "fuelType"))
    drivetrain = normalize_drivetrain(text(row, "drivetrain"))
    transmission = text(row, "transmissionGroup") or normalize_transmission(text(row, "transmission"))
    listing_type = text(row, "listingType")
    kbb_fair_usd = market_average_usd(row)
    engine = normalize_engine(row)
    cylinders = infer_cylinders(row)
    normalized_listing_type = normalize_listing_type(listing_type)

    if normalized_listing_type != "New" and mileage_miles <= 0:
        return None

    price_cad = to_cad(sale_price_usd, usd_to_cad)
    if price_cad < to_cad(MIN_VALID_PRICE_USD, usd_to_cad):
        return None

    market_average_cad = to_cad(kbb_fair_usd, usd_to_cad) if kbb_fair_usd is not None else None
    mileage_km = int(round(mileage_miles * MILES_TO_KM))

    reliability = estimate_reliability(make)
    performance = estimate_performance(row)
    practicality = estimate_practicality(body_style)
    luxury = estimate_luxury(make, row)
    winter = estimate_winter(drivetrain, body_style)
    ownership_cost = estimate_ownership_cost(make, fuel_type, row)
    fun = estimate_fun(performance, body_style, transmission)
    family = estimate_family(body_style)

    tags = build_tags(make, body_style, fuel_type, drivetrain, listing_type, performance, family)
    features = build_features(row)

    return {
        "id": make_id(listing_id=text(row, "listingId"), year=year, make=make, model=model, trim=trim),
        "make": make,
        "model": model,
        "trim": trim,
        "year": year,
        "body_style": body_style,
        "origin": ORIGIN_BY_MAKE.get(make, "Unknown"),
        "price_cad": price_cad,
        "location": location_label(row),
        "country": "United States",
        "province": clean_premium(text(row, "sellerState")),
        "city": clean_premium(text(row, "sellerCity")),
        "mileage_km": mileage_km,
        "seats": estimate_seats(body_style),
        "drivetrain": drivetrain,
        "transmission": transmission,
        "horsepower": estimate_horsepower(row),
        "fuel_type": fuel_type,
        "engine": engine,
        "cylinders": cylinders,
        "l_per_100km": estimate_l_per_100km(row),
        "listing_type": normalized_listing_type,
        "reliability": reliability,
        "performance": performance,
        "practicality": practicality,
        "luxury": luxury,
        "winter": winter,
        "ownership_cost": ownership_cost,
        "fun": fun,
        "family": family,
        "tags": tags,
        "notes": build_notes(row, market_average_cad),
        "dealer_name": clean_premium(text(row, "sellerName")) or "Rebrowser Listing",
        "listing_source": "rebrowser_autotrader",
        "source_url": clean_premium(text(row, "listingUrl")),
        "market_average_cad": market_average_cad,
        "days_on_market": int_or_none(row, "daysOnMarket"),
        "price_history_cad": build_price_history(price_cad, row, usd_to_cad),
        "accident_history": accident_history_from_vhr(text(row, "vhrPreview")),
        "cpo": listing_type.lower() == "certified",
        "features": features,
        "exterior_color": clean_premium(text(row, "exteriorColor")) or "Unknown",
    }


def build_price_history(price_cad: int, row: dict[str, str], usd_to_cad: float) -> list[int]:
    if bool_value(row, "isReducedPrice"):
        previous = price_cad + max(500, int(price_cad * 0.035))
        return [round_to_100(previous), price_cad]
    return [price_cad]


def build_features(row: dict[str, str]) -> list[str]:
    features: set[str] = set()
    if bool_value(row, "hasLeatherSeats"):
        features.add("leather seats")
    if bool_value(row, "moneyBackGuarantee"):
        features.add("money-back guarantee")
    if bool_value(row, "hasSpecialOffer"):
        features.add("special offer")
    if bool_value(row, "isNoHagglePrice"):
        features.add("no-haggle price")
    if bool_value(row, "isReducedPrice"):
        features.add("recent price drop")

    options_text = " ".join(
        (
            text(row, "options"),
            text(row, "description"),
            text(row, "listingTitle"),
            text(row, "engine"),
            text(row, "transmission"),
        )
    ).lower()
    for keyword, label in {
        "adaptive cruise": "adaptive cruise",
        "apple carplay": "apple carplay",
        "heated": "heated seats",
        "heated steering": "heated steering wheel",
        "cooled": "ventilated seats",
        "ventilated": "ventilated seats",
        "backup": "backup camera",
        "rear camera": "backup camera",
        "blind": "blind spot monitoring",
        "cruise": "adaptive cruise",
        "sunroof": "sunroof",
        "moonroof": "sunroof",
        "navigation": "navigation",
        "bluetooth": "bluetooth",
        "bose": "premium audio",
        "burmester": "premium audio",
        "harman": "premium audio",
        "jbl": "premium audio",
        "mark levinson": "premium audio",
        "meridian": "premium audio",
        "premium audio": "premium audio",
        "turbo": "turbocharged",
    }.items():
        if keyword in options_text:
            features.add(label)

    return sorted(features)


def build_tags(
    make: str,
    body_style: str,
    fuel_type: str,
    drivetrain: str,
    listing_type: str,
    performance: float,
    family: float,
) -> list[str]:
    tags = {body_style, ORIGIN_BY_MAKE.get(make, "unknown").lower()}
    if drivetrain == "AWD":
        tags.add("awd")
    if fuel_type in {"Hybrid", "EV"}:
        tags.add(fuel_type.lower())
    if listing_type.lower() == "certified":
        tags.add("cpo")
    if performance >= 8:
        tags.add("performance")
        tags.add("fun")
    if family >= 8:
        tags.add("family")
    return sorted(tag for tag in tags if tag and tag != "unknown")


def build_notes(row: dict[str, str], market_average_cad: int | None) -> str:
    deal = text(row, "dealIndicator")
    rating = numeric(row, "sellerRating")
    pieces: list[str] = []
    if deal:
        pieces.append(f"KBB deal indicator: {deal}.")
    if numeric(row, "salePrice") is None and listing_price_usd(row) is not None:
        pieces.append("Sale price is estimated from the free sample's KBB price range.")
    if market_average_cad:
        pieces.append("Includes KBB fair purchase price for market comparison.")
    if rating:
        pieces.append(f"Seller rating: {rating:.1f}/5.")
    return " ".join(pieces) or "Imported from the Rebrowser AutoTrader dataset."


def accident_history_from_vhr(vhr_preview: str) -> str:
    lowered = vhr_preview.lower()
    if "no_accidents_reported" in lowered or "no accidents" in lowered:
        return "none_reported"
    if "accident" in lowered:
        return "minor_reported"
    return "unknown"


def normalize_make(make: str) -> str:
    replacements = {
        "Mercedes-benz": "Mercedes-Benz",
        "Mini": "MINI",
    }
    clean = clean_premium(make).title()
    return replacements.get(clean, clean)


def normalize_body_style(value: str) -> str:
    cleaned = clean_premium(value).upper()
    return BODY_STYLE_MAP.get(cleaned, cleaned.lower() or "unknown")


def normalize_fuel_type(value: str) -> str:
    cleaned = clean_premium(value).lower()
    if "electric" in cleaned and "gas" in cleaned:
        return "Hybrid"
    if "electric" in cleaned:
        return "EV"
    if "diesel" in cleaned:
        return "Diesel"
    if "hybrid" in cleaned:
        return "Hybrid"
    return "Gas"


def normalize_listing_type(value: str) -> str:
    lowered = clean_premium(value).lower()
    if "certified" in lowered:
        return "Certified"
    if "new" == lowered:
        return "New"
    return "Used"


def normalize_drivetrain(value: str) -> str:
    cleaned = clean_premium(value).lower()
    if "all" in cleaned or "awd" in cleaned or "4" in cleaned:
        return "AWD"
    if "front" in cleaned or "fwd" in cleaned:
        return "FWD"
    if "rear" in cleaned or "rwd" in cleaned:
        return "RWD"
    return "Unknown"


def normalize_transmission(value: str) -> str:
    lowered = clean_premium(value).lower()
    if "manual" in lowered:
        return "Manual"
    if "automatic" in lowered or lowered:
        return "Automatic"
    return "Unknown"


def normalize_engine(row: dict[str, str]) -> str:
    engine = clean_premium(text(row, "engine"))
    if engine:
        return engine

    engine_code = clean_premium(text(row, "engineCode")).upper()
    cylinders = infer_cylinders(row)
    if cylinders:
        suffix = "Turbo" if "T" in engine_code else ""
        return f"{cylinders}-Cylinder {suffix}".strip()

    fuel_type = normalize_fuel_type(text(row, "fuelTypeGroup") or text(row, "fuelType"))
    if fuel_type == "EV":
        return "Electric"
    return "Unknown"


def infer_cylinders(row: dict[str, str]) -> int | None:
    engine_text = " ".join((text(row, "engine"), text(row, "engineCode"), text(row, "listingTitle"))).lower()
    patterns = (
        r"\b([34568])\s*[- ]?cylinder\b",
        r"\b([34568])\s*cyl\b",
        r"\b([34568])cldr\b",
        r"\bi\s*([34568])\b",
        r"\bv\s*([568])\b",
    )
    for pattern in patterns:
        match = re.search(pattern, engine_text)
        if match:
            return int(match.group(1))
    return None


def estimate_l_per_100km(row: dict[str, str]) -> float:
    fuel_type = normalize_fuel_type(text(row, "fuelTypeGroup") or text(row, "fuelType"))
    if fuel_type == "EV":
        return 0.0

    city = numeric(row, "mpgCity")
    highway = numeric(row, "mpgHighway")
    mpg_values = [value for value in (city, highway) if value and value > 0]
    if not mpg_values:
        return 8.8 if fuel_type == "Hybrid" else 10.5

    combined_mpg = sum(mpg_values) / len(mpg_values)
    return round(235.214583 / combined_mpg, 1)


def estimate_horsepower(row: dict[str, str]) -> int:
    engine = text(row, "engine").lower()
    displacement = numeric(row, "displacementUOM") or 2.0
    fuel_type = normalize_fuel_type(text(row, "fuelTypeGroup") or text(row, "fuelType"))
    if fuel_type == "EV":
        return 320
    if "8-cylinder" in engine or "8 cyl" in engine:
        return 420
    if "6-cylinder" in engine or "6 cyl" in engine:
        return 330 if "turbo" in engine else 285
    if "turbo" in engine:
        return int(190 + displacement * 45)
    return int(145 + displacement * 35)


def estimate_reliability(make: str) -> float:
    return {
        "Toyota": 9.2,
        "Lexus": 9.1,
        "Honda": 8.8,
        "Acura": 8.2,
        "Mazda": 8.4,
        "Subaru": 7.8,
        "BMW": 6.9,
        "Audi": 6.7,
        "Mercedes-Benz": 6.5,
        "Volkswagen": 7.0,
        "Genesis": 7.5,
        "Hyundai": 7.6,
        "Kia": 7.4,
        "Tesla": 7.0,
    }.get(make, 7.0)


def estimate_performance(row: dict[str, str]) -> float:
    horsepower = estimate_horsepower(row)
    score = 4.8 + min(4.5, max(0, horsepower - 150) / 70)
    title = text(row, "listingTitle").lower()
    if any(token in title for token in ("amg", "m sport", "type r", "type s", "gt", "sport", "performance")):
        score += 0.8
    return clamp(score)


def estimate_practicality(body_style: str) -> float:
    return {
        "suv": 8.7,
        "truck": 8.4,
        "van": 9.4,
        "wagon": 8.5,
        "hatchback": 7.4,
        "sedan": 7.2,
        "coupe": 4.9,
        "convertible": 4.3,
    }.get(body_style, 6.5)


def estimate_luxury(make: str, row: dict[str, str]) -> float:
    score = {
        "Acura": 7.7,
        "Audi": 8.7,
        "BMW": 8.6,
        "Cadillac": 8.2,
        "Genesis": 8.2,
        "Infiniti": 7.5,
        "Lexus": 8.5,
        "Lincoln": 8.0,
        "Mercedes-Benz": 8.8,
        "Porsche": 8.7,
        "Tesla": 7.6,
        "Volvo": 8.1,
    }.get(make, 6.2)
    if bool_value(row, "hasLeatherSeats"):
        score += 0.6
    return clamp(score)


def estimate_winter(drivetrain: str, body_style: str) -> float:
    score = 5.2
    if drivetrain == "AWD":
        score += 3.0
    if body_style in {"suv", "truck", "wagon"}:
        score += 0.6
    if drivetrain == "RWD":
        score -= 1.2
    return clamp(score)


def estimate_ownership_cost(make: str, fuel_type: str, row: dict[str, str]) -> float:
    score = 7.0
    if make in {"Toyota", "Honda", "Lexus", "Mazda"}:
        score += 1.2
    if make in {"BMW", "Audi", "Mercedes-Benz", "Porsche"}:
        score -= 1.6
    if fuel_type in {"Hybrid", "EV"}:
        score += 0.9
    if (numeric(row, "safetyRecallCount") or 0) > 0:
        score -= 0.4
    return clamp(score)


def estimate_fun(performance: float, body_style: str, transmission: str) -> float:
    score = performance * 0.82
    if body_style in {"coupe", "hatchback", "convertible"}:
        score += 0.8
    if transmission == "Manual":
        score += 0.8
    return clamp(score)


def estimate_family(body_style: str) -> float:
    return {
        "suv": 8.8,
        "truck": 7.8,
        "van": 9.7,
        "wagon": 8.6,
        "hatchback": 6.7,
        "sedan": 7.2,
        "coupe": 4.0,
        "convertible": 3.8,
    }.get(body_style, 6.5)


def estimate_seats(body_style: str) -> int:
    if body_style == "van":
        return 7
    if body_style in {"suv", "truck"}:
        return 5
    if body_style in {"coupe", "convertible"}:
        return 4
    return 5


def location_label(row: dict[str, str]) -> str:
    city = clean_premium(text(row, "sellerCity"))
    state = clean_premium(text(row, "sellerState"))
    if city and state:
        return f"{city}, {state}"
    return city or state or "Unknown"


def make_id(listing_id: str, year: int, make: str, model: str, trim: str) -> str:
    raw = listing_id or f"{year}-{make}-{model}-{trim}"
    return slugify(raw)


def slugify(value: str) -> str:
    value = value.lower().replace("+", "plus")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return re.sub(r"-+", "-", value)


def text(row: dict[str, str], field_name: str) -> str:
    value = row.get(field_name)
    return "" if value is None else str(value).strip()


def clean_premium(value: str) -> str:
    return "" if value == "[PREMIUM]" else value.strip()


def numeric(row: dict[str, str], field_name: str) -> float | None:
    value = clean_premium(text(row, field_name)).replace(",", "")
    if not value:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return None if math.isnan(number) else number


def positive_price(value: float | None) -> float | None:
    if value is None or value < MIN_VALID_PRICE_USD:
        return None
    return value


def listing_price_usd(row: dict[str, str]) -> float | None:
    sale_price = positive_price(numeric(row, "salePrice"))
    if sale_price is not None:
        return sale_price

    if normalize_listing_type(text(row, "listingType")) == "New":
        msrp = positive_price(numeric(row, "msrp"))
        if msrp is not None:
            return msrp

    return market_average_usd(row)


def market_average_usd(row: dict[str, str]) -> float | None:
    fair_price = positive_price(numeric(row, "kbbFairPurchasePrice"))
    if fair_price is not None:
        return fair_price

    low = positive_price(numeric(row, "kbbFairPriceLow"))
    high = positive_price(numeric(row, "kbbFairPriceHigh"))
    if low is not None and high is not None:
        return (low + high) / 2
    return low if low is not None else high


def int_or_none(row: dict[str, str], field_name: str) -> int | None:
    value = numeric(row, field_name)
    return int(value) if value is not None else None


def bool_value(row: dict[str, str], field_name: str) -> bool:
    return text(row, field_name).lower() in {"true", "1", "yes", "y"}


def to_cad(value: float, usd_to_cad: float) -> int:
    return round_to_100(value * usd_to_cad)


def round_to_100(value: float | int) -> int:
    return int(round(value / 100) * 100)


def clamp(value: float, minimum: float = 1.0, maximum: float = 9.8) -> float:
    return round(max(minimum, min(maximum, value)), 1)


if __name__ == "__main__":
    main()
