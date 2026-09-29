"""
Technical Bot — per-stock technical read, combining trend, momentum,
mean-reversion positioning, and trend-strength into one score in [-1, +1].

This does not decide trades on its own; it's one of three inputs the Manager
Bot weighs (alongside quant and sentiment). Fully mechanical, no external data
beyond price history, so it runs identically whether launched by a human or
by launchd at 3am.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from indicators import sma, rsi, atr, macd, bollinger_bands, adx  # noqa


def analyze_one(df: pd.DataFrame) -> dict:
    close = df["Close"]
    if len(close) < 210:
        return {"score": 0.0, "regime": "insufficient_data"}

    sma20, sma50, sma200 = sma(close, 20), sma(close, 50), sma(close, 200)
    rsi14 = rsi(close, 14)
    macd_line, signal_line, hist = macd(close)
    _, _, _, pct_b = bollinger_bands(close)
    adx14 = adx(df)

    c = close.iloc[-1]
    components = {}

    # Trend alignment: price vs short/medium/long MAs, each worth +/-1
    trend_score = 0
    trend_score += 1 if c > sma20.iloc[-1] else -1
    trend_score += 1 if c > sma50.iloc[-1] else -1
    trend_score += 1 if c > sma200.iloc[-1] else -1
    components["trend_alignment"] = trend_score / 3

    # MACD momentum: positive histogram = bullish momentum building
    components["macd_momentum"] = float(np.clip(hist.iloc[-1] / (abs(close.iloc[-20:]).mean() * 0.02), -1, 1))

    # RSI positioning: extreme readings pull score toward mean-reversion signal
    r = rsi14.iloc[-1]
    if r > 70:
        components["rsi_signal"] = -0.6  # overbought, caution
    elif r < 30:
        components["rsi_signal"] = 0.6   # oversold, potential bounce
    else:
        components["rsi_signal"] = (r - 50) / 50 * 0.3  # mild lean

    # Bollinger %B: near upper band = extended, near lower = potential support
    pb = pct_b.iloc[-1]
    if pd.isna(pb):
        components["bollinger_position"] = 0.0
    else:
        components["bollinger_position"] = float(np.clip((0.5 - pb) * 1.2, -1, 1)) * -1  # near upper band -> slightly negative (extended)

    trend_strength = adx14.iloc[-1]
    regime = "trending" if trend_strength > 25 else "choppy" if trend_strength < 18 else "transitional"

    weights = {"trend_alignment": 0.4, "macd_momentum": 0.3, "rsi_signal": 0.15, "bollinger_position": 0.15}
    score = sum(components[k] * w for k, w in weights.items())

    return {
        "score": round(float(np.clip(score, -1, 1)), 3),
        "regime": regime,
        "adx": round(float(trend_strength), 1),
        "rsi14": round(float(r), 1),
        "components": {k: round(v, 3) for k, v in components.items()},
        "price": round(float(c), 2),
        "sma20": round(float(sma20.iloc[-1]), 2),
        "sma50": round(float(sma50.iloc[-1]), 2),
        "sma200": round(float(sma200.iloc[-1]), 2),
    }


def run(data: dict) -> dict:
    return {ticker: analyze_one(df) for ticker, df in data.items()}


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from data_fetch import fetch_universe
    from wide_universe import WIDE_UNIVERSE
    data = fetch_universe(WIDE_UNIVERSE, force=False)
    results = run(data)
    ranked = sorted(results.items(), key=lambda x: -x[1]["score"])
    print("Most bullish (technical):")
    for t, r in ranked[:5]:
        print(f"  {t}: score={r['score']} regime={r['regime']} RSI={r['rsi14']}")
    print("Most bearish (technical):")
    for t, r in ranked[-5:]:
        print(f"  {t}: score={r['score']} regime={r['regime']} RSI={r['rsi14']}")
