"""
Single-position, single-asset backtest engine.

Simulates trading ONE stock at a time with a fixed capital pool (mirrors the
Rs 5,000 real-money constraint: you can only hold one position, sized by
whatever capital is currently free). Signals are computed on day t's close;
orders execute at day t+1's open, to avoid lookahead bias. Costs come from
costs.py (STT, stamp duty, exchange charges, GST, slippage baked in).

Two rule sets are provided:
  - mean_reversion_only: RSI2 oversold entry / overbought exit, no trend filter
  - trend_pullback_hybrid: same entry timing, but gated by a trend filter on
    the stock AND a regime filter on the index (only trade long when both the
    stock and the broad market are in an uptrend)
"""
import numpy as np
import pandas as pd

from indicators import sma, rsi, atr
import costs


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["sma50"] = sma(d["Close"], 50)
    d["sma200"] = sma(d["Close"], 200)
    d["sma200_prev20"] = d["sma200"].shift(20)
    d["rsi2"] = rsi(d["Close"], 2)
    d["atr14"] = atr(d, 14)
    return d


def run(df: pd.DataFrame, index_df: pd.DataFrame, mode: str, capital: float = 100000,
        stop_atr_mult: float = 2.5, rsi_entry: float = 10, rsi_exit: float = 70,
        slippage_per_side: float = costs.SLIPPAGE_PER_SIDE):
    """
    mode: 'mean_reversion_only' or 'trend_pullback_hybrid'
    Returns (trades_df, equity_curve_series)
    """
    d = _prep(df)
    idx = index_df.copy()
    idx["sma200"] = sma(idx["Close"], 200)
    idx = idx.reindex(d.index, method="ffill")

    cash = capital
    shares = 0
    entry_price = None
    entry_atr = None
    trades = []
    equity_curve = []

    for i in range(1, len(d) - 1):
        row = d.iloc[i]
        nxt = d.iloc[i + 1]  # execution day
        today = d.index[i]

        if pd.isna(row["sma200"]) or pd.isna(row["atr14"]):
            equity_curve.append((today, cash + shares * row["Close"]))
            continue

        in_position = shares > 0

        if not in_position:
            trend_ok = row["Close"] > row["sma200"] and row["sma200"] > row["sma200_prev20"]
            if mode == "trend_pullback_hybrid":
                idx_row = idx.iloc[i]
                regime_ok = (not pd.isna(idx_row["sma200"])) and idx_row["Close"] > idx_row["sma200"]
                signal = trend_ok and regime_ok and row["rsi2"] < rsi_entry
            else:  # mean_reversion_only: no trend/regime filter at all
                signal = row["rsi2"] < rsi_entry

            if signal and not pd.isna(nxt["Open"]):
                buy_price = nxt["Open"]
                fee = costs.buy_cost(cash, slippage_per_side)
                investable = cash - fee
                shares = max(int(investable // buy_price), 0)
                if shares > 0:
                    spent = shares * buy_price
                    actual_fee = costs.buy_cost(spent, slippage_per_side)
                    cash = cash - spent - actual_fee
                    entry_price = buy_price
                    entry_atr = row["atr14"]
                    trades.append({"date": nxt.name, "side": "BUY", "price": buy_price,
                                    "shares": shares, "fee": actual_fee})
        else:
            stop_price = entry_price - stop_atr_mult * entry_atr
            trend_break = row["Close"] < row["sma50"]
            exit_signal = row["rsi2"] > rsi_exit or row["Close"] < stop_price or (
                mode == "trend_pullback_hybrid" and trend_break)

            if exit_signal and not pd.isna(nxt["Open"]):
                sell_price = nxt["Open"]
                proceeds = shares * sell_price
                fee = costs.sell_cost(proceeds, slippage_per_side)
                cash = cash + proceeds - fee
                trades.append({"date": nxt.name, "side": "SELL", "price": sell_price,
                                "shares": shares, "fee": fee,
                                "pnl": proceeds - fee - (shares * entry_price)})
                shares = 0
                entry_price = None
                entry_atr = None

        mtm = cash + shares * row["Close"]
        equity_curve.append((today, mtm))

    eq = pd.Series({d_: v for d_, v in equity_curve}).sort_index()
    trades_df = pd.DataFrame(trades)
    return trades_df, eq


def metrics(equity: pd.Series, trades: pd.DataFrame, capital: float, freq: str = "daily") -> dict:
    """freq: 'daily' (annualization factor sqrt(252)) or 'monthly' (sqrt(12)) —
    must match the actual spacing of `equity`'s index, or Sharpe is meaningless."""
    if len(equity) < 2:
        return {"CAGR%": 0, "MaxDD%": 0, "Sharpe": 0, "Trades": 0, "WinRate%": 0, "FinalValue": capital}
    rets = equity.pct_change().dropna()
    n_years = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = (equity.iloc[-1] / capital) ** (1 / n_years) - 1 if n_years > 0 else 0
    roll_max = equity.cummax()
    dd = (equity / roll_max - 1).min()
    ann_factor = np.sqrt(252) if freq == "daily" else np.sqrt(12)
    sharpe = (rets.mean() / rets.std() * ann_factor) if rets.std() > 0 else 0
    sells = trades[trades["side"] == "SELL"] if len(trades) else pd.DataFrame()
    win_rate = (sells["pnl"] > 0).mean() * 100 if len(sells) else 0
    return {
        "CAGR%": round(cagr * 100, 2),
        "MaxDD%": round(dd * 100, 2),
        "Sharpe": round(sharpe, 2),
        "Trades": len(sells),
        "WinRate%": round(win_rate, 1),
        "FinalValue": round(equity.iloc[-1], 0),
    }
