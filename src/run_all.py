import warnings
warnings.filterwarnings("ignore")

import json
from pathlib import Path

import pandas as pd

from data_fetch import fetch_universe, UNIVERSE, INDEX
import backtest_single as bts
import portfolio_momentum as pm
import benchmark as bm

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def main():
    print("Loading cached data...")
    data = fetch_universe(force=False)
    index_df = data.pop(INDEX)

    # --- 1. Single-asset strategy comparison, run on EVERY stock, at institutional
    #     capital (Rs 5 lakh) so fixed-cost drag doesn't distort the comparison ---
    rows = []
    per_stock_hybrid_eq = {}
    for ticker, df in data.items():
        for mode in ["mean_reversion_only", "trend_pullback_hybrid"]:
            trades, eq = bts.run(df, index_df, mode=mode, capital=500000)
            m = bts.metrics(eq, trades, 500000)
            m.update({"ticker": ticker, "mode": mode})
            rows.append(m)
            if mode == "trend_pullback_hybrid":
                per_stock_hybrid_eq[ticker] = eq

    single_df = pd.DataFrame(rows)
    single_df.to_csv(RESULTS_DIR / "single_asset_all_stocks.csv", index=False)

    summary = single_df.groupby("mode")[["CAGR%", "MaxDD%", "Sharpe", "WinRate%", "Trades"]].mean().round(2)
    print("\n=== Single-asset strategy: AVERAGE across 19 liquid stocks (Rs 5L each, isolated) ===")
    print(summary)
    summary.to_csv(RESULTS_DIR / "single_asset_summary.csv")

    # --- 2. Cross-sectional momentum portfolio at scale (Rs 5L, top-5, monthly) ---
    print("\nRunning portfolio momentum backtest...")
    mom_eq, rebal_log = pm.run(data, index_df, capital=500000, top_k=5)
    mom_metrics = bts.metrics(mom_eq, pd.DataFrame(), 500000, freq="monthly")
    print("\n=== Cross-sectional momentum portfolio (Rs 5L, top-5, monthly rebalance) ===")
    print(mom_metrics)
    mom_eq.to_csv(RESULTS_DIR / "momentum_portfolio_equity.csv")
    with open(RESULTS_DIR / "momentum_metrics.json", "w") as f:
        json.dump(mom_metrics, f, indent=2)

    # --- 3. The Rs 5,000 reality check: hybrid strategy, ONE stock at a time,
    #     starting capital Rs 5,000, using the single best-performing liquid
    #     stock from step 1 by Sharpe (i.e. what you'd realistically pick) ---
    best_ticker = single_df[single_df["mode"] == "trend_pullback_hybrid"].sort_values(
        "Sharpe", ascending=False).iloc[0]["ticker"]
    print(f"\nBest single-stock hybrid candidate by Sharpe: {best_ticker}")
    trades_5k, eq_5k = bts.run(data[best_ticker], index_df, mode="trend_pullback_hybrid", capital=5000)
    m_5k = bts.metrics(eq_5k, trades_5k, 5000)
    print(f"=== Rs 5,000 reality check: trend+pullback hybrid on {best_ticker} alone ===")
    print(m_5k)
    trades_5k.to_csv(RESULTS_DIR / "rs5000_trades.csv", index=False)
    eq_5k.to_csv(RESULTS_DIR / "rs5000_equity.csv")

    with open(RESULTS_DIR / "rs5000_summary.json", "w") as f:
        json.dump({"ticker": best_ticker, **m_5k}, f, indent=2)

    # --- 4. Benchmarks: NIFTY buy-and-hold, and equal-weight universe buy-and-hold ---
    nifty_bh = bm.buy_and_hold_metrics(index_df)
    ew_universe = pd.concat([df["Close"] / df["Close"].iloc[0] for df in data.values()], axis=1).mean(axis=1)
    ew_df = pd.DataFrame({"Close": ew_universe})
    ew_bh = bm.buy_and_hold_metrics(ew_df)

    nifty_curve_500k = (index_df["Close"] / index_df["Close"].iloc[0] * 500000)
    nifty_curve_500k.to_csv(RESULTS_DIR / "nifty_bh_500k_curve.csv")
    ew_curve_500k = ew_universe * 500000
    ew_curve_500k.to_csv(RESULTS_DIR / "equal_weight_bh_500k_curve.csv")

    # --- Export a compact JSON for the results dashboard (monthly-resolution
    #     comparison of the 3 portfolio-level curves, aligned to momentum's dates) ---
    mom_dates = mom_eq.index
    chart_data = {
        "dates": [d.strftime("%Y-%m") for d in mom_dates],
        "momentum": [round(v) for v in mom_eq.values],
        "nifty_bh": [round(v) for v in nifty_curve_500k.reindex(mom_dates, method="ffill").values],
        "equal_weight_bh": [round(v) for v in ew_curve_500k.reindex(mom_dates, method="ffill").values],
    }
    rs5000_dates = eq_5k.index
    rs5000_chart = {
        "dates": [d.strftime("%Y-%m-%d") for d in rs5000_dates[::5]],  # downsample daily->weekly-ish
        "values": [round(v, 2) for v in eq_5k.values[::5]],
    }
    with open(RESULTS_DIR / "dashboard_data.json", "w") as f:
        json.dump({
            "portfolio_chart": chart_data,
            "rs5000_chart": rs5000_chart,
            "single_asset_summary": summary.reset_index().to_dict(orient="records"),
            "momentum_metrics": mom_metrics,
            "rs5000_metrics": {"ticker": best_ticker, **m_5k},
            "nifty_bh": nifty_bh,
            "ew_bh": ew_bh,
        }, f, indent=2)
    print("\n=== Benchmarks (buy-and-hold, same period) ===")
    print(f"NIFTY 50 buy-and-hold:            {nifty_bh}")
    print(f"Equal-weight 19-stock buy-and-hold: {ew_bh}")
    with open(RESULTS_DIR / "benchmarks.json", "w") as f:
        json.dump({"nifty_bh": nifty_bh, "equal_weight_universe_bh": ew_bh}, f, indent=2)

    print(f"\nAll results written to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
