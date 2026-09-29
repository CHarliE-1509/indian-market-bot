"""
Quant Bot — statistics, probability, risk, and Kelly position sizing.

Two distinct jobs, kept separate on purpose:
  1. Per-stock quant read: momentum, mispricing z-score, beta, volatility,
     and a probability-of-positive-move estimate (normal-approximation on
     drift/vol — a standard, defensible quant shortcut, not a claim of a
     true predictive model).
  2. Strategy-level Kelly fraction: how much of total capital the strategy's
     own backtested edge justifies deploying at all, derived from the
     momentum portfolio's realized monthly return distribution. This is
     applied once, at the "how much to invest overall" level, not per-stock
     — per-stock trade samples are too sparse in a 5-name portfolio for a
     reliable individual Kelly estimate.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from indicators import sma  # noqa

MISPRICING_THRESHOLD_PCT = 8.0


def mispricing_zscore(close: pd.Series, window: int = 50):
    mean = close.rolling(window).mean()
    std = close.rolling(window).std()
    pct_dev = (close - mean) / mean * 100
    z = (close - mean) / std.replace(0, np.nan)
    return pct_dev.iloc[-1], z.iloc[-1]


def beta_vs_index(stock_close: pd.Series, index_close: pd.Series, window: int = 252):
    stock_ret = stock_close.pct_change().dropna()
    idx_ret = index_close.pct_change().dropna()
    joined = pd.concat([stock_ret, idx_ret], axis=1, join="inner").tail(window)
    joined.columns = ["stock", "index"]
    if len(joined) < 60 or joined["index"].var() == 0:
        return None
    cov = joined.cov().iloc[0, 1]
    var = joined["index"].var()
    return cov / var


def probability_up(close: pd.Series, horizon_days: int = 21, lookback: int = 252):
    """Normal-approximation probability that price is higher in `horizon_days`,
    using recent drift and volatility. A shortcut (real returns aren't normal,
    have fat tails), not a claim of a calibrated forecasting model."""
    rets = close.pct_change().dropna().tail(lookback)
    if len(rets) < 60:
        return None
    mu_daily, sigma_daily = rets.mean(), rets.std()
    mu_h = mu_daily * horizon_days
    sigma_h = sigma_daily * np.sqrt(horizon_days)
    if sigma_h == 0:
        return None
    return float(norm.cdf(mu_h / sigma_h))


def relative_mispricing(stock_close: pd.Series, index_close: pd.Series, window: int = 50):
    """Stock's own cumulative return vs the index's, over the same window —
    catches genuine stock-specific dislocation, unlike the absolute deviation
    measure above which flags almost everything during a broad market selloff
    (if NIFTY is down 8%, most stocks look 'underpriced' vs their own mean
    even though nothing stock-specific happened)."""
    if len(stock_close) < window + 1 or len(index_close) < window + 1:
        return None
    stock_ret = stock_close.iloc[-1] / stock_close.iloc[-window] - 1
    idx_ret = index_close.iloc[-1] / index_close.iloc[-window] - 1
    return (stock_ret - idx_ret) * 100  # percentage points of relative performance


def momentum_12_1(close: pd.Series):
    if len(close) < 260:
        return None
    return float(close.iloc[-22] / close.iloc[-253] - 1)


def analyze_one(ticker: str, df: pd.DataFrame, index_df: pd.DataFrame):
    close = df["Close"]
    if len(close) < 260:
        return {"insufficient_data": True}

    pct_dev, z = mispricing_zscore(close)
    rel_mispricing = relative_mispricing(close, index_df["Close"])
    beta = beta_vs_index(close, index_df["Close"])
    p_up = probability_up(close)
    mom = momentum_12_1(close)
    ann_vol = float(close.pct_change().tail(63).std() * np.sqrt(252) * 100)

    rel_flag = bool(rel_mispricing is not None and abs(rel_mispricing) > MISPRICING_THRESHOLD_PCT)
    return {
        "price": round(float(close.iloc[-1]), 2),
        "pct_deviation_from_50d_mean": round(float(pct_dev), 2) if pd.notna(pct_dev) else None,
        "zscore_50d": round(float(z), 2) if pd.notna(z) else None,
        "mispriced_flag": bool(pd.notna(pct_dev) and abs(pct_dev) > MISPRICING_THRESHOLD_PCT),
        "mispricing_direction": ("overpriced" if pct_dev > 0 else "underpriced") if pd.notna(pct_dev) and abs(pct_dev) > MISPRICING_THRESHOLD_PCT else None,
        "relative_mispricing_vs_nifty_pct": round(rel_mispricing, 2) if rel_mispricing is not None else None,
        "relative_mispriced_flag": rel_flag,
        "relative_mispricing_note": "stock-specific move vs NIFTY over same window — this is the more meaningful flag during a broad market selloff",
        "beta_vs_nifty": round(beta, 2) if beta is not None else None,
        "annualized_volatility_pct": round(ann_vol, 1),
        "probability_up_21d": round(p_up, 3) if p_up is not None else None,
        "momentum_12_1": round(mom, 4) if mom is not None else None,
    }


def strategy_kelly_fraction(monthly_returns: pd.Series, safety_multiplier: float = 0.5) -> dict:
    """Kelly sizing from the momentum strategy's own realized monthly returns.

    Primary estimate is CONTINUOUS Kelly (f* = mu/sigma^2) — the standard
    Kelly-for-investing formula (Thorp) for a continuously-compounding return
    stream, which is what this strategy actually is. Discrete win/loss Kelly
    (the coin-flip formula) is reported alongside as a diagnostic only — it
    assumes fixed-size binary bets, a mismatch for variable monthly returns,
    and blending the two via min() previously produced a nonsensical result
    (6.7% of capital) that contradicted a strategy already beating the index.

    Kelly estimates from ~80 monthly data points are noisy — mu and especially
    sigma^2 have real estimation error, and continuous Kelly is known to be
    very sensitive to it. Treat the raw number as directional evidence about
    whether full deployment is reasonable, not a literal leverage instruction.
    This account has no margin, so the applied fraction is hard-capped at 1.0
    (fully invested) regardless of what raw Kelly suggests beyond that.
    """
    rets = monthly_returns.dropna()
    wins = rets[rets > 0]
    losses = rets[rets < 0]
    p = len(wins) / len(rets) if len(rets) else 0
    avg_win = wins.mean() if len(wins) else 0
    avg_loss = abs(losses.mean()) if len(losses) else 0
    b = avg_win / avg_loss if avg_loss > 0 else 0
    discrete_kelly = (p - (1 - p) / b) if b > 0 else 0

    mu, sigma2 = rets.mean(), rets.var()
    continuous_kelly = mu / sigma2 if sigma2 > 0 else 0

    applied = max(0.0, min(continuous_kelly * safety_multiplier, 1.0))

    return {
        "win_rate": round(p, 3), "avg_win": round(avg_win, 4), "avg_loss": round(avg_loss, 4),
        "payoff_ratio_diagnostic_only": round(b, 2),
        "discrete_kelly_diagnostic_only": round(discrete_kelly, 3),
        "continuous_kelly_raw": round(continuous_kelly, 3),
        "safety_multiplier": safety_multiplier,
        "applied_fraction_of_capital": round(applied, 3),
        "note": ("Continuous Kelly (mu/sigma^2) is the basis, at "
                 f"{int(safety_multiplier*100)}% of raw (estimation error on ~80 months "
                 "of data makes full Kelly unreliable), hard-capped at 100% since this "
                 "account has no margin. This is total-capital deployment, not a per-stock weight."),
    }


def run(data: dict, index_df: pd.DataFrame) -> dict:
    return {ticker: analyze_one(ticker, df, index_df) for ticker, df in data.items()}


if __name__ == "__main__":
    from data_fetch import fetch_universe, INDEX
    from wide_universe import WIDE_UNIVERSE

    data = fetch_universe(WIDE_UNIVERSE, force=False)
    index_df = fetch_universe([INDEX], force=False)[INDEX]
    results = run(data, index_df)

    mispriced = {t: r for t, r in results.items() if r.get("mispriced_flag")}
    print(f"\n{len(mispriced)} stocks mispriced >8% from 50-day mean:")
    for t, r in sorted(mispriced.items(), key=lambda x: -abs(x[1]["pct_deviation_from_50d_mean"]))[:15]:
        print(f"  {t}: {r['pct_deviation_from_50d_mean']:+.1f}% ({r['mispricing_direction']}), "
              f"beta={r['beta_vs_nifty']}, P(up 21d)={r['probability_up_21d']}")

    RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results"
    momentum_eq = pd.read_csv(RESULTS_DIR / "wide_momentum_top5_equity.csv", index_col=0, parse_dates=True).iloc[:, 0]
    monthly_rets = momentum_eq.pct_change().dropna()
    kelly = strategy_kelly_fraction(monthly_rets)
    print(f"\nStrategy-level Kelly sizing:\n{kelly}")
