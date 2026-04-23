"""Daily-snapshot ledger: read/write CSV, materialize new days, expand recurring.

Each row is one calendar day. Columns:
    date, opening_balance, rate_applied, deposits, contributions,
    withdrawals, interest, closing_balance

No Streamlit — pure pandas + stdlib.
"""

from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from .config import DEFAULT_LEDGERS_DIR, AccountConfig, RecurringContribution

LEDGER_COLUMNS = [
    "date",
    "opening_balance",
    "rate_applied",
    "deposits",
    "contributions",
    "withdrawals",
    "interest",
    "closing_balance",
]

DAYS_PER_YEAR = 365

_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _ledger_path(child: str, ledgers_dir: Path | str) -> Path:
    return Path(ledgers_dir) / f"{child}.csv"


def load_ledger(child: str, ledgers_dir: Path | str = DEFAULT_LEDGERS_DIR) -> pd.DataFrame:
    """Load a child's ledger CSV into a DataFrame. Returns empty frame if missing."""
    path = _ledger_path(child, ledgers_dir)
    if not path.exists():
        return pd.DataFrame(columns=LEDGER_COLUMNS)
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def save_ledger(
    child: str,
    df: pd.DataFrame,
    ledgers_dir: Path | str = DEFAULT_LEDGERS_DIR,
) -> None:
    """Write a ledger DataFrame to CSV with 4-decimal float formatting."""
    path = _ledger_path(child, ledgers_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = df[LEDGER_COLUMNS].copy()
    df["date"] = df["date"].apply(lambda d: d.isoformat() if hasattr(d, "isoformat") else str(d))
    df.to_csv(path, index=False, float_format="%.4f")


def _schedule_dates(s: RecurringContribution, from_date: date, to_date: date) -> Iterator[date]:
    """Yield every date in [from_date, to_date] on which this schedule fires."""
    start = max(s.start_date, from_date)
    end = to_date if s.end_date is None else min(s.end_date, to_date)
    if start > end:
        return

    if s.cadence == "weekly":
        target = _WEEKDAYS.index(str(s.anchor).lower())
        d = start
        while d.weekday() != target:
            d += timedelta(days=1)
            if d > end:
                return
        while d <= end:
            yield d
            d += timedelta(days=7)
    elif s.cadence == "monthly":
        target = int(s.anchor)
        d = start
        while d <= end:
            effective = min(target, monthrange(d.year, d.month)[1])
            if d.day == effective:
                yield d
            d += timedelta(days=1)
    else:
        raise ValueError(f"Unknown cadence: {s.cadence!r}")


def expand_recurring(
    schedules: list[RecurringContribution],
    from_date: date,
    to_date: date,
) -> dict[date, float]:
    """Sum recurring contributions firing on each date in [from_date, to_date]."""
    totals: dict[date, float] = defaultdict(float)
    for s in schedules:
        for d in _schedule_dates(s, from_date, to_date):
            totals[d] += s.amount
    return dict(totals)


def _seed_row(account: AccountConfig) -> dict:
    """Build the first ledger row: full seed deposit, no interest."""
    return {
        "date": account.seed_date,
        "opening_balance": 0.0,
        "rate_applied": account.annual_rate,
        "deposits": account.seed_balance,
        "contributions": 0.0,
        "withdrawals": 0.0,
        "interest": 0.0,
        "closing_balance": account.seed_balance,
    }


def _daily_rate(annual_rate: float) -> float:
    return (1 + annual_rate) ** (1 / DAYS_PER_YEAR) - 1


def materialize_through(
    account: AccountConfig,
    target_date: date,
    ledgers_dir: Path | str = DEFAULT_LEDGERS_DIR,
) -> pd.DataFrame:
    """Ensure the ledger has one row per day from seed_date through target_date.

    Idempotent: if the ledger is already current, returns it unchanged.
    Transaction-then-interest model: recurring contributions on day `d`
    accrue interest that same day.
    """
    df = load_ledger(account.key, ledgers_dir)

    if df.empty:
        df = pd.DataFrame([_seed_row(account)], columns=LEDGER_COLUMNS)
        save_ledger(account.key, df, ledgers_dir)

    last_date = df["date"].iloc[-1]
    if last_date >= target_date:
        return df

    daily_contribs = expand_recurring(
        account.recurring_contributions,
        last_date + timedelta(days=1),
        target_date,
    )

    rate = account.annual_rate
    dr = _daily_rate(rate)
    prev_close = float(df["closing_balance"].iloc[-1])
    rows = df.to_dict("records")

    d = last_date + timedelta(days=1)
    while d <= target_date:
        opening = prev_close
        contributions = float(daily_contribs.get(d, 0.0))
        post_txn = opening + contributions
        interest = post_txn * dr
        closing = post_txn + interest
        rows.append(
            {
                "date": d,
                "opening_balance": opening,
                "rate_applied": rate,
                "deposits": 0.0,
                "contributions": contributions,
                "withdrawals": 0.0,
                "interest": interest,
                "closing_balance": closing,
            }
        )
        prev_close = closing
        d += timedelta(days=1)

    df = pd.DataFrame(rows, columns=LEDGER_COLUMNS)
    save_ledger(account.key, df, ledgers_dir)
    return df
