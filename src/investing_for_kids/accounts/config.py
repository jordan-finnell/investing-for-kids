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
    """A repeating deposit schedule (weekly on a weekday, or monthly on a day-of-month)."""

    amount: float
    cadence: str
    anchor: str | int
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


def _parse_recurring(rc: dict[str, Any]) -> RecurringContribution:
    return RecurringContribution(
        amount=float(rc["amount"]),
        cadence=str(rc["cadence"]).lower(),
        anchor=rc["anchor"],
        start_date=_as_date(rc["start_date"]),
        end_date=_as_date(rc["end_date"]) if rc.get("end_date") else None,
    )


def _as_date(value: Any) -> date:
    """PyYAML parses ISO dates to `date` natively; accept string fallback too."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))
