from __future__ import annotations

import argparse
import copy
import csv
import json
import random
from pathlib import Path
from typing import Any

try:
    from import_kaggle_used_vehicles import (
        DEFAULT_OUTPUT as DEFAULT_KAGGLE_OUTPUT,
        ORIGIN_BY_MAKE,
        build_tags,
        clamp,
        estimate_family,
        estimate_fun,
        estimate_horsepower,
        estimate_luxury,
        estimate_ownership_cost,
        estimate_performance,
        estimate_practicality,
        estimate_reliability,
        estimate_seats,
        estimate_winter,
        infer_cylinders,
        infer_features,
        integer,
        normalize_body_style,
        normalize_drivetrain,
        normalize_fuel_type,
        normalize_make,
        normalize_transmission,
        parse_l_per_100km,
        round_to_100,
        slugify,
    )
except ModuleNotFoundError:
    from scripts.import_kaggle_used_vehicles import (
        DEFAULT_OUTPUT as DEFAULT_KAGGLE_OUTPUT,
        ORIGIN_BY_MAKE,
        build_tags,
        clamp,
        estimate_family,
        estimate_fun,
        estimate_horsepower,
        estimate_luxury,
        estimate_ownership_cost,
        estimate_performance,
        estimate_practicality,
        estimate_reliability,
        estimate_seats,
        estimate_winter,
        infer_cylinders,
        infer_features,
        integer,
        normalize_body_style,
        normalize_drivetrain,
        normalize_fuel_type,
        normalize_make,
        normalize_transmission,
        parse_l_per_100km,
        round_to_100,
        slugify,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANUAL_INPUT = ROOT / "data" / "private" / "manual_listings.csv"
DEFAULT_OUTPUT = ROOT / "data" / "private" / "vehicles.hybrid.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a hybrid AutoMatch inventory from dataset, manual, and simulated layers.")
    parser.add_argument("--base", type=Path, default=DEFAULT_KAGGLE_OUTPUT)
    parser.add_argument("--manual", type=Path, default=DEFAULT_MANUAL_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--simulated-count", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    base = load_json(args.base)
    manual = load_manual(args.manual) if args.manual.exists() else []
    simulated = simulate_live_listings(base + manual, count=args.simulated_count, seed=args.seed)
    inventory = dedupe_inventory([*base, *manual, *simulated])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")

    print(f"Base Kaggle listings: {len(base)}")
    print(f"Manual curated listings: {len(manual)}")
    print(f"Simulated live listings: {len(simulated)}")
    print(f"Wrote {len(inventory)} hybrid listings to {args.output}")


def load_json(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def load_manual(path: Path) -> list[dict[str, Any]]:
    vehicles: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for index, row in enumerate(reader):
            normalized = normalize_manual_row({key.strip(): value for key, value in row.items()}, index)
            if normalized:
                vehicles.append(normalized)
    return vehicles


def normalize_manual_row(row: dict[str, str], index: int) -> dict[str, Any] | None:
    year = integer(row.get("year"))
    make = normalize_make(row.get("make", ""))
    model = (row.get("model") or "").strip()
    price = integer(row.get("price_cad"))
    mileage = integer(row.get("mileage_km"))
    if year is None or not make or not model or price is None or mileage is None:
        return None

    body_style = normalize_body_style(row.get("body_style", ""))
    drivetrain = normalize_drivetrain(row.get("drivetrain", ""))
    transmission = normalize_transmission(row.get("transmission", ""))
    fuel_type = normalize_fuel_type(row.get("fuel_type", ""))
    engine = (row.get("engine") or "").strip() or "Unknown"
    cylinders = integer(row.get("cylinders")) or infer_cylinders(engine, model)
    seats = integer(row.get("seats")) or estimate_seats(body_style)
    horsepower = integer(row.get("horsepower")) or estimate_horsepower(engine, cylinders, make, model)
    l_per_100km = float_or_default(row.get("l_per_100km"), parse_l_per_100km("", "", fuel_type))
    feature_set = split_features(row.get("features", ""))
    inferred_features = set(
        infer_features(
            {
                "Body Type": body_style,
                "Engine": engine,
                "Transmission": transmission,
                "Exterior Colour": row.get("exterior_color", ""),
                "Interior Colour": "",
            },
            make,
            model,
            year,
            engine,
            transmission,
        )
    )
    features = sorted(feature_set | inferred_features)

    reliability = float_or_default(row.get("reliability"), estimate_reliability(make))
    performance = float_or_default(row.get("performance"), estimate_performance(horsepower, make, model, body_style, transmission))
    practicality = estimate_practicality(body_style)
    luxury = float_or_default(row.get("luxury"), estimate_luxury(make, row))
    winter = estimate_winter(drivetrain, body_style)
    ownership_cost = float_or_default(row.get("ownership_cost"), estimate_ownership_cost(make, fuel_type, l_per_100km))
    fun = float_or_default(row.get("fun"), estimate_fun(performance, body_style, transmission, model))
    family = float_or_default(row.get("family"), estimate_family(body_style, seats))
    listing_id = (row.get("id") or "").strip() or slugify(f"manual-{index}-{year}-{make}-{model}-{price}")

    return {
        "id": listing_id,
        "make": make,
        "model": model,
        "trim": (row.get("trim") or "Base").strip(),
        "year": year,
        "body_style": body_style,
        "origin": ORIGIN_BY_MAKE.get(make, "Unknown"),
        "price_cad": price,
        "location": (row.get("location") or "Toronto, ON").strip(),
        "country": "Canada",
        "province": (row.get("province") or "ON").strip(),
        "city": (row.get("city") or "Toronto").strip(),
        "mileage_km": mileage,
        "seats": seats,
        "drivetrain": drivetrain,
        "transmission": transmission,
        "horsepower": horsepower,
        "fuel_type": fuel_type,
        "engine": engine,
        "cylinders": cylinders,
        "l_per_100km": l_per_100km,
        "listing_type": (row.get("listing_type") or "Used").strip(),
        "reliability": clamp(reliability),
        "performance": clamp(performance),
        "practicality": practicality,
        "luxury": clamp(luxury),
        "winter": winter,
        "ownership_cost": clamp(ownership_cost),
        "fun": clamp(fun),
        "family": clamp(family),
        "tags": build_tags(make, body_style, fuel_type, drivetrain, performance, family),
        "notes": (row.get("notes") or "Manual curated listing used to simulate real marketplace coverage.").strip(),
        "dealer_name": (row.get("dealer_name") or "Manual Curated Listing").strip(),
        "listing_source": "manual_curated",
        "source_url": (row.get("source_url") or "").strip(),
        "market_average_cad": integer(row.get("market_average_cad")) or price,
        "days_on_market": integer(row.get("days_on_market")) or 8,
        "price_history_cad": [price],
        "accident_history": (row.get("accident_history") or "unknown").strip(),
        "cpo": (row.get("cpo") or "").strip().lower() in {"true", "1", "yes", "y"},
        "features": features,
        "exterior_color": (row.get("exterior_color") or "Unknown").strip(),
    }


def simulate_live_listings(vehicles: list[dict[str, Any]], count: int, seed: int) -> list[dict[str, Any]]:
    clean_pool = [
        vehicle
        for vehicle in vehicles
        if vehicle.get("price_cad", 0) >= 3500 and vehicle.get("mileage_km", 0) >= 0
    ]
    rng = random.Random(seed)
    simulated: list[dict[str, Any]] = []
    for index, vehicle in enumerate(rng.sample(clean_pool, min(count, len(clean_pool)))):
        copy_vehicle = copy.deepcopy(vehicle)
        old_price = int(copy_vehicle["price_cad"])
        adjustment = rng.uniform(-0.055, 0.035)
        new_price = max(3000, round_to_100(old_price * (1 + adjustment)))
        mileage_bump = rng.randint(0, 450)

        copy_vehicle["id"] = f"live-{index}-{copy_vehicle['id']}"
        copy_vehicle["price_cad"] = new_price
        copy_vehicle["mileage_km"] = int(copy_vehicle["mileage_km"]) + mileage_bump
        copy_vehicle["listing_source"] = "simulated_live"
        copy_vehicle["dealer_name"] = "AutoMatch Live Simulator"
        copy_vehicle["days_on_market"] = rng.randint(1, 9)
        copy_vehicle["price_history_cad"] = [old_price, new_price] if old_price != new_price else [new_price]
        copy_vehicle["notes"] = "Simulated fresh listing generated from the imported dataset to mimic marketplace updates."
        simulated.append(copy_vehicle)
    return simulated


def dedupe_inventory(vehicles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_keys: set[tuple[Any, ...]] = set()
    for vehicle in vehicles:
        if vehicle["id"] in seen_ids:
            continue
        key = (
            vehicle["year"],
            vehicle["make"],
            vehicle["model"],
            vehicle["trim"],
            vehicle["mileage_km"],
            vehicle["price_cad"],
            vehicle["listing_source"],
        )
        if key in seen_keys:
            continue
        seen_ids.add(vehicle["id"])
        seen_keys.add(key)
        output.append(vehicle)
    return output


def split_features(value: str) -> set[str]:
    return {item.strip().lower() for item in re_split(value) if item.strip()}


def re_split(value: str) -> list[str]:
    import re

    return re.split(r"[;|,]", value or "")


def float_or_default(value: Any, default: float) -> float:
    if value is None or str(value).strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


if __name__ == "__main__":
    main()
