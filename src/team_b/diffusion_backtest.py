"""
Team B, idea 2: information diffusion backtest.

Classic finding in the literature (Hong & Stein 1999; Hou 2007, "Industry
Information Diffusion and the Lead-lag Effect in Stock Returns"): information
reaches large, liquid, well-covered stocks first and diffuses to smaller,
less-followed stocks within the same industry with a lag. This tests whether
that effect is exploitable on NSE with realistic costs.

Method:
  1. Within each sector, rank stocks by trailing 60-day dollar volume
     (price * volume) as a liquidity/coverage proxy (no market-cap data
     available for free, so this substitutes for firm size).
  2. Split each sector into a "leader" basket (top half by dollar volume)
     and "laggard" basket (bottom half).
  3. Test lead-lag cross-correlation: does the leader basket's return at day
     t predict the laggard basket's return at day t+k, for k=1..5?
  4. Trading rule from whichever lag shows the strongest, most consistent
     effect: when the leader basket has an extreme day (top/bottom quintile
     move), take a same-direction position in the laggard basket the next
     day, hold for the lag period, exit.

This is fully independent from Team A's bots and strategy — only pure
infrastructure (costs.py, sector_map.py, data fetching) is shared, no
decision logic.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_fetch import fetch_universe, INDEX
from wide_universe import WIDE_UNIVERSE
from sector_map import SECTOR_MAP
import costs
import benchmark as bm

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results" / "team_b"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def build_leader_laggard_baskets(data: dict, lookback_liquidity: int = 60):
    """Returns {sector: {'leaders': [tickers], 'laggards': [tickers]}}"""
    sector_stocks = {}
    for ticker, sector in SECTOR_MAP.items():
        if ticker in data:
            sector_stocks.setdefault(sector, []).append(ticker)

    baskets = {}
    for sector, tickers in sector_stocks.items():
        if len(tickers) < 4:
            continue  # need enough names to split meaningfully
        dollar_vol = {}
        for t in tickers:
            df = data[t]
            dv = (df["Close"] * df["Volume"]).tail(lookback_liquidity).mean()
            dollar_vol[t] = dv
        ranked = sorted(tickers, key=lambda t: -dollar_vol[t])
        half = len(ranked) // 2
        baskets[sector] = {"leaders": ranked[:half], "laggards": ranked[half:]}
    return baskets


def compute_basket_returns(data: dict, baskets: dict):
    """Returns DataFrame indexed by date with columns {sector}_leader, {sector}_laggard"""
    closes = pd.DataFrame({t: df["Close"] for t, df in data.items()}).ffill()
    rets = closes.pct_change()

    out = {}
    for sector, b in baskets.items():
        out[f"{sector}__leader"] = rets[b["leaders"]].mean(axis=1)
        out[f"{sector}__laggard"] = rets[b["laggards"]].mean(axis=1)
    return pd.DataFrame(out)


def test_lead_lag(basket_rets: pd.DataFrame, baskets: dict, max_lag: int = 5):
    """Pools all sectors together to test whether leader return at t predicts
    laggard return at t+k, for k=1..max_lag. Returns correlation per lag."""
    results = {}
    for lag in range(1, max_lag + 1):
        leader_vals, laggard_vals = [], []
        for sector in baskets:
            leader = basket_rets[f"{sector}__leader"]
            laggard = basket_rets[f"{sector}__laggard"].shift(-lag)  # laggard's FUTURE return
            valid = leader.notna() & laggard.notna()
            leader_vals.extend(leader[valid].tolist())
            laggard_vals.extend(laggard[valid].tolist())
        corr = np.corrcoef(leader_vals, laggard_vals)[0, 1] if len(leader_vals) > 30 else np.nan
        results[lag] = {"correlation": round(float(corr), 4), "n_obs": len(leader_vals)}
    return results


def backtest_diffusion_strategy(data: dict, index_df: pd.DataFrame, baskets: dict,
                                  basket_rets: pd.DataFrame, best_lag: int,
                                  extreme_quantile: float = 0.8, capital: float = 500000):
    """Trading rule: for each sector, when the leader basket's return is in the
    top or bottom (1-extreme_quantile) of its own history, take a same-direction
    position in the laggard basket the next day, hold for best_lag days."""
    closes = pd.DataFrame({t: df["Close"] for t, df in data.items()}).ffill()
    trading_days = closes.index
    n = len(trading_days)

    # precompute extreme-day thresholds per sector (using expanding history to avoid lookahead:
    # simplification — use a fixed trailing 252-day rolling threshold instead of full-sample)
    signals = {}  # sector -> pd.Series of +1/-1/0 signal on the DAY the leader move happened
    for sector in baskets:
        leader = basket_rets[f"{sector}__leader"]
        roll_upper = leader.rolling(252, min_periods=60).quantile(extreme_quantile)
        roll_lower = leader.rolling(252, min_periods=60).quantile(1 - extreme_quantile)
        sig = pd.Series(0, index=leader.index)
        sig[leader >= roll_upper] = 1
        sig[leader <= roll_lower] = -1
        signals[sector] = sig

    cash = capital
    open_positions = []  # list of dicts: {sector, direction, entry_day_idx, exit_day_idx, tickers, shares_map}
    equity_curve = []

    for i in range(260, n - best_lag - 1):
        today = trading_days[i]

        # close any positions whose hold period ended (long-only: sell laggard basket at current price)
        still_open = []
        for pos in open_positions:
            if i >= pos["exit_day_idx"]:
                prices_now = closes.iloc[i]
                proceeds = sum(sh * prices_now[t] for t, sh in pos["shares_map"].items())
                fee = costs.sell_cost(proceeds)
                cash += proceeds - fee
            else:
                still_open.append(pos)
        open_positions = still_open

        # open new positions from today's signal (signal computed on leader's move at day i,
        # entering laggard basket at day i+1's close-to-close return, exiting at i+1+best_lag)
        for sector, sig in signals.items():
            if sig.iloc[i] == 1 and len(open_positions) < 10:  # cap concurrent positions, only LONG the laggard (no shorting — matches a cash account with no margin)
                tickers = baskets[sector]["laggards"]
                alloc = min(capital * 0.05, cash / max(1, 10 - len(open_positions)))  # small size per position
                if alloc < 1000 or i + 1 >= n:
                    continue
                entry_prices = closes.iloc[i + 1]
                per_stock = alloc / len(tickers)
                shares_map = {}
                spent_total = 0
                for t in tickers:
                    price = entry_prices[t]
                    fee_est = costs.buy_cost(per_stock)
                    sh = int((per_stock - fee_est) // price)
                    if sh > 0:
                        spent = sh * price
                        fee = costs.buy_cost(spent)
                        shares_map[t] = sh
                        spent_total += spent + fee
                if shares_map:
                    cash -= spent_total
                    open_positions.append({
                        "sector": sector, "direction": 1, "entry_day_idx": i + 1,
                        "exit_day_idx": min(i + 1 + best_lag, n - 1),
                        "shares_map": shares_map, "capital_committed": spent_total,
                    })

        mtm = cash
        prices_now = closes.iloc[i]
        for pos in open_positions:
            mtm += sum(sh * prices_now[t] for t, sh in pos["shares_map"].items())
        equity_curve.append((today, mtm))

    eq = pd.Series({d: v for d, v in equity_curve}).sort_index()
    return eq


def main():
    print("Loading data...")
    data = fetch_universe(WIDE_UNIVERSE, force=False)
    index_df = fetch_universe([INDEX], force=False)[INDEX]

    print("Building leader/laggard baskets per sector...")
    baskets = build_leader_laggard_baskets(data)
    print(f"  {len(baskets)} sectors with enough stocks to split: {list(baskets.keys())}")

    basket_rets = compute_basket_returns(data, baskets)

    print("\nTesting lead-lag cross-correlation (pooled across sectors)...")
    lead_lag = test_lead_lag(basket_rets, baskets)
    for lag, r in lead_lag.items():
        print(f"  lag={lag}d: correlation={r['correlation']}, n={r['n_obs']}")

    best_lag = max(lead_lag, key=lambda k: abs(lead_lag[k]["correlation"]) if not np.isnan(lead_lag[k]["correlation"]) else 0)
    print(f"\nStrongest lag: {best_lag} days (correlation {lead_lag[best_lag]['correlation']})")

    print(f"\nBacktesting trading rule at lag={best_lag}...")
    eq = backtest_diffusion_strategy(data, index_df, baskets, basket_rets, best_lag, capital=500000)

    import backtest_single as bts
    metrics = bts.metrics(eq, pd.DataFrame(), 500000)
    print(f"\nDiffusion strategy backtest: {metrics}")

    nifty_bh = bm.buy_and_hold_metrics(index_df)
    print(f"NIFTY buy-and-hold (same period): {nifty_bh}")

    import json
    eq.to_csv(RESULTS_DIR / "diffusion_equity.csv")
    with open(RESULTS_DIR / "diffusion_backtest_summary.json", "w") as f:
        json.dump({
            "lead_lag": lead_lag, "best_lag": int(best_lag),
            "metrics": metrics, "nifty_bh": nifty_bh,
            "n_sectors_tested": len(baskets),
        }, f, indent=2, default=str)
    print(f"\nSaved to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
