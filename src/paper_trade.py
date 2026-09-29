"""
Paper-trading harness — now driven by the Manager Bot (regime classification,
momentum selection filtered by technical/sentiment, Kelly-sized deployment)
instead of raw momentum ranking alone. See bots/manager_bot.py for the
decision logic and why selection stays anchored to the backtested momentum
signal rather than a new untested ensemble score.

Honesty about what this actually is: there is no persistent process running
between invocations — this script runs once per invocation (launchd fires it
on a schedule), using the latest end-of-day-ish price data available at run
time. Every run refreshes prices, re-runs all three analysis bots and the
manager (so the dashboard always reflects a fresh read), marks the paper
portfolio to market, and checks the kill-switch. It only actually TRADES on
the first run of a new month (the strategy's own cadence) or on a kill-switch
breach.

Run it with: python3 paper_trade.py
"""
import json
import sys
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_fetch import fetch_universe, refresh_latest, INDEX
from wide_universe import WIDE_UNIVERSE
import portfolio_momentum as pm
import costs
from bots import technical_bot, quant_bot, sentiment_bot, manager_bot

BASE_DIR = Path(__file__).resolve().parent.parent
LEDGER_PATH = BASE_DIR / "results" / "paper_ledger.json"
LOG_PATH = BASE_DIR / "logs" / "paper_trade_log.txt"
BOTS_OUTPUT_PATH = BASE_DIR / "results" / "bots_output.json"

INITIAL_CAPITAL = 20000
DRAWDOWN_KILL_PCT = 0.20


def load_state():
    if LEDGER_PATH.exists():
        return json.loads(LEDGER_PATH.read_text())
    return {
        "capital_initial": INITIAL_CAPITAL,
        "cash": INITIAL_CAPITAL,
        "holdings": {},  # ticker -> {"shares": int, "entry_price": float, "entry_date": str}
        "peak_equity": INITIAL_CAPITAL,
        "status": "ACTIVE",
        "halt_reason": None,
        "last_rebalance_month": None,  # "YYYY-MM"
        "trade_log": [],
        "equity_history": [],
    }


def save_state(state):
    LEDGER_PATH.write_text(json.dumps(state, indent=2, default=str))


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def mark_to_market(state, prices):
    equity = state["cash"]
    for t, pos in state["holdings"].items():
        px = prices.get(t)
        if px is not None:
            equity += pos["shares"] * px
    return equity


def liquidate_all(state, prices, reason):
    for t, pos in list(state["holdings"].items()):
        px = prices.get(t)
        if px is None:
            continue
        proceeds = pos["shares"] * px
        fee = costs.sell_cost(proceeds)
        state["cash"] += proceeds - fee
        pnl = proceeds - fee - (pos["shares"] * pos["entry_price"])
        state["trade_log"].append({
            "date": datetime.now().strftime("%Y-%m-%d"), "side": "SELL", "ticker": t,
            "shares": pos["shares"], "price": px, "fee": round(fee, 2), "pnl": round(pnl, 2),
            "reason": reason,
        })
        log(f"SELL {pos['shares']} {t} @ Rs{px:.2f} (fee Rs{fee:.2f}, pnl Rs{pnl:.2f}) — {reason}")
    state["holdings"] = {}


def run_all_bots(data, index_df):
    log("Running technical bot...")
    technical = technical_bot.run(data)
    log("Running quant bot...")
    quant = quant_bot.run(data, index_df)

    log("Running manager bot's regime + candidate selection...")
    regime_ok, candidates, as_of = pm.current_picks(data, index_df, top_k=15)

    log(f"Running sentiment bot on {len(candidates)} momentum-qualified candidates (not full universe, to keep runtime sane)...")
    sentiment = sentiment_bot.run(candidates) if candidates else {}

    momentum_eq_path = BASE_DIR / "results" / "wide_momentum_top5_equity.csv"
    kelly = {"applied_fraction_of_capital": 1.0, "note": "backtest curve not found, defaulting to full deployment"}
    if momentum_eq_path.exists():
        momentum_eq = pd.read_csv(momentum_eq_path, index_col=0, parse_dates=True).iloc[:, 0]
        kelly = quant_bot.strategy_kelly_fraction(momentum_eq.pct_change().dropna())

    decision = manager_bot.decide(data, index_df, technical, quant, sentiment, kelly)

    output = {
        "generated_at": datetime.now().isoformat(),
        "technical": technical,
        "quant": quant,
        "sentiment": sentiment,
        "kelly": kelly,
        "decision": decision,
    }
    BOTS_OUTPUT_PATH.write_text(json.dumps(output, indent=2, default=str))
    log(f"Manager decision: mode={decision['strategy_mode']}, "
        f"deploy={decision['capital_fraction_to_deploy']*100:.1f}%, "
        f"picks={[p['ticker'] for p in decision['final_picks']]}")
    return decision


def rebalance(state, data, decision):
    prices = {t: df["Close"].iloc[-1] for t, df in data.items()}
    as_of = decision["as_of"]

    liquidate_all(state, prices, "monthly rebalance")

    picks = [p["ticker"] for p in decision["final_picks"]]
    capital_fraction = decision["capital_fraction_to_deploy"]

    if not picks or capital_fraction <= 0:
        log(f"No qualifying picks / 0% capital fraction as of {as_of} ({decision['strategy_mode']}) — staying in cash")
        state["trade_log"].append({"date": as_of, "side": "NONE",
                                     "reason": f"mode={decision['strategy_mode']}, no qualifying picks or 0% Kelly allocation"})
    else:
        total_equity = mark_to_market(state, prices)
        deployable = total_equity * capital_fraction
        alloc = deployable / len(picks)
        for t in picks:
            price = prices.get(t)
            if price is None:
                continue
            fee_est = costs.buy_cost(alloc)
            shares = int((alloc - fee_est) // price)
            if shares > 0:
                spent = shares * price
                fee = costs.buy_cost(spent)
                state["cash"] -= (spent + fee)
                state["holdings"][t] = {"shares": shares, "entry_price": price, "entry_date": as_of}
                state["trade_log"].append({
                    "date": as_of, "side": "BUY", "ticker": t,
                    "shares": shares, "price": price, "fee": round(fee, 2),
                })
                log(f"BUY {shares} {t} @ Rs{price:.2f} (fee Rs{fee:.2f})")
        log(f"Rebalanced into {picks} as of {as_of}, {capital_fraction*100:.1f}% of capital deployed "
            f"({decision['strategy_mode']} mode)")

    state["last_rebalance_month"] = as_of[:7]  # "YYYY-MM"


def main():
    log("=" * 60)
    log("Paper trade run starting")
    state = load_state()

    if state["status"] == "HALTED":
        log(f"Bot is HALTED ({state['halt_reason']}). No action taken. "
            f"Delete/edit {LEDGER_PATH.name} to reset.")
        return

    log("Refreshing latest price data...")
    refresh_latest(WIDE_UNIVERSE + [INDEX], lookback="5d")
    data = fetch_universe(WIDE_UNIVERSE, force=False)
    index_df = fetch_universe([INDEX], force=False)[INDEX]

    decision = run_all_bots(data, index_df)

    latest_prices = {t: df["Close"].iloc[-1] for t, df in data.items()}
    as_of_date = data[list(data.keys())[0]].index[-1]

    equity = mark_to_market(state, latest_prices)
    state["peak_equity"] = max(state["peak_equity"], equity)
    drawdown = equity / state["peak_equity"] - 1
    log(f"As of {as_of_date.date()}: equity = Rs {equity:.2f}, peak = Rs {state['peak_equity']:.2f}, "
        f"drawdown = {drawdown*100:.2f}%")

    if drawdown <= -DRAWDOWN_KILL_PCT:
        reason = f"drawdown {drawdown*100:.1f}% breached -{DRAWDOWN_KILL_PCT*100:.0f}% kill-switch"
        log(f"KILL-SWITCH TRIGGERED: {reason}")
        liquidate_all(state, latest_prices, reason)
        state["status"] = "HALTED"
        state["halt_reason"] = reason
    else:
        current_month = as_of_date.strftime("%Y-%m")
        if state["last_rebalance_month"] != current_month:
            log(f"New month ({current_month}) since last rebalance ({state['last_rebalance_month']}) — rebalancing")
            rebalance(state, data, decision)
        else:
            log(f"Already rebalanced this month ({current_month}). Holding: {list(state['holdings'].keys())}")

    equity_final = mark_to_market(state, latest_prices)
    as_of_str = str(as_of_date.date())
    entry = {"date": as_of_str, "equity": round(equity_final, 2)}
    if state["equity_history"] and state["equity_history"][-1]["date"] == as_of_str:
        state["equity_history"][-1] = entry  # re-running same trading day (no new close yet): overwrite, don't duplicate
    else:
        state["equity_history"].append(entry)
    save_state(state)
    log(f"Run complete. Equity: Rs {equity_final:.2f}  Status: {state['status']}")


if __name__ == "__main__":
    main()
