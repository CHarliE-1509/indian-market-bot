"""Re-run the core comparison on the wide (~85 stock) liquid universe, to check
whether the 19-stock findings were an artifact of a small sample."""
import warnings
warnings.filterwarnings("ignore")
import json
from pathlib import Path

import pandas as pd
import numpy as np

from data_fetch import fetch_universe, INDEX
from wide_universe import WIDE_UNIVERSE
import backtest_single as bts
import portfolio_momentum as pm
import benchmark as bm

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
YEARS = 7.99


def main():
    print("Loading wide universe...")
    data = fetch_universe(WIDE_UNIVERSE, force=False)
    index_df = fetch_universe([INDEX], force=False)[INDEX]

    # 1. single-asset average (hybrid only — mean-reversion-only already conclusively
    #    ruled out on the smaller universe, no need to repeat)
    rows = []
    for ticker, df in data.items():
        trades, eq = bts.run(df, index_df, mode="trend_pullback_hybrid", capital=500000)
        m = bts.metrics(eq, trades, 500000)
        m["ticker"] = ticker
        rows.append(m)
    single_df = pd.DataFrame(rows)
    single_df.to_csv(RESULTS_DIR / "wide_single_asset_results.csv", index=False)
    print(f"\n=== Single-asset hybrid, averaged across {len(single_df)} stocks (wide universe) ===")
    print(single_df[["CAGR%", "MaxDD%", "Sharpe", "WinRate%"]].mean().round(2))

    # 2. momentum portfolio at top-5 and top-8, Rs 5L
    for k in [5, 8]:
        eq, _ = pm.run(data, index_df, capital=500000, top_k=k)
        m = bts.metrics(eq, pd.DataFrame(), 500000, freq="monthly")
        print(f"\n=== Momentum portfolio, wide universe, top-{k} ===")
        print(m)
        eq.to_csv(RESULTS_DIR / f"wide_momentum_top{k}_equity.csv")
        with open(RESULTS_DIR / f"wide_momentum_top{k}_metrics.json", "w") as f:
            json.dump(m, f, indent=2)

    # 3. capital sensitivity on wide universe, top-5
    levels = [25000, 50000, 100000, 200000, 500000]
    sens_rows = []
    for cap in levels:
        eq, _ = pm.run(data, index_df, capital=cap, top_k=5)
        m = bts.metrics(eq, pd.DataFrame(), cap, freq="monthly")
        sens_rows.append({"capital": cap, **m})
        print(f"  Rs {cap:>9,}: CAGR {m['CAGR%']:>6.2f}%  MaxDD {m['MaxDD%']:>7.2f}%  Sharpe {m['Sharpe']:>5.2f}")
    pd.DataFrame(sens_rows).to_csv(RESULTS_DIR / "wide_capital_sensitivity.csv", index=False)

    nifty_bh = bm.buy_and_hold_metrics(index_df)
    print(f"\nNIFTY buy-and-hold (same period): {nifty_bh}")
    with open(RESULTS_DIR / "wide_summary.json", "w") as f:
        json.dump({
            "n_stocks": len(single_df),
            "single_asset_avg": single_df[["CAGR%", "MaxDD%", "Sharpe", "WinRate%"]].mean().round(2).to_dict(),
            "nifty_bh": nifty_bh,
        }, f, indent=2)


if __name__ == "__main__":
    main()
