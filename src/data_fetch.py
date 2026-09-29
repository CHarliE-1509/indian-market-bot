"""Fetch and cache NSE daily OHLCV data via Yahoo Finance (.NS tickers)."""
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Liquid, large/mid-cap NIFTY constituents spanning sectors — avoids illiquid names
# where slippage assumptions in the backtest would be unrealistic.
UNIVERSE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TITAN.NS", "ULTRACEMCO.NS", "NESTLEIND.NS", "TATAMOTORS.NS", "WIPRO.NS",
]
INDEX = "^NSEI"  # NIFTY 50 index, used for market regime filter


def fetch(ticker: str, period: str = "8y", interval: str = "1d", force: bool = False) -> pd.DataFrame:
    cache = DATA_DIR / f"{ticker.replace('^','IDX_')}.csv"
    if cache.exists() and not force:
        df = pd.read_csv(cache, index_col=0, parse_dates=True)
        return df
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna()
    df.to_csv(cache)
    return df


def refresh_latest(tickers, lookback="5d"):
    """Pull the last few days fresh and merge into the cached CSV (dedup by date).
    Cheap enough to run daily without a full 8y re-download of every ticker."""
    for t in tickers:
        cache = DATA_DIR / f"{t.replace('^','IDX_')}.csv"
        fresh = yf.download(t, period=lookback, interval="1d", progress=False, auto_adjust=True)
        if isinstance(fresh.columns, pd.MultiIndex):
            fresh.columns = fresh.columns.get_level_values(0)
        fresh = fresh.dropna()
        if fresh.empty:
            continue
        if cache.exists():
            old = pd.read_csv(cache, index_col=0, parse_dates=True)
            combined = pd.concat([old, fresh])
            combined = combined[~combined.index.duplicated(keep="last")].sort_index()
        else:
            combined = fresh
        combined.to_csv(cache)
        time.sleep(0.2)


def fetch_universe(tickers=None, period="8y", force=False):
    tickers = tickers or (UNIVERSE + [INDEX])
    out = {}
    for i, t in enumerate(tickers):
        try:
            df = fetch(t, period=period, force=force)
            if len(df) > 100:
                out[t] = df
                print(f"  [{i+1}/{len(tickers)}] {t}: {len(df)} rows ({df.index[0].date()} -> {df.index[-1].date()})")
            else:
                print(f"  [{i+1}/{len(tickers)}] {t}: SKIPPED (only {len(df)} rows)")
        except Exception as e:
            print(f"  [{i+1}/{len(tickers)}] {t}: FAILED ({e})")
        time.sleep(0.3)  # be polite to yfinance / avoid rate limiting
    return out


if __name__ == "__main__":
    print("Fetching universe + index...")
    data = fetch_universe()
    print(f"\nDone. {len(data)} instruments cached in {DATA_DIR}")
