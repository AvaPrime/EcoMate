import math
from .models import Quote

def payback_years(quote: Quote, annual_savings: float) -> float | None:
    if annual_savings <= 0: return None
    return round(quote.total_quote / annual_savings, 2)

def npv(annual_cashflows: list[float], discount_rate: float) -> float:
    return sum(cf / ((1 + discount_rate) ** t) for t, cf in enumerate(annual_cashflows, start=1))

def irr(annual_cashflows: list[float], guess: float = 0.1) -> float | None:
    # simple Newton method
    rate = guess
    for _ in range(100):
        f = sum(cf / ((1 + rate) ** t) for t, cf in enumerate(annual_cashflows, start=1)) - 1
        df = sum(-t * cf / ((1 + rate) ** (t + 1)) for t, cf in enumerate(annual_cashflows, start=1))
        if abs(df) < 1e-8: return None
        new_rate = rate - f/df
        if abs(new_rate - rate) < 1e-6: return rate
        rate = new_rate
    return None