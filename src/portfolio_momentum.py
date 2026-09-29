"""
Cross-sectional momentum, monthly rebalance, across the full stock universe.
Tests whether the momentum edge exists at scale (needs capital big enough to
diversify — this is NOT the Rs 5,000 scenario, it's the "does the edge exist
at all" scenario).

Rule: rank stocks by 12-month return excluding the most recent month
(the standard momentum construction — skips the most recent month because
short-term reversal contaminates raw 12-month return). Hold top-K, equal
weight, rebalance monthly. Only rebalance into names when the index itself
is above its 200-day SMA (regime filter) — otherwise sit in cash.
"""
import numpy as np
import pandas as pd

import costs
from indicators import sma


def build_panel(data: dict, index_df: pd.DataFrame):
    closes = pd.DataFrame({t: df["Close"] for t, df in data.items()})
    closes = closes.dropna(how="all").ffill()
    idx = index_df.copy()
    idx["sma200"] = sma(idx["Close"], 200)
    idx = idx.reindex(closes.index, method="ffill")
    return closes, idx


def run(data: dict, index_df: pd.DataFrame, capital: float = 500000, top_k: int = 5):
    closes, idx = build_panel(data, index_df)
    month_ends = closes.resample("ME").last().index

    cash = capital
    holdings = {}  # ticker -> shares
    equity_curve = []
    rebal_log = []

    trading_days = closes.index
    for me in month_ends:
        pos = trading_days.searchsorted(me)
        if pos >= len(trading_days):
            continue
        rebal_date_idx = min(pos + 1, len(trading_days) - 1)  # trade next available day
        rebal_date = trading_days[rebal_date_idx]

        lookback_date_idx = trading_days.searchsorted(me) - 21  # ~1 month before month-end
        start_date_idx = trading_days.searchsorted(me) - 252     # ~12 months before
        if start_date_idx < 0 or lookback_date_idx < 0:
            continue

        idx_row = idx.loc[me] if me in idx.index else idx.iloc[idx.index.get_indexer([me], method="ffill")[0]]
        regime_ok = bool(not pd.isna(idx_row["sma200"]) and idx_row["Close"] > idx_row["sma200"])

        # liquidate everything first (month-end rebalance)
        px_today = closes.loc[rebal_date]
        for t, sh in list(holdings.items()):
            proceeds = sh * px_today[t]
            fee = costs.sell_cost(proceeds)
            cash += proceeds - fee
        holdings = {}

        if regime_ok:
            mom = closes.loc[trading_days[lookback_date_idx]] / closes.loc[trading_days[start_date_idx]] - 1
            mom = mom.dropna().sort_values(ascending=False)
            picks = mom.head(top_k).index.tolist()
            if picks:
                alloc = cash / len(picks)
                for t in picks:
                    price = px_today[t]
                    fee_est = costs.buy_cost(alloc)
                    sh = int((alloc - fee_est) // price)
                    if sh > 0:
                        spent = sh * price
                        fee = costs.buy_cost(spent)
                        cash -= (spent + fee)
                        holdings[t] = sh
            rebal_log.append({"date": rebal_date, "picks": picks if regime_ok else []})
        else:
            rebal_log.append({"date": rebal_date, "picks": []})

        mtm = cash + sum(sh * px_today[t] for t, sh in holdings.items())
        equity_curve.append((rebal_date, mtm))

    # Monthly-resolution equity curve (sufficient for CAGR/Sharpe/MaxDD at this holding frequency).
    eq = pd.Series({d: v for d, v in equity_curve}).sort_index()
    return eq, rebal_log


def current_picks(data: dict, index_df: pd.DataFrame, top_k: int = 5):
    """Live use: rank as of the latest available trading day (not a historical
    month-end). Returns (regime_ok, picks_list, as_of_date)."""
    closes, idx = build_panel(data, index_df)
    trading_days = closes.index
    as_of = trading_days[-1]

    idx_row = idx.iloc[-1]
    regime_ok = bool(not pd.isna(idx_row["sma200"]) and idx_row["Close"] > idx_row["sma200"])

    lookback_idx = len(trading_days) - 1 - 21
    start_idx = len(trading_days) - 1 - 252
    if start_idx < 0 or lookback_idx < 0:
        return regime_ok, [], as_of

    mom = closes.iloc[lookback_idx] / closes.iloc[start_idx] - 1
    mom = mom.dropna().sort_values(ascending=False)
    picks = mom.head(top_k).index.tolist() if regime_ok else []
    return regime_ok, picks, as_of
