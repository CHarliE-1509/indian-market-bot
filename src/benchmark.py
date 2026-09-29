import pandas as pd
import numpy as np


def buy_and_hold_metrics(df: pd.DataFrame, freq="daily") -> dict:
    close = df["Close"].dropna()
    rets = close.pct_change().dropna()
    n_years = (close.index[-1] - close.index[0]).days / 365.25
    cagr = (close.iloc[-1] / close.iloc[0]) ** (1 / n_years) - 1
    roll_max = close.cummax()
    dd = (close / roll_max - 1).min()
    ann = np.sqrt(252) if freq == "daily" else np.sqrt(12)
    sharpe = rets.mean() / rets.std() * ann if rets.std() > 0 else 0
    return {"CAGR%": round(cagr * 100, 2), "MaxDD%": round(dd * 100, 2), "Sharpe": round(sharpe, 2)}
