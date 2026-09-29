"""
Generates the static GitHub Pages site (docs/) from the latest results:
paper_ledger.json, bots_output.json, and the backtest results/ files.

Run manually or (normally) from paper_trade.py at the end of each cycle.
"""
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import page_shell, kpi, chip, fmt_rs, CHART_JS  # noqa

BASE = Path(__file__).resolve().parent.parent
RESULTS = BASE / "results"
DOCS = BASE / "docs"
DOCS.mkdir(exist_ok=True)

# Placeholder — fill in after the Cloudflare Worker is deployed (see setup notes).
# Site works correctly without it, just without live-on-refresh price updates.
LIVE_QUOTE_PROXY_URL = ""


def load_json(path, default=None):
    p = RESULTS / path
    if p.exists():
        return json.loads(p.read_text())
    return default if default is not None else {}


def write_page(filename, html):
    (DOCS / filename).write_text(html)


def generate_index(ledger, bots):
    decision = bots.get("decision", {})
    regime = decision.get("regime", {})
    mode = decision.get("strategy_mode", "UNKNOWN")
    mode_chip = {"BULL_TRENDING": "good", "BULL_CHOPPY": "warning", "BEAR": "critical"}.get(mode, "neutral")

    equity_hist = ledger.get("equity_history", [])
    latest_equity = equity_hist[-1]["equity"] if equity_hist else ledger.get("capital_initial", 0)
    initial = ledger.get("capital_initial", 20000)
    pnl_pct = (latest_equity / initial - 1) * 100 if initial else 0
    peak = ledger.get("peak_equity", initial)
    drawdown_pct = (latest_equity / peak - 1) * 100 if peak else 0

    holdings_rows = ""
    for t, pos in ledger.get("holdings", {}).items():
        holdings_rows += (f'<tr><td>{t.replace(".NS","")}</td><td>{pos["shares"]}</td>'
                           f'<td>{fmt_rs(pos["entry_price"])}</td><td>{pos.get("entry_date","")}</td></tr>')
    if not holdings_rows:
        holdings_rows = '<tr><td colspan="4" style="text-align:center;color:var(--ink-muted);">No open positions — in cash</td></tr>'

    picks_rows = ""
    for p in decision.get("final_picks", []):
        picks_rows += (f'<tr><td>{p["ticker"].replace(".NS","")}</td><td>{p.get("technical_score")}</td>'
                        f'<td>{p.get("sentiment_label")}</td><td>{p.get("relative_mispricing_pct")}</td></tr>')
    if not picks_rows:
        picks_rows = f'<tr><td colspan="4" style="text-align:center;color:var(--ink-muted);">No qualifying trades this cycle ({mode})</td></tr>'

    chart_data = {"dates": [e["date"] for e in equity_hist], "values": [e["equity"] for e in equity_hist]}
    if len(chart_data["dates"]) < 2:
        chart_data = {"dates": [chart_data["dates"][0] if chart_data["dates"] else "-", "-"],
                      "values": [chart_data["values"][0] if chart_data["values"] else initial, initial]}

    body = f"""
<header class="page-head">
  <div class="eyebrow">Live paper trading &middot; Rs {initial:,} start</div>
  <h1>Portfolio overview</h1>
  <p class="lede">Regime-adaptive momentum strategy, filtered by the Technical and Sentiment bots, sized by Kelly criterion. See the Manager page for how this cycle's decision was reached.</p>
</header>

<section>
  <div class="kpi-row">
    {kpi("Current equity", fmt_rs(latest_equity))}
    {kpi("Total return", f"{pnl_pct:+.2f}%", "pos" if pnl_pct >= 0 else "neg")}
    {kpi("Drawdown from peak", f"{drawdown_pct:.2f}%", "neg" if drawdown_pct < -1 else "")}
    {kpi("Status", ledger.get("status", "UNKNOWN"), "neg" if ledger.get("status") == "HALTED" else "pos")}
    {kpi("Strategy mode", mode)}
  </div>
</section>

<section>
  <h2>Equity curve</h2>
  <div class="chart-card">
    <div class="legend"><div class="legend-item"><span class="legend-swatch" style="background:var(--series-1)"></span>Portfolio value</div></div>
    <div class="chart-wrap"><svg id="chart-equity" style="width:100%;height:auto;"></svg><div class="tooltip" id="tt-equity"></div></div>
  </div>
</section>

<section>
  <div class="grid-2">
    <div class="card">
      <h3>Current positions</h3>
      <div class="table-scroll"><table>
        <thead><tr><th>Stock</th><th>Shares</th><th>Entry price</th><th>Entry date</th></tr></thead>
        <tbody>{holdings_rows}</tbody>
      </table></div>
    </div>
    <div class="card">
      <h3>This cycle's eligible trades</h3>
      <div class="table-scroll"><table>
        <thead><tr><th>Stock</th><th>Technical</th><th>Sentiment</th><th>Rel. vs NIFTY</th></tr></thead>
        <tbody>{picks_rows}</tbody>
      </table></div>
    </div>
  </div>
</section>

<section>
  <div class="callout info">
    <b>Regime:</b> {chip(mode, mode_chip)} &mdash; NIFTY is {regime.get('pct_vs_sma200', 0):+.1f}% vs its 200-day average (ADX {regime.get('adx', '-')}).
    Deploying {decision.get('capital_fraction_to_deploy', 0)*100:.1f}% of capital this cycle.
    <a href="manager.html">Full reasoning &rarr;</a>
  </div>
</section>

{CHART_JS}
<script>
const chartData = {json.dumps(chart_data)};
drawMultiLine(document.getElementById('chart-equity'), document.getElementById('tt-equity'),
  chartData.dates, [{{label:'Equity', values: chartData.values, color: getComputedStyle(document.documentElement).getPropertyValue('--series-1').trim()}}], {{h:280}});
</script>
"""
    write_page("index.html", page_shell("Portfolio Overview", "index.html", body, bots.get("generated_at", "")[:16].replace("T"," ")))


def generate_manager(bots):
    decision = bots.get("decision", {})
    regime = decision.get("regime", {})
    mode = decision.get("strategy_mode", "UNKNOWN")

    sector_rows = "".join(f'<tr><td>{s["sector"]}</td><td>{s["avg_score"]:+.3f}</td></tr>' for s in decision.get("top_sectors", []))
    bottom_sector_rows = "".join(f'<tr><td>{s["sector"]}</td><td>{s["avg_score"]:+.3f}</td></tr>' for s in decision.get("bottom_sectors", []))

    def candidate_rows(items, show_reason=False):
        rows = ""
        for c in items:
            reason = f'<td>{"; ".join(c.get("disqualified_because", []))}</td>' if show_reason else ""
            rows += (f'<tr><td>{c["ticker"].replace(".NS","")}</td><td>{c.get("momentum_rank","-")}</td>'
                      f'<td>{c.get("technical_score")}</td><td>{c.get("sentiment_label")}</td>{reason}</tr>')
        return rows or '<tr><td colspan="5" style="text-align:center;color:var(--ink-muted);">None</td></tr>'

    body = f"""
<header class="page-head">
  <div class="eyebrow">Manager Bot</div>
  <h1>Regime classification &amp; decision funnel</h1>
  <p class="lede">{decision.get("explanation", "")}</p>
</header>

<section>
  <div class="kpi-row">
    {kpi("Strategy mode", mode)}
    {kpi("NIFTY vs 200d SMA", f"{regime.get('pct_vs_sma200',0):+.2f}%")}
    {kpi("Trend strength (ADX)", regime.get("adx","-"))}
    {kpi("Capital deployed", f"{decision.get('capital_fraction_to_deploy',0)*100:.1f}%")}
  </div>
</section>

<section>
  <h2>Macro &rarr; sector funnel</h2>
  <div class="grid-2">
    <div class="card"><h3>Strongest sectors right now</h3>
      <div class="table-scroll"><table><thead><tr><th>Sector</th><th>Avg score</th></tr></thead><tbody>{sector_rows}</tbody></table></div>
    </div>
    <div class="card"><h3>Weakest sectors right now</h3>
      <div class="table-scroll"><table><thead><tr><th>Sector</th><th>Avg score</th></tr></thead><tbody>{bottom_sector_rows}</tbody></table></div>
    </div>
  </div>
</section>

<section>
  <h2>Qualified picks (passed technical + sentiment filters)</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Stock</th><th>Momentum rank</th><th>Technical</th><th>Sentiment</th></tr></thead>
    <tbody>{candidate_rows(decision.get("final_picks", []))}</tbody>
  </table></div>
</section>

<section>
  <h2>Disqualified candidates (momentum-ranked, but filtered out)</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Stock</th><th>Momentum rank</th><th>Technical</th><th>Sentiment</th><th>Why disqualified</th></tr></thead>
    <tbody>{candidate_rows(decision.get("disqualified_candidates", []), show_reason=True)}</tbody>
  </table></div>
</section>

<section>
  <div class="callout">
    <b>Design note:</b> stock selection is anchored to 12-1 month cross-sectional momentum (the one backtested edge —
    see the Backtest page). Technical and sentiment scores are qualifying filters and tie-breaks on top of that ranking,
    not a new freely-combined score — that would introduce untested overfitting risk dressed up as sophistication.
  </div>
</section>
"""
    write_page("manager.html", page_shell("Manager Bot", "manager.html", body, bots.get("generated_at", "")[:16].replace("T"," ")))


def generate_quant(bots):
    quant = bots.get("quant", {})
    kelly = bots.get("kelly", {})

    rows = [(t, r) for t, r in quant.items() if not r.get("insufficient_data")]
    rel_mispriced = sorted([(t, r) for t, r in rows if r.get("relative_mispriced_flag")],
                            key=lambda x: -abs(x[1]["relative_mispricing_vs_nifty_pct"]))
    top_momentum = sorted(rows, key=lambda x: -(x[1].get("momentum_12_1") or -999))[:10]
    top_prob = sorted(rows, key=lambda x: -(x[1].get("probability_up_21d") or 0))[:10]

    def mis_rows():
        out = ""
        for t, r in rel_mispriced[:15]:
            direction = "outperforming" if r["relative_mispricing_vs_nifty_pct"] > 0 else "underperforming"
            out += (f'<tr><td>{t.replace(".NS","")}</td><td>{r["price"]}</td><td>{r["relative_mispricing_vs_nifty_pct"]:+.1f}pp</td>'
                    f'<td>{direction}</td><td>{r.get("beta_vs_nifty")}</td><td>{r.get("probability_up_21d")}</td></tr>')
        return out or '<tr><td colspan="6">None currently flagged</td></tr>'

    def mom_rows(items):
        return "".join(f'<tr><td>{t.replace(".NS","")}</td><td>{r["momentum_12_1"]*100:+.2f}%</td>'
                        f'<td>{r.get("annualized_volatility_pct")}%</td><td>{r.get("beta_vs_nifty")}</td></tr>' for t, r in items)

    def prob_rows(items):
        return "".join(f'<tr><td>{t.replace(".NS","")}</td><td>{r["probability_up_21d"]:.1%}</td>'
                        f'<td>{r.get("momentum_12_1", 0)*100:+.2f}%</td></tr>' for t, r in items)

    body = f"""
<header class="page-head">
  <div class="eyebrow">Quant Bot</div>
  <h1>Statistics, probability &amp; Kelly sizing</h1>
  <p class="lede">Mispricing, momentum, beta, volatility, and probability estimates across the universe, plus the strategy-level Kelly deployment fraction.</p>
</header>

<section>
  <h2>Kelly position sizing</h2>
  <div class="kpi-row">
    {kpi("Applied fraction of capital", f"{kelly.get('applied_fraction_of_capital',0)*100:.1f}%")}
    {kpi("Raw continuous Kelly", kelly.get("continuous_kelly_raw", "-"))}
    {kpi("Win rate (months)", f"{kelly.get('win_rate',0)*100:.1f}%")}
    {kpi("Payoff ratio", kelly.get("payoff_ratio_diagnostic_only", "-"))}
  </div>
  <p class="lede" style="margin-top:10px;">{kelly.get("note","")}</p>
</section>

<section>
  <h2>Relative mispricing vs NIFTY (&gt;8 percentage points)</h2>
  <p class="lede">Stock-specific moves, not just "everything fell with the market" — see the Backtest page for why this matters more than absolute deviation.</p>
  <div class="table-scroll"><table>
    <thead><tr><th>Stock</th><th>Price</th><th>vs NIFTY</th><th>Direction</th><th>Beta</th><th>P(up 21d)</th></tr></thead>
    <tbody>{mis_rows()}</tbody>
  </table></div>
</section>

<section>
  <div class="grid-2">
    <div class="card"><h3>Top momentum (12-1 month)</h3>
      <div class="table-scroll"><table><thead><tr><th>Stock</th><th>Momentum</th><th>Ann. vol</th><th>Beta</th></tr></thead>
      <tbody>{mom_rows(top_momentum)}</tbody></table></div>
    </div>
    <div class="card"><h3>Highest P(price up in 21 days)</h3>
      <div class="table-scroll"><table><thead><tr><th>Stock</th><th>P(up)</th><th>Momentum</th></tr></thead>
      <tbody>{prob_rows(top_prob)}</tbody></table></div>
    </div>
  </div>
</section>
"""
    write_page("quant.html", page_shell("Quant Bot", "quant.html", body, bots.get("generated_at", "")[:16].replace("T"," ")))


def generate_technical(bots):
    tech = {t: r for t, r in bots.get("technical", {}).items() if "score" in r}
    ranked = sorted(tech.items(), key=lambda x: -x[1]["score"])

    def rows(items):
        return "".join(f'<tr><td>{t.replace(".NS","")}</td><td>{r["score"]:+.3f}</td><td>{r["regime"]}</td>'
                        f'<td>{r["rsi14"]}</td><td>{r["adx"]}</td></tr>' for t, r in items)

    body = f"""
<header class="page-head">
  <div class="eyebrow">Technical Bot</div>
  <h1>Trend, momentum &amp; positioning</h1>
  <p class="lede">Combines trend alignment (price vs 20/50/200-day averages), MACD momentum, RSI positioning, and Bollinger %B into one score per stock, plus ADX-based regime tagging (trending vs choppy).</p>
</header>

<section>
  <div class="grid-2">
    <div class="card"><h3>Most bullish (technical)</h3>
      <div class="table-scroll"><table><thead><tr><th>Stock</th><th>Score</th><th>Regime</th><th>RSI</th><th>ADX</th></tr></thead>
      <tbody>{rows(ranked[:15])}</tbody></table></div>
    </div>
    <div class="card"><h3>Most bearish (technical)</h3>
      <div class="table-scroll"><table><thead><tr><th>Stock</th><th>Score</th><th>Regime</th><th>RSI</th><th>ADX</th></tr></thead>
      <tbody>{rows(list(reversed(ranked[-15:])))}</tbody></table></div>
    </div>
  </div>
</section>
"""
    write_page("technical.html", page_shell("Technical Bot", "technical.html", body, bots.get("generated_at", "")[:16].replace("T"," ")))


def generate_sentiment(bots):
    sent = bots.get("sentiment", {})
    ranked = sorted(sent.items(), key=lambda x: -x[1]["score"]) if sent else []

    def leaderboard(items):
        return "".join(f'<tr><td>{t.replace(".NS","")}</td><td>{r["score"]:+.3f}</td>'
                        f'<td>{chip(r["label"], {"bullish":"good","bearish":"critical","neutral":"neutral","no_data":"neutral"}.get(r["label"],"neutral"))}</td>'
                        f'<td>{r["n_headlines"]}</td></tr>' for t, r in items)

    headlines_html = ""
    for t, r in ranked[:6]:
        items = "".join(f'<div class="headline-item">{h["title"]}<br><span class="src">{h["source"]} &middot; sentiment {h["sentiment"]:+.2f}</span></div>' for h in r.get("top_headlines", []))
        if items:
            headlines_html += f'<div class="card" style="margin-bottom:12px;"><h3>{t.replace(".NS","")}</h3>{items}</div>'

    body = f"""
<header class="page-head">
  <div class="eyebrow">Sentiment Bot</div>
  <h1>News sentiment</h1>
  <p class="lede">Google News RSS headlines (last 72h) scored with VADER + a finance-specific lexicon patch (VADER alone gets headlines like "stock plunges" backwards). Mechanical scoring, no LLM judgment — this runs unattended via launchd with no connection to an interactive Claude session.</p>
</header>

{'<section><div class="callout">No candidates had sentiment computed this cycle — sentiment is only fetched for momentum-qualified candidates to keep runtime and request volume reasonable, and there were none this cycle.</div></section>' if not ranked else ''}

<section>
  <div class="grid-2">
    <div class="card"><h3>Most bullish news</h3>
      <div class="table-scroll"><table><thead><tr><th>Stock</th><th>Score</th><th>Label</th><th>Headlines</th></tr></thead>
      <tbody>{leaderboard(ranked[:10])}</tbody></table></div>
    </div>
    <div class="card"><h3>Most bearish news</h3>
      <div class="table-scroll"><table><thead><tr><th>Stock</th><th>Score</th><th>Label</th><th>Headlines</th></tr></thead>
      <tbody>{leaderboard(list(reversed(ranked[-10:])))}</tbody></table></div>
    </div>
  </div>
</section>

<section>
  <h2>Recent headlines, top movers</h2>
  {headlines_html or '<p class="lede">No headlines this cycle.</p>'}
</section>
"""
    write_page("sentiment.html", page_shell("Sentiment Bot", "sentiment.html", body, bots.get("generated_at", "")[:16].replace("T"," ")))


def generate_backtest():
    summary_path = RESULTS / "single_asset_summary.csv"
    wide_summary = load_json("wide_summary.json", {})
    mom5 = load_json("wide_momentum_top5_metrics.json", {})
    mc = load_json("wide_monte_carlo.json", {})
    nifty_bh = wide_summary.get("nifty_bh", {})

    body = f"""
<header class="page-head">
  <div class="eyebrow">Backtest results</div>
  <h1>Does this strategy have a real edge?</h1>
  <p class="lede">Full analysis (single-name technical rules, small-cap universe, capital sensitivity, Monte Carlo) is in the
  <a href="https://claude.ai/code/artifact/e5f04172-5819-42f6-ab04-0704c2489b78" target="_blank">full backtest report</a>.
  Headline numbers below.</p>
</header>

<section>
  <div class="kpi-row">
    {kpi("Momentum portfolio CAGR", f"{mom5.get('CAGR%','-')}%", "pos")}
    {kpi("Momentum max drawdown", f"{mom5.get('MaxDD%','-')}%")}
    {kpi("Momentum Sharpe", mom5.get("Sharpe","-"))}
    {kpi("NIFTY buy-and-hold CAGR", f"{nifty_bh.get('CAGR%','-')}%")}
    {kpi("NIFTY max drawdown", f"{nifty_bh.get('MaxDD%','-')}%")}
  </div>
</section>

<section>
  <div class="callout info">
    <b>Honest finding:</b> single-name technical trading (mean-reversion, trend+pullback) loses money on average
    across both a 19-stock and 85-stock liquid universe, net of realistic Indian transaction costs. The momentum
    portfolio (top-5, NIFTY-regime-filtered, monthly rebalance) is the one strategy with a genuine backtested edge —
    beating NIFTY on both return and drawdown at scale.
  </div>
</section>

<section>
  <h2>Monte Carlo risk check</h2>
  <p class="lede">Bootstrap-resampled the strategy's own monthly returns {mc.get('n_simulations', mc.get('pct_breach_20') and 5000 or '-')} times
  to see the range of outcomes the same edge could have produced under a different sequence of months.</p>
  <div class="kpi-row">
    {kpi("Median simulated CAGR", f"{mc.get('cagr_p50','-')}%")}
    {kpi("5th percentile CAGR", f"{mc.get('cagr_p5','-')}%")}
    {kpi("Chance of breaching -20% DD", f"{mc.get('pct_breach_20','-')}%", "neg")}
    {kpi("Chance of breaching -25% DD", f"{mc.get('pct_breach_25','-')}%", "neg")}
  </div>
</section>
"""
    write_page("backtest.html", page_shell("Backtest Results", "backtest.html", body, datetime.now().strftime("%Y-%m-%d %H:%M")))


def main():
    ledger = load_json("paper_ledger.json", {"capital_initial": 20000, "cash": 20000, "holdings": {},
                                               "peak_equity": 20000, "status": "ACTIVE", "equity_history": []})
    bots = load_json("bots_output.json", {"technical": {}, "quant": {}, "sentiment": {}, "kelly": {}, "decision": {}})

    generate_index(ledger, bots)
    generate_manager(bots)
    generate_quant(bots)
    generate_technical(bots)
    generate_sentiment(bots)
    generate_backtest()
    print(f"Site generated in {DOCS}")


if __name__ == "__main__":
    main()
