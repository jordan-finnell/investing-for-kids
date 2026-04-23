# investing_for_kids

A local-only Streamlit app to help Child A and Child B understand investing — both theoretically (exponential-growth visualizations) and practically (managing simulated investment accounts with daily compounding).

See `starting_vision.md` for the original vision and `plan.md` for the design and implementation plan.

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

## Layout

- `app.py` — Streamlit entry point
- `src/investing_for_kids/` — package source
  - `theoretical/` — exponential-growth plots + projections
  - `accounts/` — per-child daily ledgers, transactions, compounding
  - `ui/` — top-level layout and shared UI helpers
- `config/accounts.yaml` — per-child rate, seed, recurring contributions
- `data/ledgers/<child>.csv` — per-child daily ledger (one row per day)
