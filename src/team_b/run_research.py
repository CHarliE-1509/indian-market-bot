"""
Runs all Team B research (4 diffusion variants + analyst consensus screen)
and saves consolidated results for the Team B dashboard page. This is
research/monitoring only — see each module's docstring for findings.
Nothing here places trades; team_b_ledger.json stays uncommitted (cash)
until/unless a validated strategy exists.
"""
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "results" / "team_b"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LEDGER_PATH = RESULTS_DIR / "team_b_ledger.json"

INITIAL_CAPITAL = 20000


def init_ledger_if_needed():
    if LEDGER_PATH.exists():
        return json.loads(LEDGER_PATH.read_text())
    ledger = {
        "capital_initial": INITIAL_CAPITAL,
        "cash": INITIAL_CAPITAL,
        "holdings": {},
        "status": "UNCOMMITTED",
        "reason": "No Team B strategy has demonstrated backtested edge yet — see research findings. Capital sits in cash until one does.",
        "created_at": datetime.now().isoformat(),
    }
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2))
    return ledger


def main():
    print("=" * 60)
    print("Team B research run starting")
    init_ledger_if_needed()

    import diffusion_backtest as db
    import diffusion_variants as dv
    import analyst_consensus_bot as acb
    from wide_universe import WIDE_UNIVERSE
    from data_fetch import fetch_universe, INDEX
    import backtest_single as bts
    import benchmark as bm

    print("\n[1/5] Within-sector liquidity-tier diffusion...")
    data = fetch_universe(WIDE_UNIVERSE, force=False)
    index_df = fetch_universe([INDEX], force=False)[INDEX]
    baskets = db.build_leader_laggard_baskets(data)
    basket_rets = db.compute_basket_returns(data, baskets)
    lead_lag = db.test_lead_lag(basket_rets, baskets)
    best_lag = max(lead_lag, key=lambda k: abs(lead_lag[k]["correlation"]) if lead_lag[k]["correlation"] == lead_lag[k]["correlation"] else 0)
    eq = db.backtest_diffusion_strategy(data, index_df, baskets, basket_rets, best_lag, capital=500000)
    sector_liquidity_result = {
        "mechanism": "Within-sector liquidity-tier (leader/laggard by dollar volume) lead-lag",
        "n_sectors_tested": len(baskets),
        "lead_lag_by_day": lead_lag,
        "best_lag": int(best_lag),
        "backtest_metrics": bts.metrics(eq, __import__("pandas").DataFrame(), 500000),
        "verdict": "FAILED — negligible correlation (~0.03), backtest shows no edge vs NIFTY buy-and-hold.",
    }
    print(f"  Best lag {best_lag}d, correlation {lead_lag[best_lag]['correlation']}, backtest CAGR {sector_liquidity_result['backtest_metrics']['CAGR%']}%")

    print("\n[2/5] US overnight index diffusion...")
    us_result = dv.test_us_overnight_diffusion()
    print(f"  Gap corr {us_result['gap_correlation']}, intraday corr {us_result['intraday_correlation']}")

    print("\n[3/5] Commodity-to-equity diffusion...")
    commodity_result = dv.test_commodity_diffusion()
    print(f"  Tested {len(commodity_result['results_by_ticker'])} tickers")

    print("\n[4/5] ADR-to-NSE diffusion...")
    adr_result = dv.test_adr_diffusion()
    print(f"  Tested {len(adr_result['results_by_pair'])} pairs")

    print("\n[5/5] Analyst consensus screen (observational only, not backtested)...")
    consensus = acb.run(WIDE_UNIVERSE)
    print(f"  {len(consensus)}/{len(WIDE_UNIVERSE)} stocks had analyst coverage")

    nifty_bh = bm.buy_and_hold_metrics(index_df)

    output = {
        "generated_at": datetime.now().isoformat(),
        "nifty_bh_same_period": nifty_bh,
        "diffusion_tests": {
            "sector_liquidity_tier": sector_liquidity_result,
            "us_overnight_index": us_result,
            "commodity_to_equity": commodity_result,
            "adr_to_nse": adr_result,
        },
        "analyst_consensus": consensus,
        "conclusion": ("All four tested information-diffusion mechanisms failed to show retail-exploitable edge on free "
                       "daily NSE data — either negligible/noisy correlation, or (for the two cross-market tests) a real "
                       "correlation that is fully absorbed into NSE's opening price before market open. Analyst consensus "
                       "divergence cannot be backtested (no historical target-price data available for free) and remains "
                       "observational only. No Team B strategy currently has demonstrated edge; capital stays uncommitted."),
    }
    with open(RESULTS_DIR / "research_summary.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved consolidated results to {RESULTS_DIR / 'research_summary.json'}")


if __name__ == "__main__":
    main()
