"""
Monte Carlo Bot — estimates drift/volatility per stock (from historical daily
log returns) for a client-side GBM price-path simulation on the dashboard.

Only estimates parameters here; the actual simulation runs in the browser
(see docs/montecarlo.html) so the user can pick any stock and re-roll
instantly without a server round-trip. Geometric Brownian Motion is a
simplification — constant drift/volatility, log-normal returns, no fat tails
or jumps — presented as an illustrative uncertainty cone, not a forecast.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def estimate_params(close: pd.Series, lookback: int = 252):
    log_rets = np.log(close / close.shift(1)).dropna().tail(lookback)
    if len(log_rets) < 60:
        return None
    return {
        "mu": float(log_rets.mean()),
        "sigma": float(log_rets.std()),
        "last_price": float(close.iloc[-1]),
        "n_obs": len(log_rets),
    }


def run(data: dict) -> dict:
    out = {}
    for ticker, df in data.items():
        params = estimate_params(df["Close"])
        if params:
            out[ticker] = params
    return out


if __name__ == "__main__":
    from data_fetch import fetch_universe
    from wide_universe import WIDE_UNIVERSE
    data = fetch_universe(WIDE_UNIVERSE, force=False)
    params = run(data)
    sample = list(params.items())[0]
    print(f"Estimated params for {len(params)} stocks. Sample: {sample}")
    ann_vol = sample[1]["sigma"] * (252 ** 0.5) * 100
    ann_drift = sample[1]["mu"] * 252 * 100
    print(f"  -> annualized drift {ann_drift:.1f}%, annualized vol {ann_vol:.1f}%")
