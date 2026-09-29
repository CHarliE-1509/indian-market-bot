"""
Analyst consensus divergence screen — the closest honest replication of
Kalshi's "compare a model probability against an independent aggregated
view" methodology available with free NSE data (no options chain data exists
for NSE via any free source, which is what would give a true market-implied
probability the way a Kalshi contract price does).

IMPORTANT LIMITATION: this is observational only, NOT backtested and NEVER a
source of live capital allocation. Yahoo Finance only exposes CURRENT analyst
target prices, not a historical time series — there is no way to test
whether "buying large analyst-target divergences" would have worked
historically. Treat this as a live snapshot worth knowing about, not a
validated signal.
"""
import sys
import time
import warnings
from pathlib import Path

import yfinance as yf

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def fetch_one(ticker: str):
    try:
        info = yf.Ticker(ticker).info
    except Exception:
        return None
    target = info.get("targetMeanPrice")
    current = info.get("currentPrice") or info.get("regularMarketPrice")
    n_analysts = info.get("numberOfAnalystOpinions")
    if not target or not current or not n_analysts:
        return None
    return {
        "current_price": current,
        "target_mean_price": target,
        "target_high": info.get("targetHighPrice"),
        "target_low": info.get("targetLowPrice"),
        "implied_return_pct": round((target / current - 1) * 100, 2),
        "n_analysts": n_analysts,
        "recommendation": info.get("recommendationKey"),
    }


def run(tickers, sleep_between=0.3):
    out = {}
    for t in tickers:
        result = fetch_one(t)
        if result:
            out[t] = result
        time.sleep(sleep_between)
    return out


if __name__ == "__main__":
    from wide_universe import WIDE_UNIVERSE
    print(f"Fetching analyst consensus for {len(WIDE_UNIVERSE)} stocks (this hits Yahoo's info endpoint per ticker, slower than price data)...")
    results = run(WIDE_UNIVERSE)
    ranked = sorted(results.items(), key=lambda x: -x[1]["implied_return_pct"])
    print(f"\n{len(results)}/{len(WIDE_UNIVERSE)} had analyst coverage data")
    print("\nLargest analyst-implied upside:")
    for t, r in ranked[:5]:
        print(f"  {t}: {r['implied_return_pct']:+.1f}% implied ({r['n_analysts']} analysts, {r['recommendation']})")
    print("\nLargest analyst-implied downside:")
    for t, r in ranked[-5:]:
        print(f"  {t}: {r['implied_return_pct']:+.1f}% implied ({r['n_analysts']} analysts, {r['recommendation']})")
