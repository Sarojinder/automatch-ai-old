from __future__ import annotations

import json
import os
from pathlib import Path

from app.models import Vehicle


DEFAULT_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "vehicles.json"
HYBRID_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "private" / "vehicles.hybrid.json"
KAGGLE_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "private" / "vehicles.kaggle.json"
IMPORTED_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "private" / "vehicles.rebrowser.json"


def load_vehicles(path: Path | str | None = None) -> list[Vehicle]:
    data_path = resolve_data_path(path)
    with data_path.open("r", encoding="utf-8") as vehicle_file:
        records = json.load(vehicle_file)
    return [Vehicle.from_dict(record) for record in records]


def resolve_data_path(path: Path | str | None = None) -> Path:
    env_path = os.environ.get("AUTOMATCH_DATA_PATH")
    if env_path:
        return Path(env_path)

    if path is None:
        for candidate in (HYBRID_DATA_PATH, KAGGLE_DATA_PATH, IMPORTED_DATA_PATH):
            if _has_json_records(candidate):
                return candidate
    return Path(path) if path is not None else DEFAULT_DATA_PATH


def data_source_info(path: Path | str | None = None) -> dict[str, str]:
    resolved = resolve_data_path(path)
    source_types = {
        HYBRID_DATA_PATH: "hybrid_marketplace",
        KAGGLE_DATA_PATH: "kaggle_toronto_used_vehicles",
        IMPORTED_DATA_PATH: "imported_real_listings",
    }
    source_type = source_types.get(resolved, "synthetic_demo")
    return {
        "type": source_type,
        "path": str(resolved),
    }


def _has_json_records(path: Path) -> bool:
    if not path.exists() or path.stat().st_size <= 2:
        return False
    try:
        with path.open("r", encoding="utf-8") as data_file:
            records = json.load(data_file)
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(records, list) and len(records) > 0
