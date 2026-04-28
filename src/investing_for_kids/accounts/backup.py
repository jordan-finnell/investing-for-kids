"""Advance every configured ledger to today's date."""

from __future__ import annotations

from datetime import date

from investing_for_kids.accounts.config import load_accounts
from investing_for_kids.accounts.ledger import materialize_through


def main() -> None:
    today = date.today()
    for account in load_accounts().values():
        materialize_through(account, today)
        print(f"Advanced {account.key} through {today.isoformat()}")


if __name__ == "__main__":
    main()
