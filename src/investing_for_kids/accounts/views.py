"""Streamlit UI for one child's account tab — header, transactions, history."""

from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .config import AccountConfig
from .ledger import materialize_through
from .transactions import record_deposit, record_withdrawal


def _format_currency(value: float) -> str:
    """Format a dollar amount with two decimals and thousands separators."""
    return f"${value:,.2f}"


def _balance_chart(df: pd.DataFrame, display_name: str) -> go.Figure:
    """Line chart of closing balance over time, with activity markers overlaid."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["closing_balance"],
            mode="lines",
            name="Balance",
            line={"width": 3},
        )
    )
    activity = df[(df["deposits"] > 0) | (df["withdrawals"] > 0)]
    if not activity.empty:
        fig.add_trace(
            go.Scatter(
                x=activity["date"],
                y=activity["closing_balance"],
                mode="markers",
                name="Deposits/Withdrawals",
                marker={"size": 10, "color": "orange"},
            )
        )
    fig.update_layout(
        title=f"{display_name}'s balance over time",
        xaxis_title="Date",
        yaxis_title="Balance ($)",
        height=350,
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
    )
    return fig


def _recent_activity(df: pd.DataFrame, limit: int = 30) -> pd.DataFrame:
    """Most recent `limit` days with non-zero deposit, contribution, or withdrawal."""
    activity = df[(df["deposits"] > 0) | (df["contributions"] > 0) | (df["withdrawals"] > 0)].tail(
        limit
    )
    return pd.DataFrame(
        {
            "Date": activity["date"].astype(str).values,
            "Deposit": activity["deposits"].map(_format_currency).values,
            "Contribution": activity["contributions"].map(_format_currency).values,
            "Withdrawal": activity["withdrawals"].map(_format_currency).values,
            "Interest": activity["interest"].map(_format_currency).values,
            "Balance": activity["closing_balance"].map(_format_currency).values,
        }
    )


def _transaction_forms(account: AccountConfig, today: date) -> None:
    """Side-by-side deposit/withdrawal forms. Reruns the page on success."""
    cols = st.columns(2)
    with cols[0], st.form(key=f"{account.key}_deposit_form", clear_on_submit=True):
        amount = st.number_input(
            "Deposit ($)",
            min_value=0.0,
            step=5.0,
            format="%.2f",
            key=f"{account.key}_deposit_amt",
        )
        if st.form_submit_button("Deposit", width="stretch") and amount > 0:
            try:
                record_deposit(account, amount, today=today)
                st.success(f"Deposited {_format_currency(amount)}")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    with cols[1], st.form(key=f"{account.key}_withdraw_form", clear_on_submit=True):
        amount = st.number_input(
            "Withdraw ($)",
            min_value=0.0,
            step=5.0,
            format="%.2f",
            key=f"{account.key}_withdraw_amt",
        )
        if st.form_submit_button("Withdraw", width="stretch") and amount > 0:
            try:
                record_withdrawal(account, amount, today=today)
                st.success(f"Withdrew {_format_currency(amount)}")
                st.rerun()
            except ValueError as e:
                st.error(str(e))


def render(account: AccountConfig) -> None:
    """Render this child's account tab: header, transaction forms, chart, table."""
    today = date.today()
    df = materialize_through(account, today)

    current_balance = float(df["closing_balance"].iloc[-1])
    total_put_in = float(df["deposits"].sum() + df["contributions"].sum() - df["withdrawals"].sum())
    total_interest = float(df["interest"].sum())

    st.header(f"{account.display_name}'s account")

    cols = st.columns(4)
    cols[0].metric("Current balance", _format_currency(current_balance))
    cols[1].metric("Yearly growth rate", f"{account.annual_rate * 100:.2f}%")
    cols[2].metric("Money put in", _format_currency(total_put_in))
    cols[3].metric("Interest earned", _format_currency(total_interest))

    st.subheader("Add or take out money")
    _transaction_forms(account, today)

    st.plotly_chart(_balance_chart(df, account.display_name), width="stretch")

    st.subheader("Recent activity")
    activity = _recent_activity(df)
    if activity.empty:
        st.info("No transactions yet — try depositing some money above!")
    else:
        st.dataframe(activity, hide_index=True, width="stretch")
