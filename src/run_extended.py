"""
Answers to the follow-up questions:
  a) Does a high-volatility small-cap universe do better with the hybrid strategy?
  b) What does Rs 5,000 split across 2-3 cheaper liquid large-caps look like?
  c) What's a sane minimum capital for the momentum portfolio (cash-drag test)?
  d) Monte Carlo bootstrap on the momentum strategy's monthly returns, since a
     single historical path (the run_all.py backtest) doesn't tell you the range
     of outcomes a different sequence of the same market could have produced.
"""
import json
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path

import numpy as np
import pandas as pd

from data_fetch import fetch_universe, UNIVERSE, INDEX
import backtest_single as bts
import portfolio_momentum as pm
import costs

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
SMALLCAP = ['SUZLON.NS','YESBANK.NS','IDEA.NS','RPOWER.NS','PNB.NS','IDFCFIRSTB.NS',
            'RVNL.NS','IEX.NS','SAIL.NS','NATIONALUM.NS','HINDCOPPER.NS','NHPC.NS',
            'TRIDENT.NS','JPPOWER.NS']
CHEAP_BASKET = ['WIPRO.NS', 'ITC.NS', 'KOTAKBANK.NS']
YEARS = 7.99


def section_a_smallcap(index_df):
    print("\n" + "=" * 70)
    print("(a) HIGH-VOLATILITY SMALL/MID-CAP UNIVERSE")
    print("=" * 70)
    data = fetch_universe(SMALLCAP, force=False)
    rows = []
    # Small/mid-caps have materially wider spreads than large caps — 0.08%/side
    # (the large-cap assumption) understates real cost here. 0.30%/side is a more
    # honest floor for these names; even that may be optimistic in a fast market.
    SMALLCAP_SLIPPAGE = 0.0030
    for ticker, df in data.items():
        vol = df["Close"].pct_change().std() * np.sqrt(252) * 100
        trades, eq = bts.run(df, index_df, mode="trend_pullback_hybrid", capital=500000,
                              slippage_per_side=SMALLCAP_SLIPPAGE)
        m = bts.metrics(eq, trades, 500000)
        m.update({"ticker": ticker, "ann_volatility_pct": round(vol, 1)})
        rows.append(m)
    df_out = pd.DataFrame(rows).sort_values("Sharpe", ascending=False)
    df_out.to_csv(RESULTS_DIR / "smallcap_hybrid_results.csv", index=False)
    print(df_out[["ticker", "ann_volatility_pct", "CAGR%", "MaxDD%", "Sharpe", "Trades", "WinRate%"]]
          .to_string(index=False))
    print(f"\nAverage CAGR: {df_out['CAGR%'].mean():.2f}%  Average Sharpe: {df_out['Sharpe'].mean():.2f}"
          f"  Average MaxDD: {df_out['MaxDD%'].mean():.2f}%")
    return df_out


def section_b_cheap_basket(index_df):
    print("\n" + "=" * 70)
    print("(b) RS 5,000 SPLIT ACROSS 3 CHEAPER LIQUID LARGE-CAPS")
    print("=" * 70)
    data = fetch_universe(CHEAP_BASKET, force=False)
    per_stock_capital = 5000 / len(CHEAP_BASKET)
    curves = []
    all_trades = 0
    for ticker, df in data.items():
        trades, eq = bts.run(df, index_df, mode="trend_pullback_hybrid", capital=per_stock_capital)
        curves.append(eq.rename(ticker))
        all_trades += len(trades[trades["side"] == "SELL"]) if len(trades) else 0
        print(f"  {ticker}: Rs {per_stock_capital:.0f} -> Rs {eq.iloc[-1]:.0f}")
    combined = pd.concat(curves, axis=1).ffill().bfill().sum(axis=1)
    m = bts.metrics(combined, pd.DataFrame(), 5000)
    m["Trades"] = all_trades
    print(f"\nCombined Rs 5,000 basket ({', '.join(t.replace('.NS','') for t in CHEAP_BASKET)}): {m}")
    combined.to_csv(RESULTS_DIR / "rs5000_basket_equity.csv")
    with open(RESULTS_DIR / "rs5000_basket_summary.json", "w") as f:
        json.dump(m, f, indent=2)
    return combined, m


def section_c_capital_sensitivity(data, index_df):
    print("\n" + "=" * 70)
    print("(c) MINIMUM CAPITAL FOR THE MOMENTUM PORTFOLIO (cash-drag test)")
    print("=" * 70)
    levels = [25000, 50000, 100000, 200000, 500000, 1000000]
    rows = []
    for cap in levels:
        eq, rebal_log = pm.run(data, index_df, capital=cap, top_k=5)
        m = bts.metrics(eq, pd.DataFrame(), cap, freq="monthly")
        rows.append({"capital": cap, **m})
        print(f"  Rs {cap:>9,}: CAGR {m['CAGR%']:>6.2f}%  MaxDD {m['MaxDD%']:>7.2f}%  Sharpe {m['Sharpe']:>5.2f}")
    df_out = pd.DataFrame(rows)
    df_out.to_csv(RESULTS_DIR / "capital_sensitivity.csv", index=False)
    return df_out


def section_d_monte_carlo(mom_eq_path):
    print("\n" + "=" * 70)
    print("(d) MONTE CARLO BOOTSTRAP ON MOMENTUM STRATEGY RETURNS")
    print("=" * 70)
    eq = pd.read_csv(mom_eq_path, index_col=0, parse_dates=True).iloc[:, 0]
    rets = eq.pct_change().dropna().values
    n_months = len(rets)
    N_SIMS = 5000
    rng = np.random.default_rng(42)

    final_values = []
    max_drawdowns = []
    for _ in range(N_SIMS):
        sampled = rng.choice(rets, size=n_months, replace=True)  # i.i.d. bootstrap
        path = 500000 * np.cumprod(1 + sampled)
        roll_max = np.maximum.accumulate(path)
        dd = (path / roll_max - 1).min()
        final_values.append(path[-1])
        max_drawdowns.append(dd * 100)

    final_values = np.array(final_values)
    max_drawdowns = np.array(max_drawdowns)
    cagr_sim = (final_values / 500000) ** (1 / YEARS) - 1

    pct = lambda arr, p: np.percentile(arr, p)
    result = {
        "n_simulations": N_SIMS,
        "cagr_p5": round(pct(cagr_sim, 5) * 100, 2),
        "cagr_p50": round(pct(cagr_sim, 50) * 100, 2),
        "cagr_p95": round(pct(cagr_sim, 95) * 100, 2),
        "maxdd_p50": round(pct(max_drawdowns, 50), 2),
        "maxdd_p5": round(pct(max_drawdowns, 5), 2),   # 5th percentile = worse tail
        "maxdd_p1": round(pct(max_drawdowns, 1), 2),
        "pct_sims_breaching_20pct_dd": round((max_drawdowns < -20).mean() * 100, 1),
        "historical_realized_maxdd": -14.45,
    }
    print(json.dumps(result, indent=2))
    with open(RESULTS_DIR / "monte_carlo_momentum.json", "w") as f:
        json.dump(result, f, indent=2)
    return result


def main():
    print("Loading base universe + small-cap universe + index...")
    base_data = fetch_universe(force=False)
    index_df = base_data.pop(INDEX)

    smallcap_df = section_a_smallcap(index_df)
    basket_eq, basket_m = section_b_cheap_basket(index_df)
    sensitivity_df = section_c_capital_sensitivity(base_data, index_df)
    mc_result = section_d_monte_carlo(RESULTS_DIR / "momentum_portfolio_equity.csv")

    print("\nAll extended analysis written to", RESULTS_DIR)


if __name__ == "__main__":
    main()
