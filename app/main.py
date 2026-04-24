from __future__ import annotations

import argparse
import json

from app.service import run_recommendation


def run(query: str, limit: int) -> dict:
    return run_recommendation(query, limit=limit)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an AutoMatch AI recommendation query.")
    parser.add_argument("query", help="Natural-language vehicle preference prompt.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum recommendations to return.")
    args = parser.parse_args()

    print(json.dumps(run(args.query, args.limit), indent=2))


if __name__ == "__main__":
    main()
