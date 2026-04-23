"""Streamlit UI for the Theory tab.

Inputs: starting balance, annual rate, duration in years, and an optional
recurring contribution. Outputs: a balance-over-time chart, a stacked area
of principal-plus-contributions vs. interest, and a year-by-year table.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from . import growth


def _format_currency(value: float) -> str:
    """Format a dollar amount with two decimals and thousands separators."""
    return f"${value:,.2f}"


def _balance_chart(daily: pd.DataFrame) -> go.Figure:
    """Line chart of projected balance over time (x = years)."""
    years = daily["day"] / growth.DAYS_PER_YEAR
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=years,
            y=daily["balance"],
            mode="lines",
            name="Balance",
            line={"width": 3},
        )
    )
    fig.update_layout(
        title="Projected balance over time",
        xaxis_title="Years from today",
        yaxis_title="Balance ($)",
        height=400,
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
    )
    return fig


def _principal_vs_interest_chart(daily: pd.DataFrame, starting_balance: float) -> go.Figure:
    """Stacked area showing how much of the balance came from interest."""
    years = daily["day"] / growth.DAYS_PER_YEAR
    principal = starting_balance + daily["contributions_to_date"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=years,
            y=principal,
            mode="lines",
            name="Money you put in",
            stackgroup="one",
            line={"width": 0},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=daily["interest_to_date"],
            mode="lines",
            name="Interest earned",
            stackgroup="one",
            line={"width": 0},
        )
    )
    fig.update_layout(
        title="Where the money came from",
        xaxis_title="Years from today",
        yaxis_title="Balance ($)",
        height=400,
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
    )
    return fig


def _period_table(daily: pd.DataFrame, starting_balance: float, period: str) -> pd.DataFrame:
    """Sample the daily series at yearly or monthly boundaries for display.

    Month boundaries are spaced evenly across the 365-day year
    (day ≈ round(i * 365/12)), so month 12 lands exactly on year 1.
    """
    total_days = int(daily.iloc[-1]["day"])
    if period == "monthly":
        total_months = total_days * 12 // growth.DAYS_PER_YEAR
        day_indices = [round(i * growth.DAYS_PER_YEAR / 12) for i in range(total_months + 1)]
        label_col = "Month"
        labels = list(range(total_months + 1))
    else:
        total_years = total_days // growth.DAYS_PER_YEAR
        day_indices = [i * growth.DAYS_PER_YEAR for i in range(total_years + 1)]
        label_col = "Year"
        labels = list(range(total_years + 1))

    sampled = daily.iloc[day_indices].reset_index(drop=True)
    return pd.DataFrame(
        {
            label_col: labels,
            "Balance": sampled["balance"].map(_format_currency).values,
            "Money put in": (starting_balance + sampled["contributions_to_date"])
            .map(_format_currency)
            .values,
            "Interest earned": sampled["interest_to_date"].map(_format_currency).values,
        }
    )


def render() -> None:
    """Render the Theory tab: inputs, charts, yearly table."""
    st.header("How money grows over time")
    st.caption(
        "Try changing the numbers below to see how small amounts can grow "
        "into much bigger amounts — just by waiting."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        starting_balance = st.number_input(
            "Starting balance ($)",
            min_value=0.0,
            value=100.0,
            step=10.0,
            format="%.2f",
        )
    with col2:
        annual_rate_pct = st.number_input(
            "Yearly growth rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=8.0,
            step=0.5,
            format="%.2f",
        )
    with col3:
        years = st.number_input(
            "Years",
            min_value=1,
            max_value=75,
            value=10,
            step=1,
        )

    col4, col5 = st.columns(2)
    with col4:
        recurring_amount = st.number_input(
            "Recurring contribution ($)",
            min_value=0.0,
            value=10.0,
            step=5.0,
            format="%.2f",
        )
    with col5:
        cadence = st.selectbox("How often?", options=["monthly", "weekly"], index=0)

    annual_rate = annual_rate_pct / 100.0
    daily_contrib = growth._cadence_to_daily(recurring_amount, cadence)
    daily = growth.compounding_series(
        starting_balance=starting_balance,
        annual_rate=annual_rate,
        days=int(years) * growth.DAYS_PER_YEAR,
        daily_contribution=daily_contrib,
    )

    final = daily.iloc[-1]
    total_put_in = starting_balance + final["contributions_to_date"]
    metric_cols = st.columns(3)
    metric_cols[0].metric("Final balance", _format_currency(final["balance"]))
    metric_cols[1].metric("Money you put in", _format_currency(total_put_in))
    metric_cols[2].metric("Interest earned", _format_currency(final["interest_to_date"]))

    st.plotly_chart(_balance_chart(daily), width="stretch")
    st.plotly_chart(
        _principal_vs_interest_chart(daily, starting_balance),
        width="stretch",
    )

    period = st.radio(
        "Show growth",
        options=["Yearly", "Monthly"],
        horizontal=True,
        key="theory_table_period",
    )
    period_key = period.lower()
    st.subheader("Year by year" if period_key == "yearly" else "Month by month")
    st.dataframe(
        _period_table(daily, starting_balance, period_key),
        hide_index=True,
        width="stretch",
    )
