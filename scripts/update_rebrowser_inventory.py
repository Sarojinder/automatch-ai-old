from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Any

from import_rebrowser_autotrader import DEFAULT_OUTPUT, load_rows, normalize_rows


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DIR = ROOT / "data" / "raw" / "autotrader-dataset" / "car-listings" / "data"
GITHUB_CONTENTS_API = (
    "https://api.github.com/repos/rebrowser/autotrader-dataset/contents/car-listings/data?ref=main"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download the latest free Rebrowser AutoTrader listing samples from GitHub "
            "and normalize them into AutoMatch inventory JSON."
        )
    )
    parser.add_argument("--days", type=int, default=7, help="Latest daily files to download.")
    parser.add_argument(
        "--format",
        choices=("parquet", "csv"),
        default="parquet",
        help="Dataset file format to download. Parquet contains the actual sample rows.",
    )
    parser.add_argument("--limit", type=int, default=10000, help="Maximum normalized listings to write.")
    parser.add_argument(
        "--states",
        default="NY,MI,PA,OH,IL,MA,VT,NH,ME",
        help="Comma-separated seller states to keep. Use '*' for all states.",
    )
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR, help="Where raw CSV files are cached.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Normalized JSON output path.")
    parser.add_argument("--usd-to-cad", type=float, default=1.35, help="USD to CAD conversion rate.")
    parser.add_argument("--refresh", action="store_true", help="Re-download CSV files even if they already exist.")
    parser.add_argument(
        "--activate",
        action="store_true",
        help="Also copy normalized output to data/vehicles.json for a one-file demo.",
    )
    args = parser.parse_args()

    args.raw_dir.mkdir(parents=True, exist_ok=True)
    latest_files = latest_data_files(args.days, suffix=f".{args.format}")
    if not latest_files:
        raise RuntimeError(f"No {args.format} files were found in the Rebrowser GitHub dataset.")

    downloaded = download_data_files(latest_files, args.raw_dir, refresh=args.refresh)
    states = None if args.states.strip() == "*" else {state.strip().upper() for state in args.states.split(",")}
    vehicles = normalize_rows(load_rows(args.raw_dir), limit=args.limit, states=states, usd_to_cad=args.usd_to_cad)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(vehicles, indent=2) + "\n", encoding="utf-8")

    if args.activate:
        active_path = ROOT / "data" / "vehicles.json"
        shutil.copyfile(args.output, active_path)
        print(f"Activated imported inventory at {active_path}")

    print(f"Downloaded/cached {downloaded} {args.format} file(s) in {args.raw_dir}")
    print(f"Wrote {len(vehicles)} normalized real listings to {args.output}")
    print("Restart the FastAPI server so it loads the new inventory.")


def latest_data_files(days: int, suffix: str) -> list[dict[str, Any]]:
    with urllib.request.urlopen(GITHUB_CONTENTS_API, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    csv_files = [
        item
        for item in payload
        if item.get("type") == "file"
        and str(item.get("name", "")).endswith(suffix)
        and item.get("download_url")
    ]
    return sorted(csv_files, key=lambda item: item["name"])[-days:]


def download_data_files(files: list[dict[str, Any]], raw_dir: Path, refresh: bool = False) -> int:
    count = 0
    for item in files:
        destination = raw_dir / item["name"]
        if destination.exists() and not refresh:
            count += 1
            continue

        print(f"Downloading {item['name']}...", file=sys.stderr)
        with urllib.request.urlopen(item["download_url"], timeout=60) as response:
            destination.write_bytes(response.read())
        count += 1
    return count


if __name__ == "__main__":
    main()
