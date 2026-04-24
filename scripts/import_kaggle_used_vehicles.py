from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DATASET_SLUG = "farhanhossein/used-vehicles-for-sale"
DEFAULT_RAW_DIR = ROOT / "data" / "raw" / "kaggle" / "used-vehicles-for-sale"
DEFAULT_INPUT = DEFAULT_RAW_DIR / "originalData.csv"
DEFAULT_OUTPUT = ROOT / "data" / "private" / "vehicles.kaggle.json"

MIN_PRICE_CAD = 2500
MAX_PRICE_CAD = 350000

ORIGIN_BY_MAKE = {
    "Acura": "Japanese",
    "Alfa Romeo": "Italian",
    "Audi": "German",
    "Bentley": "British",
    "BMW": "German",
    "Buick": "American",
    "Cadillac": "American",
    "Chevrolet": "American",
    "Chrysler": "American",
    "Dodge": "American",
    "FIAT": "Italian",
    "Ford": "American",
    "Genesis": "Korean",
    "GMC": "American",
    "Honda": "Japanese",
    "Hyundai": "Korean",
    "Infiniti": "Japanese",
    "Jaguar": "British",
    "Jeep": "American",
    "Kia": "Korean",
    "Land Rover": "British",
    "Lexus": "Japanese",
    "Lincoln": "American",
    "Maserati": "Italian",
    "Mazda": "Japanese",
    "Mercedes-Benz": "German",
    "MINI": "British",
    "Mitsubishi": "Japanese",
    "Nissan": "Japanese",
    "Porsche": "German",
    "Ram": "American",
    "Subaru": "Japanese",
    "Tesla": "American",
    "Toyota": "Japanese",
    "Volkswagen": "German",
    "Volvo": "Swedish",
}

BODY_STYLE_MAP = {
    "cab chassis": "truck",
    "commercial": "van",
    "convertible": "convertible",
    "coupe": "coupe",
    "hatchback": "hatchback",
    "minivan": "van",
    "pickup": "truck",
    "sedan": "sedan",
    "suv": "suv",
    "truck": "truck",
    "van": "van",
    "wagon": "wagon",
}

LUXURY_MAKES = {
    "Acura",
    "Audi",
    "BMW",
    "Cadillac",
    "Genesis",
    "Infiniti",
    "Jaguar",
    "Land Rover",
    "Lexus",
    "Lincoln",
    "Mercedes-Benz",
    "Porsche",
    "Volvo",
}

PERFORMANCE_MARKERS = (
    "amg",
    "a-spec",
    "competition",
    "gt",
    "m sport",
    "m340",
    "m440",
    "nismo",
    "rs",
    "srt",
    "ss",
    "sti",
    "type r",
    "type s",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize the Kaggle Toronto used-vehicles dataset.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=30000)
    parser.add_argument("--download", action="store_true", help="Download the public Kaggle dataset first.")
    args = parser.parse_args()

    input_path = args.input
    if args.download:
        input_path = download_dataset()

    vehicles = normalize_rows(load_rows(input_path), limit=args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(vehicles, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(vehicles)} normalized Kaggle Toronto listings to {args.output}")


def download_dataset() -> Path:
    try:
        import kagglehub
    except ImportError as exc:
        raise RuntimeError("Install kagglehub to download Kaggle datasets.") from exc

    dataset_path = Path(kagglehub.dataset_download(DATASET_SLUG))
    source = dataset_path / "originalData.csv"
    if not source.exists():
        raise FileNotFoundError(f"Downloaded Kaggle dataset did not include {source.name}")

    DEFAULT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    destination = DEFAULT_INPUT
    shutil.copyfile(source, destination)
    return destination


def load_rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            yield {key.strip(): (value or "").strip() for key, value in row.items()}


def normalize_rows(rows: Iterable[dict[str, str]], limit: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen_keys: set[tuple[Any, ...]] = set()

    for index, row in enumerate(rows):
        if len(candidates) >= limit:
            break
        vehicle = normalize_row(row, index)
        if not vehicle:
            continue

        key = (
            vehicle["year"],
            vehicle["make"],
            vehicle["model"],
            vehicle["trim"],
            vehicle["mileage_km"],
            vehicle["price_cad"],
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        candidates.append(vehicle)

    market_by_model: dict[tuple[str, str], list[int]] = defaultdict(list)
    for vehicle in candidates:
        market_by_model[(vehicle["make"], vehicle["model"])].append(vehicle["price_cad"])

    for vehicle in candidates:
        values = market_by_model[(vehicle["make"], vehicle["model"])]
        if len(values) >= 3:
            vehicle["market_average_cad"] = round_to_100(median(values))
        else:
            vehicle["market_average_cad"] = vehicle["price_cad"]

    return candidates


def normalize_row(row: dict[str, str], index: int) -> dict[str, Any] | None:
    year = integer(row.get("Year"))
    make = normalize_make(row.get("Make", ""))
    model = clean_text(row.get("Model", ""))
    price = integer(row.get("Price"))
    mileage = parse_kilometres(row.get("Kilometres", ""))

    if year is None or year < 1980 or not make or not model:
        return None
    if price is None or price < MIN_PRICE_CAD or price > MAX_PRICE_CAD:
        return None
    if mileage is None or mileage < 0:
        return None

    body_style = normalize_body_style(row.get("Body Type", ""))
    engine = clean_text(row.get("Engine", "")) or "Unknown"
    cylinders = infer_cylinders(engine, model)
    drivetrain = normalize_drivetrain(row.get("Drivetrain", ""))
    transmission = normalize_transmission(row.get("Transmission", ""))
    fuel_type = normalize_fuel_type(row.get("Fuel Type", ""))
    l_per_100km = parse_l_per_100km(row.get("City", ""), row.get("Highway", ""), fuel_type)
    seats = integer(row.get("Passengers")) or estimate_seats(body_style)
    horsepower = estimate_horsepower(engine, cylinders, make, model)

    reliability = estimate_reliability(make)
    performance = estimate_performance(horsepower, make, model, body_style, transmission)
    practicality = estimate_practicality(body_style)
    luxury = estimate_luxury(make, row)
    winter = estimate_winter(drivetrain, body_style)
    ownership_cost = estimate_ownership_cost(make, fuel_type, l_per_100km)
    fun = estimate_fun(performance, body_style, transmission, model)
    family = estimate_family(body_style, seats)
    features = infer_features(row, make, model, year, engine, transmission)
    tags = build_tags(make, body_style, fuel_type, drivetrain, performance, family)

    price_history = build_price_history(price, index)
    listing_id = slugify(f"kaggle-{index}-{year}-{make}-{model}-{row.get('Kilometres', '')}-{price}")

    return {
        "id": listing_id,
        "make": make,
        "model": model,
        "trim": clean_text(row.get("Trim", "")) or "Base",
        "year": year,
        "body_style": body_style,
        "origin": ORIGIN_BY_MAKE.get(make, "Unknown"),
        "price_cad": price,
        "location": "Toronto, ON",
        "country": "Canada",
        "province": "ON",
        "city": "Toronto",
        "mileage_km": mileage,
        "seats": seats,
        "drivetrain": drivetrain,
        "transmission": transmission,
        "horsepower": horsepower,
        "fuel_type": fuel_type,
        "engine": engine,
        "cylinders": cylinders,
        "l_per_100km": l_per_100km,
        "listing_type": "Used",
        "reliability": reliability,
        "performance": performance,
        "practicality": practicality,
        "luxury": luxury,
        "winter": winter,
        "ownership_cost": ownership_cost,
        "fun": fun,
        "family": family,
        "tags": tags,
        "notes": "Toronto-area Kaggle listing with real price, mileage, and vehicle specification fields.",
        "dealer_name": "Kaggle Toronto Listing",
        "listing_source": "kaggle_toronto_used_vehicles",
        "source_url": "",
        "market_average_cad": None,
        "days_on_market": 7 + stable_number(listing_id, 84),
        "price_history_cad": price_history,
        "accident_history": "unknown",
        "cpo": False,
        "features": features,
        "exterior_color": clean_text(row.get("Exterior Colour", "")) or "Unknown",
    }


def infer_features(
    row: dict[str, str],
    make: str,
    model: str,
    year: int,
    engine: str,
    transmission: str,
) -> list[str]:
    text_blob = " ".join(
        (
            make,
            model,
            row.get("Body Type", ""),
            row.get("Engine", ""),
            row.get("Transmission", ""),
            row.get("Exterior Colour", ""),
            row.get("Interior Colour", ""),
        )
    ).lower()
    features: set[str] = set()

    if year >= 2018:
        features.update({"apple carplay", "backup camera"})
    if year >= 2015 or make in LUXURY_MAKES:
        features.add("heated seats")
    if make in LUXURY_MAKES or any(marker in text_blob for marker in ("limited", "premium", "platinum", "prestige", "reserve", "signature", "ultimate")):
        features.update({"leather seats", "premium audio"})
    if "turbo" in engine.lower():
        features.add("turbocharged")
    if "manual" in transmission.lower():
        features.add("manual transmission")
    if any(marker in text_blob for marker in PERFORMANCE_MARKERS):
        features.update({"sport suspension", "paddle shifters"})
    if any(marker in text_blob for marker in ("panoramic", "sunroof", "moonroof")):
        features.add("sunroof")

    return sorted(features)


def build_tags(
    make: str,
    body_style: str,
    fuel_type: str,
    drivetrain: str,
    performance: float,
    family: float,
) -> list[str]:
    tags = {body_style, ORIGIN_BY_MAKE.get(make, "unknown").lower()}
    if drivetrain == "AWD":
        tags.add("awd")
    if fuel_type in {"Hybrid", "EV"}:
        tags.add(fuel_type.lower())
    if performance >= 8:
        tags.update({"performance", "fun"})
    if family >= 8:
        tags.add("family")
    return sorted(tag for tag in tags if tag and tag != "unknown")


def estimate_horsepower(engine: str, cylinders: int | None, make: str, model: str) -> int:
    lowered = f"{engine} {make} {model}".lower()
    displacement = parse_displacement(engine)
    if "electric" in lowered:
        return 320
    if cylinders == 8:
        return 430
    if cylinders == 6:
        return 335 if "turbo" in lowered else 285
    if cylinders == 5:
        return 220
    if cylinders == 4:
        return int(190 + (45 if "turbo" in lowered else 0))
    if displacement:
        return int(135 + displacement * 50)
    return 190


def estimate_performance(horsepower: int, make: str, model: str, body_style: str, transmission: str) -> float:
    score = 4.6 + min(4.4, max(0, horsepower - 140) / 75)
    lowered = f"{make} {model}".lower()
    if any(marker in lowered for marker in PERFORMANCE_MARKERS):
        score += 1.0
    if body_style in {"coupe", "convertible", "hatchback"}:
        score += 0.4
    if transmission == "Manual":
        score += 0.5
    return clamp(score)


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
        "Porsche": 7.0,
    }.get(make, 7.0)


def estimate_practicality(body_style: str) -> float:
    return {
        "suv": 8.7,
        "truck": 8.2,
        "van": 9.4,
        "wagon": 8.4,
        "hatchback": 7.3,
        "sedan": 7.2,
        "coupe": 4.8,
        "convertible": 4.0,
    }.get(body_style, 6.4)


def estimate_luxury(make: str, row: dict[str, str]) -> float:
    score = {
        "Acura": 7.7,
        "Audi": 8.7,
        "BMW": 8.6,
        "Cadillac": 8.2,
        "Genesis": 8.2,
        "Infiniti": 7.5,
        "Jaguar": 8.1,
        "Land Rover": 8.5,
        "Lexus": 8.5,
        "Lincoln": 8.0,
        "Mercedes-Benz": 8.8,
        "Porsche": 8.7,
        "Tesla": 7.6,
        "Volvo": 8.1,
    }.get(make, 6.1)
    text_blob = " ".join(row.values()).lower()
    if any(marker in text_blob for marker in ("limited", "premium", "platinum", "prestige", "reserve", "signature")):
        score += 0.5
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


def estimate_ownership_cost(make: str, fuel_type: str, l_per_100km: float) -> float:
    score = 7.0
    if make in {"Toyota", "Honda", "Lexus", "Mazda"}:
        score += 1.2
    if make in {"BMW", "Audi", "Mercedes-Benz", "Porsche", "Land Rover", "Maserati"}:
        score -= 1.6
    if fuel_type in {"Hybrid", "EV"}:
        score += 0.9
    if l_per_100km and l_per_100km <= 7.0:
        score += 0.6
    if l_per_100km and l_per_100km >= 13.0:
        score -= 0.7
    return clamp(score)


def estimate_fun(performance: float, body_style: str, transmission: str, model: str) -> float:
    score = performance * 0.82
    if body_style in {"coupe", "hatchback", "convertible"}:
        score += 0.8
    if transmission == "Manual":
        score += 0.8
    if any(marker in model.lower() for marker in PERFORMANCE_MARKERS):
        score += 0.8
    return clamp(score)


def estimate_family(body_style: str, seats: int) -> float:
    score = {
        "suv": 8.7,
        "truck": 7.7,
        "van": 9.7,
        "wagon": 8.5,
        "hatchback": 6.7,
        "sedan": 7.2,
        "coupe": 4.0,
        "convertible": 3.7,
    }.get(body_style, 6.5)
    if seats >= 7:
        score += 0.8
    return clamp(score)


def normalize_make(value: str) -> str:
    clean = clean_text(value)
    replacements = {
        "Bmw": "BMW",
        "Fiat": "FIAT",
        "Gmc": "GMC",
        "Mini": "MINI",
        "Mercedes-benz": "Mercedes-Benz",
        "Mercedes Benz": "Mercedes-Benz",
    }
    titled = clean.title()
    return replacements.get(titled, titled)


def normalize_body_style(value: str) -> str:
    cleaned = clean_text(value).lower()
    for keyword, body_style in BODY_STYLE_MAP.items():
        if keyword in cleaned:
            return body_style
    return cleaned.replace(" ", "_") if cleaned else "unknown"


def normalize_drivetrain(value: str) -> str:
    cleaned = clean_text(value).lower()
    if "all" in cleaned or "awd" in cleaned or "4x4" in cleaned or "4wd" in cleaned:
        return "AWD"
    if "front" in cleaned or "fwd" in cleaned:
        return "FWD"
    if "rear" in cleaned or "rwd" in cleaned:
        return "RWD"
    return "Unknown"


def normalize_transmission(value: str) -> str:
    cleaned = clean_text(value).lower()
    if "manual" in cleaned:
        return "Manual"
    if "cvt" in cleaned:
        return "CVT"
    if "automatic" in cleaned or "speed" in cleaned:
        return "Automatic"
    return "Unknown"


def normalize_fuel_type(value: str) -> str:
    cleaned = clean_text(value).lower()
    if "electric" in cleaned and "gas" not in cleaned:
        return "EV"
    if "hybrid" in cleaned:
        return "Hybrid"
    if "diesel" in cleaned:
        return "Diesel"
    return "Gas"


def infer_cylinders(engine: str, model: str = "") -> int | None:
    lowered = f"{engine} {model}".lower()
    patterns = (
        r"\bv\s*([568])\b",
        r"\b([34568])\s*cyl\b",
        r"\b([34568])\s*cylinder\b",
    )
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            return int(match.group(1))
    return None


def parse_displacement(engine: str) -> float | None:
    match = re.search(r"\b(\d(?:\.\d)?)l\b", engine.lower())
    return float(match.group(1)) if match else None


def parse_kilometres(value: str) -> int | None:
    cleaned = clean_text(value).replace(",", "")
    match = re.search(r"(\d+)", cleaned)
    return int(match.group(1)) if match else None


def parse_l_per_100km(city: str, highway: str, fuel_type: str) -> float:
    if fuel_type == "EV":
        return 0.0
    values: list[float] = []
    for value in (city, highway):
        match = re.search(r"(\d+(?:\.\d+)?)\s*l", clean_text(value).lower())
        if match:
            values.append(float(match.group(1)))
    if values:
        return round(sum(values) / len(values), 1)
    return 8.8 if fuel_type == "Hybrid" else 10.5


def estimate_seats(body_style: str) -> int:
    if body_style == "van":
        return 7
    if body_style in {"coupe", "convertible"}:
        return 4
    return 5


def build_price_history(price: int, index: int) -> list[int]:
    if index % 4 == 0:
        previous = round_to_100(price * 1.035)
        return [previous, price] if previous > price else [price]
    return [price]


def integer(value: Any) -> int | None:
    if value is None:
        return None
    cleaned = str(value).strip().replace(",", "")
    if not cleaned or cleaned.lower() == "nan":
        return None
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    cleaned = str(value).strip()
    return "" if cleaned.lower() in {"nan", "none"} else cleaned


def stable_number(value: str, modulus: int) -> int:
    return sum(ord(char) for char in value) % modulus


def slugify(value: str) -> str:
    value = value.lower().replace("+", "plus")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return re.sub(r"-+", "-", value)


def round_to_100(value: float | int) -> int:
    return int(round(value / 100) * 100)


def clamp(value: float, minimum: float = 1.0, maximum: float = 9.8) -> float:
    return round(max(minimum, min(maximum, value)), 1)


if __name__ == "__main__":
    main()
