"""
The three other information diffusion variants tested (formalized as reusable
functions so run_research.py can reproduce them and save results for the
Team B page). All three: real, tested, and negative — see each function's
docstring for what was found and why.
"""
import sys
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_fetch import fetch_universe, INDEX


def test_us_overnight_diffusion():
    """US S&P500 close-to-close return vs NIFTY's next-day move, decomposed
    into the overnight gap (open vs prior close — NOT tradeable, since GIFT
    Nifty/SGX Nifty futures price this in before NSE opens) vs the intraday
    continuation (open to close — the only part a retail trade could actually
    capture). Finding: strong gap correlation (0.45), ~zero intraday (-0.05)."""
    us_data = fetch_universe(["^GSPC"], period="8y", force=False)
    sp500_ret = us_data["^GSPC"]["Close"].pct_change()
    nifty = fetch_universe([INDEX], force=False)[INDEX]

    gap_ret = (nifty["Open"] / nifty["Close"].shift(1) - 1).shift(-1)
    intraday_ret = (nifty["Close"] / nifty["Open"] - 1).shift(-1)

    df = pd.DataFrame({"sp500": sp500_ret, "gap": gap_ret, "intraday": intraday_ret}).dropna()
    return {
        "mechanism": "US S&P500 overnight move -> NIFTY next-day open/close",
        "n_obs": len(df),
        "gap_correlation": round(float(df["sp500"].corr(df["gap"])), 4),
        "intraday_correlation": round(float(df["sp500"].corr(df["intraday"])), 4),
        "verdict": "FAILED — information fully absorbed into NSE's opening price before market open (GIFT Nifty arbitrage); nothing left to trade once the market opens.",
    }


def test_commodity_diffusion():
    """Crude oil (WTI) daily return vs candidate commodity-exposed stocks
    (OMCs, aviation, paints, metals) at lags 0/1/2/3/5 days. Finding: weak,
    sign-inconsistent correlations that don't decay smoothly with lag — the
    signature of noise / contemporaneous common-factor co-movement, not
    genuine diffusion."""
    crude_data = fetch_universe(["CL=F"], period="8y", force=False)
    crude_ret = crude_data["CL=F"]["Close"].pct_change()

    candidates = {
        "BPCL.NS": "OMC — refining/marketing margin exposure",
        "IOC.NS": "OMC — refining/marketing margin exposure",
        "INDIGO.NS": "Aviation — fuel cost exposure",
        "ASIANPAINT.NS": "Paints — petrochemical input cost",
        "JSWSTEEL.NS": "Metals — commodity complex correlation",
        "TATASTEEL.NS": "Metals — commodity complex correlation",
    }
    data = fetch_universe(list(candidates.keys()), period="8y", force=False)

    results = {}
    for t, note in candidates.items():
        if t not in data:
            continue
        stock_ret = data[t]["Close"].pct_change()
        df = pd.DataFrame({"crude": crude_ret, "stock": stock_ret}).dropna()
        by_lag = {}
        for lag in [0, 1, 2, 3, 5]:
            shifted = pd.DataFrame({"crude": df["crude"], "stock_future": df["stock"].shift(-lag)}).dropna()
            by_lag[lag] = round(float(shifted["crude"].corr(shifted["stock_future"])), 4)
        results[t] = {"note": note, "correlation_by_lag": by_lag}

    return {
        "mechanism": "Crude oil (WTI) -> commodity-exposed NSE stocks",
        "results_by_ticker": results,
        "verdict": "FAILED — correlations weak (0.02-0.11) and don't decay smoothly with lag; looks like contemporaneous common-factor noise, not diffusion.",
    }


def test_adr_diffusion():
    """US-listed ADR overnight move vs the same company's NSE stock next-day
    gap/intraday move, for 5 dual-listed companies. Finding: same pattern as
    the index-level test — strong gap correlation (0.28-0.59), ~zero
    intraday correlation. Consistent, not a fluke of the aggregate index."""
    pairs = {"INFY": "INFY.NS", "IBN": "ICICIBANK.NS", "HDB": "HDFCBANK.NS",
             "WIT": "WIPRO.NS", "RDY": "DRREDDY.NS"}
    adr_data = fetch_universe(list(pairs.keys()), period="8y", force=False)
    nse_data = fetch_universe(list(pairs.values()), period="8y", force=False)

    results = {}
    for adr, nse in pairs.items():
        if adr not in adr_data or nse not in nse_data:
            continue
        adr_ret = adr_data[adr]["Close"].pct_change()
        nse_df = nse_data[nse]
        gap_ret = (nse_df["Open"] / nse_df["Close"].shift(1) - 1).shift(-1)
        intraday_ret = (nse_df["Close"] / nse_df["Open"] - 1).shift(-1)
        df = pd.DataFrame({"adr": adr_ret, "gap": gap_ret, "intraday": intraday_ret}).dropna()
        results[f"{adr}->{nse}"] = {
            "n_obs": len(df),
            "gap_correlation": round(float(df["adr"].corr(df["gap"])), 4),
            "intraday_correlation": round(float(df["adr"].corr(df["intraday"])), 4),
        }

    return {
        "mechanism": "US-listed ADR overnight move -> same company's NSE stock next day",
        "results_by_pair": results,
        "verdict": "FAILED — confirms the index-level finding at individual-stock granularity: overnight information is fully absorbed into NSE's opening price, nothing tradeable left intraday.",
    }
