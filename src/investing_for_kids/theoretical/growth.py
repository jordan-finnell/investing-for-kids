"""Exponential-growth math for the Theory tab.

Pure functions — no Streamlit, no I/O. Produces the projection chart
and per-year table shown in the Theory tab.
"""

from __future__ import annotations

import pandas as pd

DAYS_PER_YEAR = 365

# Recurring contributions fire at fixed-day intervals in the projection:
# monthly ≈ every 30 days (~12 firings/year), bimonthly every 15 days
# (~24 firings/year). The curve will have small steps on firing days —
# that's an honest depiction of discrete deposits and mirrors how the
# Accounts module books contributions in the actual ledger.
CADENCE_INTERVAL_DAYS = {"monthly": 30, "bimonthly": 15}


def _daily_rate(annual_rate: float) -> float:
    """Convert an annual rate into its equivalent daily compounding rate."""
    return (1 + annual_rate) ** (1 / DAYS_PER_YEAR) - 1


def compounding_series(
    starting_balance: float,
    annual_rate: float,
    days: int,
    recurring_amount: float = 0.0,
    cadence: str = "monthly",
) -> pd.DataFrame:
    """Produce a day-by-day balance projection with discrete contributions.

    Transaction-then-interest model: on firing days, the contribution is
    added first, then that day's interest accrues on the post-deposit
    balance (matching the Accounts module).

    Returns a DataFrame with `days + 1` rows (day 0 is the starting state)
    and columns: `day`, `balance`, `contributions_to_date`, `interest_to_date`.
    """
    cadence = cadence.lower()
    if cadence not in CADENCE_INTERVAL_DAYS:
        raise ValueError(f"cadence must be 'monthly' or 'bimonthly', got {cadence!r}")
    interval = CADENCE_INTERVAL_DAYS[cadence]

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
        if recurring_amount > 0 and d % interval == 0:
            balance += recurring_amount
            contrib_total += recurring_amount
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
    `balance`, `contributions_to_date`, `interest_to_date`. Year-end rows
    are sampled from the underlying daily series.
    """
    daily = compounding_series(
        starting_balance=starting_balance,
        annual_rate=annual_rate,
        days=years * DAYS_PER_YEAR,
        recurring_amount=recurring_amount,
        cadence=cadence,
    )
    yearly = daily.iloc[::DAYS_PER_YEAR].copy()
    yearly["year"] = yearly["day"] // DAYS_PER_YEAR
    return yearly[["year", "balance", "contributions_to_date", "interest_to_date"]].reset_index(
        drop=True
    )
