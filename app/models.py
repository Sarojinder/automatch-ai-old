from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any


@dataclass(frozen=True)
class Vehicle:
    id: str
    make: str
    model: str
    trim: str
    year: int
    body_style: str
    origin: str
    price_cad: int
    location: str
    mileage_km: int
    seats: int
    drivetrain: str
    transmission: str
    horsepower: int
    fuel_type: str
    l_per_100km: float
    reliability: float
    performance: float
    practicality: float
    luxury: float
    winter: float
    ownership_cost: float
    fun: float
    family: float
    tags: tuple[str, ...]
    notes: str
    country: str = "Canada"
    province: str = "ON"
    city: str = ""
    listing_type: str = "Used"
    dealer_name: str = "Demo Dealer"
    listing_source: str = "synthetic_demo"
    source_url: str = ""
    market_average_cad: int | None = None
    days_on_market: int | None = None
    price_history_cad: tuple[int, ...] = ()
    accident_history: str = "unknown"
    cpo: bool = False
    features: tuple[str, ...] = ()
    engine: str = ""
    cylinders: int | None = None
    exterior_color: str = "Unknown"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Vehicle":
        allowed_fields = {field_info.name for field_info in fields(cls)}
        clean = {key: value for key, value in data.items() if key in allowed_fields}
        clean["tags"] = tuple(clean.get("tags", ()))
        clean["features"] = tuple(clean.get("features", ()))
        clean["price_history_cad"] = tuple(clean.get("price_history_cad", ()))
        return cls(**clean)

    @property
    def display_name(self) -> str:
        return f"{self.year} {self.make} {self.model} {self.trim}".strip()

    @property
    def market_delta_cad(self) -> int | None:
        if self.market_average_cad is None:
            return None
        return self.price_cad - self.market_average_cad


@dataclass
class PreferenceProfile:
    query: str
    budget_min: int | None = None
    budget_max: int | None = None
    budget_flex_pct: float = 0.08
    location: str | None = None
    year_min: int | None = None
    year_max: int | None = None
    max_mileage_km: int | None = None
    origins: set[str] = field(default_factory=set)
    excluded_origins: set[str] = field(default_factory=set)
    makes: set[str] = field(default_factory=set)
    excluded_makes: set[str] = field(default_factory=set)
    body_styles: set[str] = field(default_factory=set)
    excluded_body_styles: set[str] = field(default_factory=set)
    listing_types: set[str] = field(default_factory=set)
    fuel_types: set[str] = field(default_factory=set)
    engine_cylinders: set[int] = field(default_factory=set)
    required_features: set[str] = field(default_factory=set)
    required_accident_history: str | None = None
    required_drivetrain: str | None = None
    seats_min: int | None = None
    archetypes: set[str] = field(default_factory=set)
    priorities: dict[str, float] = field(default_factory=dict)
    down_payment: int = 5000
    annual_interest_rate: float = 7.99
    loan_months: int = 60

    def add_priority(self, name: str, weight: float = 1.0) -> None:
        self.priorities[name] = self.priorities.get(name, 0.0) + weight

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "budget_flex_pct": self.budget_flex_pct,
            "location": self.location,
            "year_min": self.year_min,
            "year_max": self.year_max,
            "max_mileage_km": self.max_mileage_km,
            "origins": sorted(self.origins),
            "excluded_origins": sorted(self.excluded_origins),
            "makes": sorted(self.makes),
            "excluded_makes": sorted(self.excluded_makes),
            "body_styles": sorted(self.body_styles),
            "excluded_body_styles": sorted(self.excluded_body_styles),
            "listing_types": sorted(self.listing_types),
            "fuel_types": sorted(self.fuel_types),
            "engine_cylinders": sorted(self.engine_cylinders),
            "required_features": sorted(self.required_features),
            "required_accident_history": self.required_accident_history,
            "required_drivetrain": self.required_drivetrain,
            "seats_min": self.seats_min,
            "archetypes": sorted(self.archetypes),
            "priorities": dict(sorted(self.priorities.items())),
            "down_payment": self.down_payment,
            "annual_interest_rate": self.annual_interest_rate,
            "loan_months": self.loan_months,
        }


@dataclass(frozen=True)
class FinanceEstimate:
    financed_amount: int
    monthly_payment: float
    total_paid: float
    total_interest: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "financed_amount": self.financed_amount,
            "monthly_payment": round(self.monthly_payment, 2),
            "total_paid": round(self.total_paid, 2),
            "total_interest": round(self.total_interest, 2),
        }


@dataclass(frozen=True)
class Recommendation:
    vehicle: Vehicle
    score: float
    reasons: tuple[str, ...]
    cautions: tuple[str, ...]
    finance: FinanceEstimate
    ml_score: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "vehicle": {
                "id": self.vehicle.id,
                "display_name": self.vehicle.display_name,
                "make": self.vehicle.make,
                "model": self.vehicle.model,
                "trim": self.vehicle.trim,
                "year": self.vehicle.year,
                "body_style": self.vehicle.body_style,
                "origin": self.vehicle.origin,
                "price_cad": self.vehicle.price_cad,
                "location": self.vehicle.location,
                "country": self.vehicle.country,
                "province": self.vehicle.province,
                "city": self.vehicle.city,
                "mileage_km": self.vehicle.mileage_km,
                "seats": self.vehicle.seats,
                "drivetrain": self.vehicle.drivetrain,
                "transmission": self.vehicle.transmission,
                "horsepower": self.vehicle.horsepower,
                "fuel_type": self.vehicle.fuel_type,
                "engine": self.vehicle.engine,
                "cylinders": self.vehicle.cylinders,
                "l_per_100km": self.vehicle.l_per_100km,
                "listing_type": self.vehicle.listing_type,
                "tags": list(self.vehicle.tags),
                "notes": self.vehicle.notes,
                "dealer_name": self.vehicle.dealer_name,
                "listing_source": self.vehicle.listing_source,
                "source_url": self.vehicle.source_url,
                "market_average_cad": self.vehicle.market_average_cad,
                "market_delta_cad": self.vehicle.market_delta_cad,
                "days_on_market": self.vehicle.days_on_market,
                "price_history_cad": list(self.vehicle.price_history_cad),
                "accident_history": self.vehicle.accident_history,
                "cpo": self.vehicle.cpo,
                "features": list(self.vehicle.features),
                "exterior_color": self.vehicle.exterior_color,
            },
            "score": round(min(self.score, 100.0), 2),
            "ml_score": round(self.ml_score, 2) if self.ml_score is not None else None,
            "reasons": list(self.reasons),
            "cautions": list(self.cautions),
            "finance": self.finance.as_dict(),
        }
