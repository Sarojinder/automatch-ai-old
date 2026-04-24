from __future__ import annotations

from app.models import PreferenceProfile, Recommendation


def summarize_recommendations(
    profile: PreferenceProfile,
    recommendations: list[Recommendation],
) -> str:
    if not recommendations:
        return "I could not find a clean match. Try widening the budget, year range, mileage limit, or origin preference."

    top = recommendations[0]
    budget_part = f" at ${top.vehicle.price_cad:,}"
    focus = _priority_summary(profile)
    return (
        f"My top pick is the {top.vehicle.display_name}{budget_part}. "
        f"It ranks highest because it lines up with {focus} while staying close to the ownership and financing constraints."
    )


def follow_up_questions(profile: PreferenceProfile) -> list[str]:
    questions: list[str] = []
    if profile.budget_max is None:
        questions.append("What is the maximum budget before tax and fees?")
    if not profile.location:
        questions.append("Which city or search area should I prioritize?")
    if "family" not in profile.priorities and "fun" not in profile.priorities:
        questions.append("Should this lean more toward fun driving, family practicality, or low ownership cost?")
    if not profile.origins and not profile.excluded_origins:
        questions.append("Do you care about brand origin, like Japanese reliability or German performance?")
    return questions[:3]


def _priority_summary(profile: PreferenceProfile) -> str:
    if not profile.priorities:
        return "overall value"

    labels = {
        "family": "family practicality",
        "fun": "fun driving",
        "audio": "audio quality",
        "fuel_economy": "fuel economy",
        "luxury": "comfort and luxury",
        "ownership_cost": "lower ownership cost",
        "performance": "performance",
        "practicality": "practicality",
        "reliability": "reliability",
        "value": "value for money",
        "winter": "winter capability",
    }
    top_priorities = sorted(profile.priorities.items(), key=lambda item: item[1], reverse=True)[:3]
    return ", ".join(labels.get(name, name.replace("_", " ")) for name, _ in top_priorities)
