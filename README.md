# investing_for_kids

A local-only Streamlit app to help my kids understand investing — both theoretically (exponential-growth visualizations) and practically (managing simulated investment accounts with daily compounding).

## About this project

I built this for my own children to give them hands-on experience with compound interest: a Theory tab for projections they can play with, and per-child account tabs where they can track real (simulated) balances, record deposits and withdrawals, and watch their money grow day by day.

This is the public portfolio version — account names are replaced with generic placeholders (`Child A`, `Child B`). The family version lives in a separate private repo and continues to be the one we actually use.

See [plans/starting_vision.md](plans/starting_vision.md) for the original brief and [plans/plan.md](plans/plan.md) for the design and implementation plan.

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

`config/accounts.yaml` is the source of truth for every child's account. See [config/accounts_template.yaml](config/accounts_template.yaml) for a fully-commented reference that covers every supported key.

Key points when editing:

- `annual_rate` is stored as a decimal (`0.08` == 8%). Changing it affects **future** ledger rows only; past rows keep their original `rate_applied`, so history stays auditable.
- `recurring_contributions` supports two cadences: `monthly` with `days: [N]` (1 day), or `bimonthly` with `days: [N, M]` (2 days). Every day must be in `1..28` so firings are uniform across months regardless of length. Multiple schedules per child are allowed.
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
- `deck/` — standalone HTML slide deck intro for the kids (reveal.js + Plotly charts)
- `src/investing_for_kids/stocks/` — yfinance data fetch + Plotly chart builders for the deck

## Slide deck

A short intro deck for the kids lives under `deck/` — open `deck/index.html` in a browser to view.

- Six slides (title → hook → what's a stock → Netflix/Nvidia price history → S&P 500 as the safer approach → wrap-up) in a first-person parent voice.
- Charts are pre-rendered interactive Plotly HTML fragments embedded via `<iframe>`.
- Built on [reveal.js](https://revealjs.com/) via CDN — no build step.

### Refreshing the data

The deck's chart data (`deck/data/*.csv`) is committed as a snapshot. To pull fresh prices from yfinance and rebuild the charts:

```bash
uv pip install -e .[deck]
python -m investing_for_kids.stocks.fetch_prices
python -m investing_for_kids.stocks.build_charts
```

The `build_charts` script prints start/end prices and "$100 growth" multipliers — paste the new numbers into `deck/index.html` when they shift meaningfully.

## Resetting an account

Delete the child's ledger CSV:

```bash
rm data/ledgers/child_a.csv
```

The next page load re-seeds the ledger from `config/accounts.yaml` (`seed_date`, `seed_balance`, and current `annual_rate`). No app restart needed.

Caveat: if the account has recurring contributions whose `start_date` is in the past, the re-seeded ledger will back-fill a contribution on every firing date between `start_date` and today. To avoid that, bump each schedule's `start_date` to today (or later) before deleting the CSV.
