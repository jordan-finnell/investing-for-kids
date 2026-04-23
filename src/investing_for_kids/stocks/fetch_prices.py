"""One-shot yfinance fetch → commit snapshot CSVs into `deck/data/`.

Run manually when you want to refresh the data behind the slide deck:

    uv pip install -e .[deck]
    python -m investing_for_kids.stocks.fetch_prices
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
DECK_DATA_DIR = _PROJECT_ROOT / "deck" / "data"

TICKERS = {
    "nflx": {"symbol": "NFLX", "start": "2010-01-01"},
    "nvda": {"symbol": "NVDA", "start": "2010-01-01"},
    "sp500": {"symbol": "^GSPC", "start": "1990-01-01"},
}


def fetch(symbol: str, start: str = "2010-01-01") -> pd.DataFrame:
    """Pull monthly closing prices for a ticker. Returns a DataFrame with date + close."""
    hist = yf.Ticker(symbol).history(start=start, interval="1mo", auto_adjust=True)
    if hist.empty:
        raise RuntimeError(f"yfinance returned no data for {symbol!r}")
    df = pd.DataFrame(
        {
            "date": hist.index.strftime("%Y-%m-%d"),
            "close": hist["Close"].round(2).values,
        }
    )
    return df


def main() -> None:
    """Fetch all configured tickers and write to `deck/data/<key>.csv`."""
    DECK_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for key, cfg in TICKERS.items():
        df = fetch(cfg["symbol"], start=cfg["start"])
        out = DECK_DATA_DIR / f"{key}.csv"
        df.to_csv(out, index=False)
        print(f"  {cfg['symbol']:>6}  {len(df):>4} rows  →  {out.relative_to(_PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
