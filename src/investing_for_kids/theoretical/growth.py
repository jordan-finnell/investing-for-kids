"""Exponential-growth math for the Theory tab.

Pure functions — no Streamlit, no I/O. Produces the projection chart
and per-year table shown in the Theory tab.
"""

from __future__ import annotations

import pandas as pd

DAYS_PER_YEAR = 365


def _daily_rate(annual_rate: float) -> float:
    """Convert an annual rate into its equivalent daily compounding rate."""
    return (1 + annual_rate) ** (1 / DAYS_PER_YEAR) - 1


def _cadence_to_daily(amount: float, cadence: str) -> float:
    """Smooth a recurring contribution into a per-day amount.

    Weekly → amount / 7; monthly → amount / 30. Smoothing is fine for the
    teaching projection — exact deposit timing doesn't meaningfully change
    the curve.
    """
    if amount <= 0:
        return 0.0
    cadence = cadence.lower()
    if cadence == "weekly":
        return amount / 7
    if cadence == "monthly":
        return amount / 30
    if cadence == "daily":
        return amount
    raise ValueError(f"Unknown cadence: {cadence!r}")


def compounding_series(
    starting_balance: float,
    annual_rate: float,
    days: int,
    daily_contribution: float = 0.0,
) -> pd.DataFrame:
    """Produce a day-by-day balance projection.

    Uses the transaction-then-interest model: each day's contribution is
    added before that day's interest accrues, matching the Accounts module.

    Returns a DataFrame with `days + 1` rows (day 0 is the starting state)
    and columns: `day`, `balance`, `contributions_to_date`, `interest_to_date`.
    """
    dr = _daily_rate(annual_rate)
    balance = float(starting_balance)
    contrib_total = 0.0
    interest_total = 0.0

    rows = [
        {
            "day": 0,
            "balance": balance,
            "contributions_to_date": 0.0,
            "interest_to_date": 0.0,
        }
    ]
    for d in range(1, days + 1):
        balance += daily_contribution
        contrib_total += daily_contribution
        interest = balance * dr
        balance += interest
        interest_total += interest
        rows.append(
            {
                "day": d,
                "balance": balance,
                "contributions_to_date": contrib_total,
                "interest_to_date": interest_total,
            }
        )
    return pd.DataFrame(rows)


def project_growth(
    starting_balance: float,
    annual_rate: float,
    years: int,
    recurring_amount: float = 0.0,
    cadence: str = "monthly",
) -> pd.DataFrame:
    """Project year-end balances across `years` years.

    Returns one row per year from 0 to `years` with columns `year`,
    `balance`, `contributions_to_date`, `interest_to_date`. Contributions
    are smoothed to a daily equivalent so the curve is smooth; year-end
    rows are sampled from the daily series.
    """
    daily_contrib = _cadence_to_daily(recurring_amount, cadence)
    daily = compounding_series(
        starting_balance=starting_balance,
        annual_rate=annual_rate,
        days=years * DAYS_PER_YEAR,
        daily_contribution=daily_contrib,
    )
    yearly = daily.iloc[::DAYS_PER_YEAR].copy()
    yearly["year"] = yearly["day"] // DAYS_PER_YEAR
    return yearly[["year", "balance", "contributions_to_date", "interest_to_date"]].reset_index(
        drop=True
    )
