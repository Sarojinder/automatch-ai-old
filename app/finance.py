from __future__ import annotations

from app.models import FinanceEstimate, Vehicle


def monthly_payment(principal: int, annual_rate: float, months: int) -> float:
    if principal <= 0:
        return 0.0
    if months <= 0:
        raise ValueError("months must be greater than zero")

    monthly_rate = annual_rate / 100 / 12
    if monthly_rate == 0:
        return principal / months

    return principal * monthly_rate / (1 - (1 + monthly_rate) ** -months)


def estimate_financing(
    vehicle: Vehicle,
    down_payment: int = 5000,
    annual_rate: float = 7.99,
    months: int = 60,
) -> FinanceEstimate:
    financed_amount = max(vehicle.price_cad - down_payment, 0)
    payment = monthly_payment(financed_amount, annual_rate, months)
    total_paid = payment * months + min(down_payment, vehicle.price_cad)

    return FinanceEstimate(
        financed_amount=financed_amount,
        monthly_payment=payment,
        total_paid=total_paid,
        total_interest=max(total_paid - vehicle.price_cad, 0),
    )

