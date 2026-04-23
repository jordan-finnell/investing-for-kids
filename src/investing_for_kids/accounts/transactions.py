"""Ad-hoc deposits and withdrawals — mutate today's ledger row in place.

The same transaction-then-interest model as daily materialization: a deposit
made today earns today's interest on the post-deposit balance.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from .config import DEFAULT_LEDGERS_DIR, AccountConfig
from .ledger import _daily_rate, materialize_through, save_ledger


def _recompute_row(row: dict) -> tuple[float, float]:
    """Return (interest, closing_balance) recomputed from the row's fields."""
    dr = _daily_rate(float(row["rate_applied"]))
    net = float(row["deposits"]) + float(row["contributions"]) - float(row["withdrawals"])
    post_txn = float(row["opening_balance"]) + net
    interest = post_txn * dr
    return interest, post_txn + interest


def record_deposit(
    account: AccountConfig,
    amount: float,
    ledgers_dir: Path | str = DEFAULT_LEDGERS_DIR,
    today: date | None = None,
) -> None:
    """Add a deposit to today's row; recompute interest and closing balance."""
    if amount <= 0:
        raise ValueError("Deposit amount must be positive")
    today = today or date.today()

    df = materialize_through(account, today, ledgers_dir)
    idx = df.index[-1]
    df.at[idx, "deposits"] = float(df.at[idx, "deposits"]) + amount
    interest, closing = _recompute_row(df.loc[idx].to_dict())
    df.at[idx, "interest"] = interest
    df.at[idx, "closing_balance"] = closing
    save_ledger(account.key, df, ledgers_dir)


def record_withdrawal(
    account: AccountConfig,
    amount: float,
    ledgers_dir: Path | str = DEFAULT_LEDGERS_DIR,
    today: date | None = None,
) -> None:
    """Subtract a withdrawal from today's row; reject if it would drive balance below zero."""
    if amount <= 0:
        raise ValueError("Withdrawal amount must be positive")
    today = today or date.today()

    df = materialize_through(account, today, ledgers_dir)
    idx = df.index[-1]
    trial = df.loc[idx].to_dict()
    trial["withdrawals"] = float(trial["withdrawals"]) + amount
    _, projected_close = _recompute_row(trial)
    if projected_close < 0:
        raise ValueError(
            f"Withdrawal of ${amount:.2f} would drop the balance below zero "
            f"(would close at ${projected_close:.2f})."
        )

    df.at[idx, "withdrawals"] = trial["withdrawals"]
    interest, closing = _recompute_row(df.loc[idx].to_dict())
    df.at[idx, "interest"] = interest
    df.at[idx, "closing_balance"] = closing
    save_ledger(account.key, df, ledgers_dir)
