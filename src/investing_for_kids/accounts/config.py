"""Account configuration — load `config/accounts.yaml` into typed objects.

No Streamlit, no pandas. Pure parse/serialize.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "accounts.yaml"
DEFAULT_LEDGERS_DIR = _PROJECT_ROOT / "data" / "ledgers"


@dataclass
class RecurringContribution:
    """A repeating deposit schedule.

    `cadence` is either "monthly" (fires on one day-of-month) or "bimonthly"
    (fires on two days-of-month). `days` lists the firing days; its length
    must match the cadence (1 for monthly, 2 for bimonthly). Every day must
    be in 1..28 so the schedule fires uniformly regardless of month length.
    """

    amount: float
    cadence: str
    days: list[int]
    start_date: date
    end_date: date | None = None


@dataclass
class AccountConfig:
    """Config for one child's account, loaded from YAML."""

    key: str
    display_name: str
    seed_balance: float
    seed_date: date
    annual_rate: float
    recurring_contributions: list[RecurringContribution] = field(default_factory=list)


def load_accounts(path: Path | str = DEFAULT_CONFIG_PATH) -> dict[str, AccountConfig]:
    """Load account configs from a YAML file, keyed by account key."""
    path = Path(path)
    with path.open() as f:
        raw = yaml.safe_load(f) or {}
    accounts_raw = raw.get("accounts", {}) or {}
    return {key: _parse_account(key, data) for key, data in accounts_raw.items()}


def _parse_account(key: str, data: dict[str, Any]) -> AccountConfig:
    return AccountConfig(
        key=key,
        display_name=data["display_name"],
        seed_balance=float(data["seed_balance"]),
        seed_date=_as_date(data["seed_date"]),
        annual_rate=float(data["annual_rate"]),
        recurring_contributions=[
            _parse_recurring(rc) for rc in (data.get("recurring_contributions") or [])
        ],
    )


_EXPECTED_DAYS = {"monthly": 1, "bimonthly": 2}


def _parse_recurring(rc: dict[str, Any]) -> RecurringContribution:
    cadence = str(rc["cadence"]).lower()
    if cadence not in _EXPECTED_DAYS:
        raise ValueError(
            f"recurring_contributions.cadence must be 'monthly' or 'bimonthly', got {cadence!r}"
        )
    days = [int(d) for d in rc["days"]]
    expected = _EXPECTED_DAYS[cadence]
    if len(days) != expected:
        raise ValueError(
            f"{cadence} cadence requires exactly {expected} day(s) in `days`, got {days}"
        )
    for d in days:
        if not 1 <= d <= 28:
            raise ValueError(
                f"recurring_contributions.days must be between 1 and 28 "
                f"(so the schedule fires regardless of month length), got {d}"
            )
    return RecurringContribution(
        amount=float(rc["amount"]),
        cadence=cadence,
        days=days,
        start_date=_as_date(rc["start_date"]),
        end_date=_as_date(rc["end_date"]) if rc.get("end_date") else None,
    )


def _as_date(value: Any) -> date:
    """PyYAML parses ISO dates to `date` natively; accept string fallback too."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))
