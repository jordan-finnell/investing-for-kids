# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A local-only Streamlit app to help children (Child A and Child B) understand investing — both theoretically (exponential growth visualizations) and practically (managing simulated investment accounts with real-time compounding).

## Environment Setup

```bash
source ~/project/investing_for_kids/.venv/bin/activate
```

UV is used for venv management. Python 3.13. Always activate the venv before running any Python commands. Installed as an editable package (`uv pip install -e .[dev]`), so imports like `from investing_for_kids.accounts.ledger import materialize_through` work.

## Common Commands

```bash
# Run the app (opens at http://localhost:8501)
streamlit run app.py

# Format / lint (both must be clean before committing)
ruff format .
ruff check .

# Add a dependency
uv pip install <package>
```

For headless UI validation (no browser), use `streamlit.testing.v1.AppTest`:

```python
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("app.py", default_timeout=10); at.run()
assert not at.exception
```

## Architecture

src-layout package under `src/investing_for_kids/`:

- **`theoretical/`** — Theory tab.
  - `growth.py` — pure projection math (`compounding_series`, `project_growth`). No Streamlit.
  - `views.py` — Streamlit UI (inputs, charts, yearly/monthly toggle table).

- **`accounts/`** — per-child accounts, backend + UI.
  - `config.py` — YAML loader; `AccountConfig` + `RecurringContribution` dataclasses. Default paths are anchored to repo root via `__file__`, so imports work regardless of CWD.
  - `ledger.py` — CSV daily-snapshot ledger. `materialize_through(account, target_date)` brings the ledger up to any date idempotently (seeds on first run, appends one row per intervening day). `expand_recurring()` handles weekly (weekday anchor) and monthly (day-of-month anchor, clamped to month length) cadences.
  - `transactions.py` — `record_deposit` / `record_withdrawal`. Withdrawals are rejected if they would drive the balance below zero.
  - `views.py` — per-child Streamlit tab (metrics, dep/withdraw forms, history chart, recent activity).

- **`ui/layout.py`** — top-level tab bar. Tabs are built dynamically from `load_accounts()` (Theory + one tab per configured child).

**Separation principle**: pure-Python compute modules (`theoretical/growth.py`, `accounts/config.py`, `accounts/ledger.py`, `accounts/transactions.py`) never import Streamlit. UI lives only in `views.py` modules, `ui/layout.py`, and `app.py`. Preserve this boundary when adding features.

## Storage

- **`config/accounts.yaml`** — source of truth for each child's `display_name`, `seed_balance`, `seed_date`, `annual_rate`, and `recurring_contributions`. Hand-edited.
- **`config/accounts_template.yaml`** — fully-commented reference for supported keys. Update it when adding new config fields.
- **`data/ledgers/<child>.csv`** — one row per calendar day. Columns: `date, opening_balance, rate_applied, deposits, contributions, withdrawals, interest, closing_balance`. Written with `float_format="%.4f"`. Committed to git as the backup strategy.
- No SQLite or external databases — deliberately file-based, human-readable, git-diffable.

## Compounding model

Transaction-then-interest:

```
net             = deposits + contributions - withdrawals
post_txn        = opening_balance + net
interest        = post_txn * ((1 + rate_applied)^(1/365) - 1)
closing_balance = post_txn + interest
```

`rate_applied` is stored per-row, so changing `annual_rate` in `accounts.yaml` only affects rows generated after the change — history stays auditable. `seed_date`/`seed_balance` in YAML are only consulted when the child's ledger CSV doesn't yet exist.

## Technical Conventions

- Python 3.13 only. Use `from __future__ import annotations` and modern type syntax (`list[X]`, `X | None`).
- Ruff for formatting and linting; both must pass before commit.
- Docstrings on functions: clear and concise. Minimize inline `#` comments inside function bodies.
- No heavy type validation — this is a single-owner private project.
- Account data is committed to git for backup. Keep data files small and human-readable.
- No external services, no auth, no multi-user concerns.
- Streamlit widgets: use the modern `width="stretch"` API, not the deprecated `use_container_width=True`.

## Workflow

- Each phase of work lands as its own PR off `main`, squash-merged.
- Don't stack branches on unmerged PRs — merge sequentially.
- The IDE environment has no Windows-style git credential helper; `gh auth setup-git` configures gh as the helper for pushes.
