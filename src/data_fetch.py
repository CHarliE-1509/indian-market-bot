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


REQUEST_TIMEOUT = 15  # seconds — without this, a single stalled/rate-limited ticker can
# hang a yf.download call indefinitely (observed: runs that should take ~70s took
# hours once Yahoo started rate-limiting, because nothing bounded a slow request).
MAX_CONSECUTIVE_FAILURES = 8  # circuit breaker: this many failed/timed-out tickers in a
# row is a strong signal of a rate-limit/outage, not bad luck on individual tickers —
# stop hammering and use cached data for whatever's left, rather than grinding for hours.


def fetch(ticker: str, period: str = "8y", interval: str = "1d", force: bool = False) -> pd.DataFrame:
    cache = DATA_DIR / f"{ticker.replace('^','IDX_')}.csv"
    if cache.exists() and not force:
        df = pd.read_csv(cache, index_col=0, parse_dates=True)
        return df
    df = yf.download(ticker, period=period, interval=interval, progress=False,
                      auto_adjust=True, timeout=REQUEST_TIMEOUT)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna()
    df.to_csv(cache)
    return df


def refresh_latest(tickers, lookback="5d"):
    """Pull the last few days fresh and merge into the cached CSV (dedup by date).
    Cheap enough to run daily without a full 8y re-download of every ticker.

    Bounded against a flaky/rate-limited data provider: each ticker gets a hard
    request timeout and one retry; a run of consecutive failures trips a circuit
    breaker that stops the refresh early (remaining tickers just keep using their
    last cached data this cycle) instead of hanging for hours."""
    consecutive_failures = 0
    skipped = []
    for t in tickers:
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            skipped.append(t)
            continue

        cache = DATA_DIR / f"{t.replace('^','IDX_')}.csv"
        fresh = None
        for attempt in range(2):
            try:
                fresh = yf.download(t, period=lookback, interval="1d", progress=False,
                                     auto_adjust=True, timeout=REQUEST_TIMEOUT)
                break
            except Exception as e:
                if attempt == 0:
                    time.sleep(1.5)  # short backoff before the one retry
                else:
                    print(f"  refresh_latest: {t} failed after retry: {e}")

        if fresh is None or fresh.empty:
            consecutive_failures += 1
            continue
        consecutive_failures = 0

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

    if skipped:
        print(f"  refresh_latest: circuit breaker tripped after {MAX_CONSECUTIVE_FAILURES} "
              f"consecutive failures — skipped {len(skipped)} tickers this run, using cached data for them.")


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
