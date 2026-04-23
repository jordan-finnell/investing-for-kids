# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A local-only Streamlit app to help children (Child A and Child B) understand investing — both theoretically (exponential growth visualizations) and practically (managing simulated investment accounts with real-time compounding).

## Environment Setup

```bash
source ~/project/investing_for_kids/.venv/bin/activate
```

UV is used for venv management. Always activate the venv before running any Python commands.

## Common Commands

```bash
# Run the app
streamlit run app.py

# Format code
ruff format .

# Lint
ruff check .

# Install a new dependency
uv pip install <package>
```

## Architecture

The project should be structured as an importable Python package. Key areas:

- **Theoretical module**: Exponential growth calculations and Streamlit visualizations. Accepts user inputs (starting balance, return rate, duration) and renders plots/tables.
- **Accounts module**: Backend for child investment accounts. Handles daily compounding, deposits/withdrawals, balance history, and growth rate configuration. Persists to a simple file-based store (CSV or SQLite — avoid full RDBMS).
- **Streamlit frontend**: Single local app surfacing both modules. Accounts for both children are visible in the same UI (no auth separation needed).

## Technical Conventions

- Python only.
- Ruff for formatting and linting.
- Docstrings on functions: clear and concise. Minimize inline `#` comments inside function bodies.
- No heavy type validation — this is a single-owner private project.
- Account data should be versioned via git (committed alongside code) for backup. Keep data files small and human-readable.
- No external services, no auth, no multi-user concerns.
