1# Plan: Build the `investing_for_kids` Streamlit app

## Context

The project is currently greenfield — only `CLAUDE.md`, `.gitignore`, and `starting_vision.md` exist. The goal (from `starting_vision.md`) is a local-only Streamlit app that teaches Child A and Child B about investing through (1) theoretical visualizations of exponential growth and (2) two simulated investment accounts with daily compounding, transactions, and balance history. No real money is managed — the accounts are an accounting/teaching tool.

Confirmed design decisions (from clarifying questions in-session):

- **Storage**: CSV-per-child daily ledger + single YAML config.
- **Compounding**: materialized daily snapshot rows (one row per calendar day), rate embedded per row so rate changes are auditable via the ledger itself. ~3.6k rows over a decade is trivial.
- **Theoretical module scope**: exponential-growth plot + per-year table, **with recurring contributions** as a first-class input. Inflation and market dynamics are explicitly deferred.
- **Rate management**: single "current rate" per child in YAML; updating it affects only future ledger rows. Past rows keep whatever rate they were written with.
- **Package layout**: `src/investing_for_kids/` (src-layout); `app.py` at repo root as the Streamlit entry point.

## Repo Layout

```
investing_for_kids/
├── app.py                           # Streamlit entry point — thin wrapper
├── pyproject.toml                   # uv / ruff / package metadata
├── CLAUDE.md                        # already exists
├── README.md                        # NEW — run instructions, high-level overview
├── .gitignore                       # already exists
├── .claude/
│   └── settings.json                # NEW — permissions allowlist (see "Claude Code setup")
├── config/
│   └── accounts.yaml                # per-child metadata, rate, recurring contributions
├── data/
│   └── ledgers/
│       ├── child_a.csv                 # daily ledger — one row per day
│       └── child_b.csv
└── src/
    └── investing_for_kids/
        ├── __init__.py
        ├── theoretical/
        │   ├── __init__.py
        │   ├── growth.py            # pure calc: exponential growth + contributions
        │   └── views.py             # Streamlit UI for the theoretical tab
        ├── accounts/
        │   ├── __init__.py
        │   ├── config.py            # load/save accounts.yaml
        │   ├── ledger.py            # read/write CSV, materialize new days
        │   ├── transactions.py      # record deposit/withdrawal
        │   └── views.py             # Streamlit UI for each child's account tab
        └── ui/
            ├── __init__.py
            └── layout.py            # top-level tabs, shared header/formatting helpers
```

Separation principle: **pure-Python compute modules (`growth.py`, `ledger.py`, `transactions.py`, `config.py`) never import Streamlit.** UI lives only in `views.py` / `layout.py` / `app.py`. This keeps core logic trivially testable and re-usable.

## Storage Design

### `config/accounts.yaml` (hand-edited source of truth for rates & contributions)

```yaml
accounts:
  child_a:
    display_name: Child A
    seed_balance: 100.00
    seed_date: 2026-04-22
    annual_rate: 0.08                  # 8% APR; editable any time
    recurring_contributions:
      - amount: 10.00
        cadence: weekly                # weekly | monthly
        anchor: monday                 # day-of-week for weekly, day-of-month (int) for monthly
        start_date: 2026-04-22
        end_date: null                 # optional; null = open-ended
  child_b:
    display_name: Child B
    seed_balance: 100.00
    seed_date: 2026-04-22
    annual_rate: 0.08
    recurring_contributions: []
```

### `data/ledgers/<child>.csv` (daily ledger, one row per calendar day)

Columns:

| column            | meaning                                                      |
|-------------------|--------------------------------------------------------------|
| `date`            | ISO date (YYYY-MM-DD)                                        |
| `opening_balance` | Balance at start of day (= previous day's `closing_balance`) |
| `rate_applied`    | Annual rate used to compute this day's interest              |
| `deposits`        | Sum of ad-hoc deposits recorded for this day                 |
| `contributions`   | Sum of recurring contributions scheduled for this day        |
| `withdrawals`     | Sum of ad-hoc withdrawals recorded for this day              |
| `interest`        | Interest credited this day (formula below)                   |
| `closing_balance` | End-of-day balance                                           |

Append-only in normal operation. Ad-hoc transactions mutate today's row (rewriting the last row only). Because each row is independent of future rows, git diffs are clean and bounded.

## Core Algorithm: Daily Compounding

**Effective daily rate** derived from the annual rate stored on that day's row:

```
daily_rate = (1 + rate_applied) ** (1 / 365) - 1
```

**Transaction-then-interest model** (so "deposited today" earns interest today — better intuition for kids):

```
net_activity    = deposits + contributions - withdrawals
post_txn        = opening_balance + net_activity
interest        = post_txn * daily_rate
closing_balance = post_txn + interest
```

**Materialization** (`ledger.materialize_through(today)`):

1. Load CSV; find `last_row.date`.
2. For each `d` in `(last_row.date, today]`:
   - `opening = last_row.closing_balance`
   - `rate_applied = current annual_rate from accounts.yaml`
   - `contributions = sum of recurring schedules that fire on d`
   - `deposits = withdrawals = 0` (ad-hoc entries happen via `transactions.py`, which rewrites today's row)
   - Compute `interest` and `closing_balance`; append.
3. Persist CSV.

Idempotent: running twice on the same day is a no-op. Called on every Streamlit page load for each account, and before recording any transaction.

**Seeding**: the first ledger row is written on first run. `opening_balance = 0`, `deposits = seed_balance`, no interest, closing = seed.

## Module Responsibilities

### `theoretical/growth.py`

Pure functions, no Streamlit, no I/O.

- `project_growth(starting_balance, annual_rate, years, recurring_amount=0, cadence='monthly') -> pd.DataFrame`
  - Returns a yearly (or daily, configurable) DataFrame with columns `year, contributions_to_date, interest_to_date, balance`.
- `compounding_series(starting_balance, annual_rate, days, daily_contribution=0.0) -> pd.Series`
  - Daily series for the plot.

Contributions are converted to a per-day equivalent internally (weekly → /7, monthly → /30) for the smooth projection curve.

### `theoretical/views.py`

Streamlit UI for the Theory tab:

- Number inputs: starting balance, annual rate %, duration (years), recurring contribution amount + cadence.
- A Plotly/Altair line chart of balance over time + a contribution-vs-interest stacked area.
- A yearly table (via `st.dataframe`) showing balance, cumulative contributions, cumulative interest.

### `accounts/config.py`

- `load_accounts(path='config/accounts.yaml') -> dict[str, AccountConfig]`
- `save_accounts(config, path) -> None`
- `AccountConfig` is a simple dataclass (no heavy validation — private project).

### `accounts/ledger.py`

- `load_ledger(child) -> pd.DataFrame`
- `save_ledger(child, df) -> None`
- `materialize_through(child, target_date, config) -> pd.DataFrame` (core compounding logic above)
- `expand_recurring(schedules, from_date, to_date) -> dict[date, amount]` (helper)

### `accounts/transactions.py`

- `record_deposit(child, amount, config) -> None` — materializes through today, then adds `amount` to today's `deposits` and recomputes today's row.
- `record_withdrawal(child, amount, config) -> None` — same, but to `withdrawals`. Guardrail: reject if it would drive closing below zero (friendly `ValueError`; UI catches and shows a warning).

### `accounts/views.py`

Per-child Streamlit tab:

- Header: child's name, current balance (large), current annual rate, next scheduled contribution.
- Quick-action buttons/forms: "Deposit", "Withdraw" (amount input → calls `transactions.py`).
- Balance-history chart: line chart of `closing_balance` over time, overlaid markers for deposits/withdrawals.
- Recent-activity table: last ~30 ledger rows with non-zero activity.

Both children's tabs are rendered in the same app — the vision explicitly calls for no firewalling.

### `ui/layout.py`

- `render()` — builds the top-level Streamlit layout: tab bar with `Theory`, `Child A`, `Child B`, and materializes both ledgers up to today on app boot.

### `app.py`

```python
from investing_for_kids.ui.layout import render

render()
```

## Dependencies (`pyproject.toml`)

Runtime:
- `streamlit`
- `pandas`
- `plotly` (or `altair` — plotly has the nicer default Streamlit integration)
- `pyyaml`

Dev:
- `ruff`

Installed via `uv pip install -e .[dev]`. Project is registered as a proper package so `from investing_for_kids...` imports work both in Streamlit and ad-hoc notebooks.

## Claude Code Setup Suggestions (user asked)

- **`.claude/settings.json` permissions allowlist** for the common bash commands you'll run frequently, to reduce permission prompts: `ruff format .`, `ruff check .`, `streamlit run app.py`, `uv pip install …`, `uv venv`, `python -m …`. The `fewer-permission-prompts` skill can scan transcripts and generate this allowlist once you have a few sessions of history.
- **Skills worth knowing**:
  - `/review` — PR-style review of pending changes.
  - `/security-review` — mostly low-value here (no user input, local-only), but fine to run before first push.
  - `/simplify` — run after any feature lands; good fit for this codebase's "keep it small" ethos.
  - `/init` — already effectively done (CLAUDE.md exists); skip.
- **MCPs**: Playwright is overkill for a single-user local app. Skip unless you later want automated UI smoke tests. No other MCP is needed for this scope.
- **Hooks (optional, via `update-config` skill)**: an auto-format hook that runs `ruff format` on write is a nice ergonomic win. Worth adding once a few files exist.

## Critical Files to Create (execution order, high-level)

Phase 1 — scaffolding:
1. `pyproject.toml`, `.claude/settings.json`, `README.md`
2. `src/investing_for_kids/__init__.py` (+ submodule `__init__.py`s)
3. `config/accounts.yaml` (with both children seeded)
4. `app.py` stub + `ui/layout.py` tab skeleton

Phase 2 — theoretical module:
5. `theoretical/growth.py` (pure calcs, incl. recurring contributions)
6. `theoretical/views.py` (Streamlit tab)

Phase 3 — accounts module:
7. `accounts/config.py`
8. `accounts/ledger.py` (materialization + recurring expansion)
9. `accounts/transactions.py`
10. `accounts/views.py` (per-child UI)

Phase 4 — wiring & polish:
11. Wire all tabs in `ui/layout.py`.
12. First end-to-end run; seed ledgers via initial materialize.
13. Commit data files (ledgers + accounts.yaml) per the "git-as-backup" decision.

## Verification Plan

After implementation:

1. **Environment**: `source .venv/bin/activate && uv pip install -e .[dev]` succeeds.
2. **Lint/format**: `ruff format .` and `ruff check .` are clean.
3. **App boot**: `streamlit run app.py` starts; all three tabs render without error.
4. **Theoretical tab**: entering starting=$1000, rate=8%, duration=10yr, monthly contribution=$50 produces a monotonically increasing curve; yearly table's final-year balance matches hand calc (spot-check with `(1+0.08)^10 * 1000 + FV of annuity`).
5. **Ledger materialization**: manually set `seed_date` several days in the past, delete the ledger CSV, reload the app → CSV is created with one row per intervening day, closing balances compounding correctly.
6. **Transaction flow**: deposit $20 in Child A's account → today's row shows `deposits=20`, closing balance updated, balance-history chart reflects it.
7. **Rate change**: edit `annual_rate` in `accounts.yaml`, reload app on a future date → new ledger rows use the new rate, old rows untouched.
8. **Withdrawal guardrail**: try to withdraw more than the balance → friendly warning, no ledger mutation.
9. **Recurring contribution**: set a weekly $10 schedule; backfill several weeks by reloading after changing the system date (or a hard-coded `today` override used just for this test) → contribution rows land on the expected weekdays.
10. **Git hygiene**: `git status` after a session shows modified ledger CSVs diffing cleanly (one new row per day passed, plus today's updated transactions).
