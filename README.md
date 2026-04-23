# investing_for_kids

A local-only Streamlit app to help Child A and Child B understand investing — both theoretically (exponential-growth visualizations) and practically (managing simulated investment accounts with daily compounding).

See `starting_vision.md` for the original vision and `plan.md` for the design and implementation plan.

## What it does

**Theory tab** — exponential-growth projections. Set a starting balance, yearly rate, duration, and optional recurring contribution (weekly/monthly); get summary metrics (final balance, money put in, interest earned), a balance-over-time line chart, a principal-vs-interest stacked area, and a year-by-year or month-by-month table (toggle).

**Per-child tabs** (one per account in `accounts.yaml`) — shows current balance, rate, cumulative deposits, and interest earned. Record ad-hoc deposits/withdrawals (withdrawals are rejected if they would drive the balance below zero). Balance history is rendered as a line chart with markers on days that had deposit or withdrawal activity; recent non-zero activity is shown in a table.

## Setup

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install -e .[dev]
```

## Run

```bash
source .venv/bin/activate
streamlit run app.py
```

Opens at http://localhost:8501.

## Dev

```bash
ruff format .
ruff check .
```

## Configuring accounts

`config/accounts.yaml` is the source of truth for every child's account. See `config/accounts_template.yaml` for a fully-commented reference that covers every supported key.

Key points when editing:

- `annual_rate` is stored as a decimal (`0.08` == 8%). Changing it affects **future** ledger rows only; past rows keep their original `rate_applied`, so history stays auditable.
- `recurring_contributions` supports `weekly` (anchor = weekday name, e.g. `monday`) or `monthly` (anchor = day-of-month, `1`–`31`; clamped to the last day of shorter months). Multiple schedules per child are allowed.
- `seed_date` and `seed_balance` are only consulted when the child's ledger CSV doesn't yet exist. Once there's at least one row, the YAML seed fields are ignored — see the *Resetting an account* section below.

Adding a new child is just a new top-level key under `accounts:` — the app picks it up on the next page load and creates a tab automatically.

## How it works

- **Storage**: a CSV per child in `data/ledgers/<child>.csv`, one row per calendar day with columns `date, opening_balance, rate_applied, deposits, contributions, withdrawals, interest, closing_balance`. Human-readable and git-tracked as the backup strategy.
- **Materialization**: each page load calls `materialize_through(today)` per child. It's idempotent — if the ledger is already current it's a no-op; otherwise it appends one row per intervening day.
- **Compounding**: transaction-then-interest. Each day's contributions/deposits are applied first, then `interest = post_txn_balance * ((1 + rate)^(1/365) - 1)` accrues on the post-transaction balance. Same-day deposits earn that same day's interest.
- **Module boundaries**: pure-Python compute (`theoretical/growth.py`, `accounts/ledger.py`, `accounts/transactions.py`, `accounts/config.py`) never imports Streamlit — the `views.py` modules and `ui/layout.py` are the only UI layer.

## Layout

- `app.py` — Streamlit entry point
- `src/investing_for_kids/` — package source
  - `theoretical/growth.py` — pure projection math; `views.py` — Theory tab UI
  - `accounts/` — `config.py` (YAML parse), `ledger.py` (CSV + materialization), `transactions.py` (deposit/withdraw), `views.py` (per-child UI)
  - `ui/layout.py` — top-level tabs, dynamically built from the configured accounts
- `config/accounts.yaml` — per-child rate, seed, recurring contributions
- `config/accounts_template.yaml` — reference documenting every supported key
- `data/ledgers/<child>.csv` — per-child daily ledger (one row per day)

## Resetting an account

Delete the child's ledger CSV:

```bash
rm data/ledgers/child_a.csv
```

The next page load re-seeds the ledger from `config/accounts.yaml` (`seed_date`, `seed_balance`, and current `annual_rate`). No app restart needed.

Caveat: if the account has recurring contributions whose `start_date` is in the past, the re-seeded ledger will back-fill a contribution on every firing date between `start_date` and today. To avoid that, bump each schedule's `start_date` to today (or later) before deleting the CSV.
