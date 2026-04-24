from __future__ import annotations

from typing import Any

from app.assistant import follow_up_questions, summarize_recommendations
from app.data_loader import data_source_info, load_vehicles
from app.ml_ranker import model_status
from app.preferences import parse_preferences
from app.recommender import recommend_vehicles


VEHICLES = load_vehicles()
DATA_SOURCE = data_source_info()


def run_recommendation(
    query: str,
    limit: int = 5,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = parse_preferences(query, overrides=overrides)
    recommendations = recommend_vehicles(VEHICLES, profile, limit=limit)
    return {
        "interpreted_preferences": profile.as_dict(),
        "summary": summarize_recommendations(profile, recommendations),
        "follow_up_questions": follow_up_questions(profile),
        "model": model_status(),
        "data_source": DATA_SOURCE,
        "recommendations": [recommendation.as_dict() for recommendation in recommendations],
    }


def vehicle_summaries() -> list[dict[str, Any]]:
    return [
        {
            "id": vehicle.id,
            "display_name": vehicle.display_name,
            "price_cad": vehicle.price_cad,
            "location": vehicle.location,
            "country": vehicle.country,
            "province": vehicle.province,
            "city": vehicle.city,
            "mileage_km": vehicle.mileage_km,
            "origin": vehicle.origin,
            "body_style": vehicle.body_style,
            "listing_type": vehicle.listing_type,
            "dealer_name": vehicle.dealer_name,
            "listing_source": vehicle.listing_source,
            "market_average_cad": vehicle.market_average_cad,
            "market_delta_cad": vehicle.market_delta_cad,
            "days_on_market": vehicle.days_on_market,
            "cpo": vehicle.cpo,
            "tags": list(vehicle.tags),
        }
        for vehicle in VEHICLES
    ]
