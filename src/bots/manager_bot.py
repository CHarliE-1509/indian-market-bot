"""
Manager Bot — weighs the Sentiment, Technical, and Quant bots' output to pick
a strategy mode, funnel macro -> sector -> stock, and produce a final
allocation with Kelly-derived total sizing.

Design principle: stock SELECTION stays anchored to the one thing that has
actually been rigorously backtested (12-1 month cross-sectional momentum with
a NIFTY-regime filter — see portfolio_momentum.py and the dashboard results).
Sentiment and technical scores are used as QUALIFYING FILTERS and tie-breaks
on top of that ranking, not as a new untested combined-alpha score. Letting
three freshly-built, unbacktested signals freely override the one validated
signal would just be introducing new overfitting risk dressed up as
sophistication.

Regime -> strategy mode:
  BULL_TRENDING  (NIFTY > 200SMA, ADX > 22): full momentum, Kelly-sized top-5
  BULL_CHOPPY    (NIFTY > 200SMA, ADX <= 22): momentum but smaller book (top-3),
                  half the Kelly fraction — momentum decays in choppy markets
  BEAR           (NIFTY <= 200SMA): mostly cash, matching the existing regime
                  filter's backtested behavior. A small tactical sleeve (<=20%
                  of capital) is allowed ONLY into names with positive relative
                  outperformance vs NIFTY, bullish technical, and non-bearish
                  sentiment — a deliberately narrow exception, not a new
                  strategy the backtest has validated.
"""
import sys
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from indicators import sma, adx  # noqa
import portfolio_momentum as pm  # noqa
from sector_map import SECTOR_MAP  # noqa


def classify_regime(index_df: pd.DataFrame) -> dict:
    close = index_df["Close"]
    sma200 = sma(close, 200)
    trend_strength = adx(index_df).iloc[-1]
    bull = close.iloc[-1] > sma200.iloc[-1]
    trending = trend_strength > 22

    if bull and trending:
        mode = "BULL_TRENDING"
    elif bull and not trending:
        mode = "BULL_CHOPPY"
    else:
        mode = "BEAR"

    return {
        "mode": mode,
        "nifty_close": round(float(close.iloc[-1]), 2),
        "nifty_sma200": round(float(sma200.iloc[-1]), 2),
        "pct_vs_sma200": round(float((close.iloc[-1] / sma200.iloc[-1] - 1) * 100), 2),
        "adx": round(float(trend_strength), 1),
    }


MODE_CONFIG = {
    "BULL_TRENDING": {"top_k": 5, "kelly_multiplier": 1.0, "min_technical_score": -0.3},
    "BULL_CHOPPY": {"top_k": 3, "kelly_multiplier": 0.5, "min_technical_score": -0.1},
    "BEAR": {"top_k": 2, "kelly_multiplier": 0.2, "min_technical_score": 0.2},  # tactical sleeve only
}


def rank_sectors(technical: dict, quant: dict) -> list:
    sector_scores = {}
    for ticker, sector in SECTOR_MAP.items():
        t = technical.get(ticker, {})
        q = quant.get(ticker, {})
        if "score" not in t or q.get("insufficient_data"):
            continue
        combined = t["score"] + (q.get("momentum_12_1") or 0) * 2  # momentum dominates, matches backtest weight
        sector_scores.setdefault(sector, []).append(combined)
    ranked = sorted(
        ((s, sum(v) / len(v)) for s, v in sector_scores.items()),
        key=lambda x: -x[1],
    )
    return [{"sector": s, "avg_score": round(v, 3)} for s, v in ranked]


def decide(data: dict, index_df: dict, technical: dict, quant: dict, sentiment: dict,
           kelly: dict) -> dict:
    regime = classify_regime(index_df)
    mode = regime["mode"]
    cfg = MODE_CONFIG[mode]

    regime_ok, momentum_picks, as_of = pm.current_picks(data, index_df, top_k=max(cfg["top_k"] * 3, 10))

    qualified = []
    disqualified = []
    for ticker in momentum_picks:
        t = technical.get(ticker, {})
        s = sentiment.get(ticker, {})
        reasons_out = []
        if t.get("score", 0) < cfg["min_technical_score"]:
            reasons_out.append(f"technical score {t.get('score')} below floor {cfg['min_technical_score']}")
        if s.get("label") == "bearish" and s.get("n_headlines", 0) >= 3:
            reasons_out.append(f"bearish news sentiment ({s.get('score')}, {s.get('n_headlines')} headlines)")
        if mode == "BEAR":
            rel = quant.get(ticker, {}).get("relative_mispricing_vs_nifty_pct")
            if rel is None or rel <= 0:
                reasons_out.append("bear-market tactical sleeve requires positive relative strength vs NIFTY")

        entry = {
            "ticker": ticker, "momentum_rank": momentum_picks.index(ticker) + 1,
            "technical_score": t.get("score"), "sentiment_label": s.get("label"),
            "sentiment_score": s.get("score"), "relative_mispricing_pct": quant.get(ticker, {}).get("relative_mispricing_vs_nifty_pct"),
        }
        if reasons_out:
            entry["disqualified_because"] = reasons_out
            disqualified.append(entry)
        else:
            qualified.append(entry)
        if len(qualified) >= cfg["top_k"]:
            break

    final_picks = qualified[:cfg["top_k"]] if regime_ok else []
    capital_fraction = 0.0 if not regime_ok and mode != "BEAR" else round(
        kelly.get("applied_fraction_of_capital", 1.0) * cfg["kelly_multiplier"], 3)
    if mode == "BEAR" and not final_picks:
        capital_fraction = 0.0

    sectors = rank_sectors(technical, quant)

    return {
        "as_of": str(as_of.date()),
        "regime": regime,
        "strategy_mode": mode,
        "mode_config": cfg,
        "regime_filter_ok": regime_ok,
        "capital_fraction_to_deploy": capital_fraction,
        "top_sectors": sectors[:5],
        "bottom_sectors": sectors[-3:],
        "final_picks": final_picks,
        "disqualified_candidates": disqualified,
        "explanation": (
            f"Regime classified as {mode} (NIFTY {regime['pct_vs_sma200']:+.1f}% vs its 200-day "
            f"average, ADX {regime['adx']}). Selection is momentum-ranked (the backtested edge); "
            f"technical and sentiment acted as qualifying filters, disqualifying "
            f"{len(disqualified)} of {len(qualified) + len(disqualified)} momentum-ranked candidates. "
            f"Deploying {capital_fraction*100:.1f}% of capital per Kelly sizing, adjusted "
            f"{cfg['kelly_multiplier']}x for this regime."
        ),
    }


if __name__ == "__main__":
    from data_fetch import fetch_universe, INDEX
    from wide_universe import WIDE_UNIVERSE
    import technical_bot, quant_bot, sentiment_bot

    data = fetch_universe(WIDE_UNIVERSE, force=False)
    index_df = fetch_universe([INDEX], force=False)[INDEX]

    print("Running technical bot...")
    technical = technical_bot.run(data)
    print("Running quant bot...")
    quant = quant_bot.run(data, index_df)
    print("Running sentiment bot on top momentum candidates only (to keep this test fast)...")
    _, candidates, _ = pm.current_picks(data, index_df, top_k=15)
    sentiment = sentiment_bot.run(candidates)

    RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results"
    momentum_eq = pd.read_csv(RESULTS_DIR / "wide_momentum_top5_equity.csv", index_col=0, parse_dates=True).iloc[:, 0]
    kelly = quant_bot.strategy_kelly_fraction(momentum_eq.pct_change().dropna())

    decision = decide(data, index_df, technical, quant, sentiment, kelly)
    import json
    print(json.dumps(decision, indent=2, default=str))
