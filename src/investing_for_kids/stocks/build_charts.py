"""Build interactive Plotly HTML fragments for the slide deck.

Reads the CSVs written by `fetch_prices.main()` and emits standalone HTML
chart fragments (plotly.js loaded from CDN) into `deck/charts/`.

Also prints per-ticker summary stats (start price, end price, growth
multiplier on $100) so the deck author can paste the current numbers
into `deck/index.html`.

    python -m investing_for_kids.stocks.build_charts
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
DECK_DATA_DIR = _PROJECT_ROOT / "deck" / "data"
DECK_CHARTS_DIR = _PROJECT_ROOT / "deck" / "charts"

PALETTE = {
    "line": "#ff7f2a",
    "fill": "#fde4cf",
    "bg": "#fffaf2",
    "grid": "#e8d9be",
    "text": "#2a4e4d",
}


def _load(key: str) -> pd.DataFrame:
    path = DECK_DATA_DIR / f"{key}.csv"
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df


def _style_layout(fig: go.Figure, title: str, log_y: bool = False) -> None:
    fig.update_layout(
        title={"text": title, "font": {"size": 26, "color": PALETTE["text"]}},
        xaxis={"title": "", "gridcolor": PALETTE["grid"]},
        yaxis={
            "title": "",
            "gridcolor": PALETTE["grid"],
            "tickprefix": "$",
            "type": "log" if log_y else "linear",
        },
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        font={"family": "Georgia, serif", "size": 16, "color": PALETTE["text"]},
        margin={"l": 60, "r": 40, "t": 70, "b": 50},
        showlegend=False,
    )


def _line_chart(df: pd.DataFrame, title: str, log_y: bool = False) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["close"],
            mode="lines",
            line={"color": PALETTE["line"], "width": 3},
            fill="tozeroy",
            fillcolor=PALETTE["fill"],
            hovertemplate="%{x|%b %Y}<br><b>$%{y:.2f}</b><extra></extra>",
        )
    )
    # Start + end annotations
    start, end = df.iloc[0], df.iloc[-1]
    fig.add_annotation(
        x=start["date"],
        y=start["close"],
        text=f"<b>{start['date']:%b %Y}: ${start['close']:.2f}</b>",
        showarrow=True,
        arrowhead=2,
        ax=60,
        ay=-40,
        font={"size": 15, "color": PALETTE["text"]},
    )
    fig.add_annotation(
        x=end["date"],
        y=end["close"],
        text=f"<b>{end['date']:%b %Y}: ${end['close']:.2f}</b>",
        showarrow=True,
        arrowhead=2,
        ax=-60,
        ay=-40,
        font={"size": 15, "color": PALETTE["text"]},
    )
    _style_layout(fig, title, log_y=log_y)
    return fig


def _write(fig: go.Figure, filename: str) -> Path:
    out = DECK_CHARTS_DIR / filename
    fig.write_html(out, include_plotlyjs="cdn", full_html=True)
    return out


def _summary(df: pd.DataFrame, label: str) -> None:
    start, end = df.iloc[0], df.iloc[-1]
    multiplier = end["close"] / start["close"]
    hundred = 100.0 * multiplier
    print(
        f"  {label:<8}  {start['date']:%Y-%m}: ${start['close']:>7.2f}  →  "
        f"{end['date']:%Y-%m}: ${end['close']:>8.2f}   "
        f"(×{multiplier:.1f};  $100 → ${hundred:,.0f})"
    )


def main() -> None:
    """Build all chart fragments and print a summary table."""
    DECK_CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    charts = [
        ("nflx", "How much did Netflix cost?", "nflx_price.html", False),
        ("nvda", "How much did Nvidia cost?", "nvda_price.html", False),
        ("sp500", "The S&P 500: all 500 biggest companies together", "sp500_growth.html", True),
    ]

    print("\nBuilt charts:")
    for key, title, filename, log_y in charts:
        df = _load(key)
        fig = _line_chart(df, title, log_y=log_y)
        out = _write(fig, filename)
        print(f"  → {out.relative_to(_PROJECT_ROOT)}")

    print("\nStart vs. end summary (paste these into deck/index.html):")
    for key, label in [("nflx", "Netflix"), ("nvda", "Nvidia"), ("sp500", "S&P 500")]:
        _summary(_load(key), label)
    print()


if __name__ == "__main__":
    main()
