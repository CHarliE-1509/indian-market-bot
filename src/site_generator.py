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

# Cloudflare Worker CORS proxy for live Yahoo Finance quotes (see cloudflare-worker.js).
# Site degrades gracefully to the last scheduled push if this is empty or unreachable.
LIVE_QUOTE_PROXY_URL = "https://nse-price-proxy.ktilak703.workers.dev"


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
    cash_for_live = ledger.get("cash", 0)

    holdings = ledger.get("holdings", {})
    holdings_rows = ""
    for t, pos in holdings.items():
        holdings_rows += (f'<tr data-ticker="{t}"><td>{t.replace(".NS","")}</td><td>{pos["shares"]}</td>'
                           f'<td>{fmt_rs(pos["entry_price"])}</td><td>{pos.get("entry_date","")}</td>'
                           f'<td class="num live-price" data-ticker-cell="{t}">&mdash;</td>'
                           f'<td class="num live-pnl" data-ticker-pnl="{t}">&mdash;</td></tr>')
    if not holdings_rows:
        holdings_rows = '<tr><td colspan="6" style="text-align:center;color:var(--ink-muted);">No open positions — in cash</td></tr>'

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
    {kpi("Current equity", fmt_rs(latest_equity), "pos" if pnl_pct >= 0 else "neg", "kpi-equity")}
    {kpi("Total return", f"{pnl_pct:+.2f}%", "pos" if pnl_pct >= 0 else "neg", "kpi-return")}
    {kpi("Drawdown from peak", f"{drawdown_pct:.2f}%", "neg" if drawdown_pct < -1 else "", "kpi-drawdown")}
    {kpi("Status", ledger.get("status", "UNKNOWN"), "neg" if ledger.get("status") == "HALTED" else "pos")}
    {kpi("Strategy mode", mode)}
  </div>
  <p id="live-indicator" style="font-size:11px;color:var(--ink-muted);margin:8px 0 0;">Showing last scheduled update (checking for live prices&hellip;)</p>
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
        <thead><tr><th>Stock</th><th>Shares</th><th>Entry price</th><th>Entry date</th><th>Live price</th><th>P&amp;L</th></tr></thead>
        <tbody id="holdings-tbody">{holdings_rows}</tbody>
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

<script>
(function() {{
  const PROXY = {json.dumps(LIVE_QUOTE_PROXY_URL)};
  const HOLDINGS = {json.dumps(holdings)};
  const CASH = {cash_for_live};
  const PEAK_EQUITY = {peak};
  const INITIAL = {initial};
  const indicator = document.getElementById('live-indicator');

  if (!PROXY) {{
    indicator.textContent = 'Showing last scheduled update (live price proxy not configured)';
    return;
  }}

  async function fetchQuote(ticker) {{
    const r = await fetch(`${{PROXY}}/?symbol=${{encodeURIComponent(ticker)}}`);
    if (!r.ok) throw new Error('bad response');
    const data = await r.json();
    return data.chart.result[0].meta.regularMarketPrice;
  }}

  async function refreshLive() {{
    const tickers = Object.keys(HOLDINGS);
    try {{
      const prices = await Promise.all(tickers.map(t => fetchQuote(t).catch(() => null)));
      let liveEquity = CASH;
      let anyFailed = false;
      tickers.forEach((t, i) => {{
        const price = prices[i];
        const priceCell = document.querySelector(`[data-ticker-cell="${{t}}"]`);
        const pnlCell = document.querySelector(`[data-ticker-pnl="${{t}}"]`);
        if (price == null) {{ anyFailed = true; if (priceCell) priceCell.textContent = 'n/a'; return; }}
        const pos = HOLDINGS[t];
        liveEquity += pos.shares * price;
        const pnl = (price - pos.entry_price) * pos.shares;
        const pnlPct = (price / pos.entry_price - 1) * 100;
        if (priceCell) priceCell.textContent = '₹' + price.toFixed(2);
        if (pnlCell) {{
          pnlCell.textContent = (pnl >= 0 ? '+' : '') + '₹' + pnl.toFixed(0) + ' (' + pnlPct.toFixed(1) + '%)';
          pnlCell.style.color = pnl >= 0 ? 'var(--good)' : 'var(--critical)';
        }}
      }});

      if (tickers.length === 0 || !anyFailed) {{
        const pnlPct = (liveEquity / INITIAL - 1) * 100;
        const ddPct = (liveEquity / Math.max(PEAK_EQUITY, liveEquity) - 1) * 100;
        document.getElementById('kpi-equity').textContent = fmtRsJS(liveEquity);
        document.getElementById('kpi-return').textContent = (pnlPct >= 0 ? '+' : '') + pnlPct.toFixed(2) + '%';
        document.getElementById('kpi-drawdown').textContent = ddPct.toFixed(2) + '%';
        indicator.textContent = 'Live prices as of ' + new Date().toLocaleTimeString('en-IN', {{hour: '2-digit', minute:'2-digit'}});
        indicator.style.color = 'var(--good)';
      }} else {{
        indicator.textContent = 'Some live prices unavailable — showing last scheduled update for those';
      }}
    }} catch (e) {{
      indicator.textContent = 'Live price fetch failed — showing last scheduled update';
    }}
  }}

  refreshLive();
}})();
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


def generate_montecarlo(ledger, bots):
    sys.path.insert(0, str(Path(__file__).resolve().parent / "bots"))
    from bots import montecarlo_bot
    from bots.sentiment_bot import COMPANY_NAMES

    from data_fetch import fetch_universe, INDEX
    from wide_universe import WIDE_UNIVERSE
    data = fetch_universe(WIDE_UNIVERSE, force=False)
    params = montecarlo_bot.run(data)

    holdings = list(ledger.get("holdings", {}).keys())
    decision_picks = [p["ticker"] for p in bots.get("decision", {}).get("final_picks", [])]
    default_ticker = (holdings[0] if holdings else
                       decision_picks[0] if decision_picks else
                       "RELIANCE.NS")
    if default_ticker not in params:
        default_ticker = next(iter(params))

    options_html = "".join(
        f'<option value="{t}"{" selected" if t == default_ticker else ""}>{COMPANY_NAMES.get(t, t.replace(".NS",""))}</option>'
        for t in sorted(params.keys(), key=lambda t: COMPANY_NAMES.get(t, t))
    )
    default_note = ("your current position" if default_ticker in holdings else
                     "this cycle's top pick" if default_ticker in decision_picks else
                     "no current position — showing an example")

    body = f"""
<header class="page-head">
  <div class="eyebrow">Monte Carlo Bot</div>
  <h1>Simulated future price paths</h1>
  <p class="lede">Geometric Brownian Motion simulation using each stock's own historical drift and volatility
  (trailing 252 trading days). This is a standard illustrative technique, not a forecast — GBM assumes
  constant volatility and log-normal returns, so it misses fat tails, jumps, and regime changes. Read the
  spread of outcomes, not any single path.</p>
</header>

<section>
  <div class="card">
    <div style="display:flex;gap:16px;flex-wrap:wrap;align-items:flex-end;margin-bottom:14px;">
      <div>
        <label style="display:block;font-size:11px;color:var(--ink-muted);margin-bottom:4px;">Stock (defaulting to {default_note})</label>
        <select id="mc-ticker" style="padding:7px 10px;border-radius:6px;border:1px solid var(--border);background:var(--card);color:var(--ink-1);font-family:inherit;min-width:220px;">
          {options_html}
        </select>
      </div>
      <div>
        <label style="display:block;font-size:11px;color:var(--ink-muted);margin-bottom:4px;">Horizon (trading days)</label>
        <select id="mc-horizon" style="padding:7px 10px;border-radius:6px;border:1px solid var(--border);background:var(--card);color:var(--ink-1);font-family:inherit;">
          <option value="10">10 (~2 weeks)</option>
          <option value="21" selected>21 (~1 month)</option>
          <option value="63">63 (~3 months)</option>
          <option value="126">126 (~6 months)</option>
        </select>
      </div>
      <div>
        <label style="display:block;font-size:11px;color:var(--ink-muted);margin-bottom:4px;">Simulations</label>
        <select id="mc-nsims" style="padding:7px 10px;border-radius:6px;border:1px solid var(--border);background:var(--card);color:var(--ink-1);font-family:inherit;">
          <option value="200">200</option>
          <option value="500" selected>500</option>
          <option value="2000">2000</option>
        </select>
      </div>
      <button id="mc-reroll" style="padding:8px 16px;border-radius:6px;border:1px solid var(--border);background:var(--series-1);color:white;font-weight:600;font-size:13px;cursor:pointer;">Re-roll</button>
    </div>

    <div class="legend">
      <div class="legend-item"><span class="legend-swatch" style="background:var(--series-1)"></span>Median path</div>
      <div class="legend-item"><span class="legend-swatch" style="background:var(--series-3);opacity:.5"></span>25th&ndash;75th percentile band</div>
      <div class="legend-item"><span class="legend-swatch" style="background:var(--ink-muted);opacity:.3"></span>Individual simulated paths</div>
    </div>
    <div class="chart-wrap"><svg id="chart-mc" style="width:100%;height:auto;"></svg></div>
  </div>
</section>

<section>
  <div class="kpi-row" id="mc-stats">
    {kpi("Current price", "&mdash;", "", "mc-current")}
    {kpi("Median simulated price", "&mdash;", "", "mc-median")}
    {kpi("5th&ndash;95th percentile range", "&mdash;", "", "mc-range")}
    {kpi("P(price higher at horizon)", "&mdash;", "", "mc-prob-up")}
    {kpi("Annualized volatility used", "&mdash;", "", "mc-vol")}
  </div>
</section>

<section>
  <h2>Terminal price distribution</h2>
  <p class="lede">Where simulated prices actually land at the end of the horizon &mdash; the shape here is more intuitive to read as "probability" than the cone above.</p>
  <div class="chart-card">
    <div class="chart-wrap"><svg id="chart-hist" style="width:100%;height:auto;"></svg></div>
  </div>
</section>

<section>
  <h2>Risk metrics from the same simulation</h2>
  <div class="kpi-row">
    {kpi("95% Value at Risk", "&mdash;", "neg", "mc-var95")}
    {kpi("95% Expected Shortfall", "&mdash;", "neg", "mc-cvar95")}
    {kpi("Median max drawdown", "&mdash;", "", "mc-maxdd-median")}
    {kpi("P(touches +10% anytime)", "&mdash;", "pos", "mc-touch-up")}
    {kpi("P(touches -10% anytime)", "&mdash;", "neg", "mc-touch-down")}
  </div>
  <p class="lede" style="margin-top:10px;">VaR/Expected Shortfall describe the ending-price distribution. Touch probabilities are different and usually larger &mdash;
  they ask whether price crosses a threshold <em>at any point</em> during the horizon, which is what actually matters for a stop-loss, not just where it ends up.</p>
</section>

<section>
  <div class="callout">
    <b>Reading this chart:</b> the drift/volatility come from the stock's own trailing 12-month price history, so a
    stock in a recent downtrend (negative drift) will show a cone skewed downward &mdash; that's the model reflecting
    recent history, not a prediction that the trend continues. Wider cones = higher historical volatility. Use this
    to calibrate how much uncertainty is actually normal for a given stock, not as a trade signal on its own.
  </div>
</section>

<script>
const MC_PARAMS = {json.dumps(params)};
const MC_TICKER_INFO = {{ holdings: {json.dumps(holdings)}, picks: {json.dumps(decision_picks)} }};

function boxMuller() {{
  let u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}}

function simulate(ticker, horizonDays, nSims) {{
  const p = MC_PARAMS[ticker];
  const paths = [];
  for (let s = 0; s < nSims; s++) {{
    const path = [p.last_price];
    let price = p.last_price;
    for (let t = 0; t < horizonDays; t++) {{
      const z = boxMuller();
      price = price * Math.exp((p.mu - 0.5 * p.sigma * p.sigma) + p.sigma * z);
      path.push(price);
    }}
    paths.push(path);
  }}
  return paths;
}}

function percentile(arr, p) {{
  const sorted = [...arr].sort((a,b) => a-b);
  const idx = (sorted.length - 1) * p;
  const lo = Math.floor(idx), hi = Math.ceil(idx);
  if (lo === hi) return sorted[lo];
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo);
}}

function drawFanChart(paths, horizonDays) {{
  const svg = document.getElementById('chart-mc');
  const W = 860, H = 360, padL = 60, padR = 16, padT = 16, padB = 28;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
  svg.innerHTML = '';
  const cs = getComputedStyle(document.documentElement);
  const col = n => cs.getPropertyValue(n).trim();
  const ns = 'http://www.w3.org/2000/svg';
  const el = (tag, attrs) => {{ const e = document.createElementNS(ns, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; }};

  const n = horizonDays + 1;
  const bands = {{p5: [], p25: [], p50: [], p75: [], p95: []}};
  for (let t = 0; t < n; t++) {{
    const vals = paths.map(p => p[t]);
    bands.p5.push(percentile(vals, 0.05));
    bands.p25.push(percentile(vals, 0.25));
    bands.p50.push(percentile(vals, 0.50));
    bands.p75.push(percentile(vals, 0.75));
    bands.p95.push(percentile(vals, 0.95));
  }}

  const allVals = [...bands.p5, ...bands.p95];
  const minV = Math.min(...allVals), maxV = Math.max(...allVals);
  const pad = (maxV - minV) * 0.06 || 1;
  const yMin = minV - pad, yMax = maxV + pad;
  const x = i => padL + (i/(n-1)) * plotW;
  const y = v => padT + plotH - ((v - yMin)/(yMax - yMin)) * plotH;

  for (let i=0;i<=4;i++) {{
    const v = yMin + (yMax-yMin)*i/4, gy = y(v);
    svg.appendChild(el('line', {{x1:padL, x2:W-padR, y1:gy, y2:gy, stroke: col('--grid'), 'stroke-width':1}}));
    const t = el('text', {{x: padL-8, y: gy+3, 'text-anchor':'end', fill: col('--ink-muted'), 'font-size':10.5, 'font-family':'IBM Plex Mono, monospace'}});
    t.textContent = '₹' + Math.round(v).toLocaleString('en-IN');
    svg.appendChild(t);
  }}
  svg.appendChild(el('line', {{x1:padL, x2:padL, y1:padT, y2:padT+plotH, stroke: col('--baseline'), 'stroke-width':1}}));
  [0, Math.floor((n-1)/2), n-1].forEach(i => {{
    const t = el('text', {{x: x(i), y: H-8, 'text-anchor': i===0?'start':(i===n-1?'end':'middle'), fill: col('--ink-muted'), 'font-size':10.5, 'font-family':'IBM Plex Mono, monospace'}});
    t.textContent = i === 0 ? 'today' : `+${{i}}d`;
    svg.appendChild(t);
  }});

  // faint individual sample paths (cap at 60 drawn, for visual "spaghetti" without killing perf)
  const sampleCount = Math.min(paths.length, 60);
  for (let s = 0; s < sampleCount; s++) {{
    const pts = paths[s].map((v,i) => `${{x(i)}},${{y(v)}}`).join(' ');
    svg.appendChild(el('polyline', {{points: pts, fill:'none', stroke: col('--ink-muted'), 'stroke-width':1, opacity:0.15}}));
  }}

  // 25-75 band as filled area
  const bandPts = bands.p25.map((v,i) => `${{x(i)}},${{y(v)}}`).join(' ') + ' ' +
                  bands.p75.slice().reverse().map((v,i) => `${{x(n-1-i)}},${{y(v)}}`).join(' ');
  svg.appendChild(el('polygon', {{points: bandPts, fill: col('--series-3'), opacity:0.18}}));

  // p5/p95 boundary lines
  [['p5', '--critical'], ['p95', '--good']].forEach(([key, colorVar]) => {{
    const pts = bands[key].map((v,i) => `${{x(i)}},${{y(v)}}`).join(' ');
    svg.appendChild(el('polyline', {{points: pts, fill:'none', stroke: col(colorVar), 'stroke-width':1.5, 'stroke-dasharray':'3 3', opacity:0.6}}));
  }});

  // median line, emphasized
  const medPts = bands.p50.map((v,i) => `${{x(i)}},${{y(v)}}`).join(' ');
  svg.appendChild(el('polyline', {{points: medPts, fill:'none', stroke: col('--series-1'), 'stroke-width':2.5, 'stroke-linejoin':'round', 'stroke-linecap':'round'}}));

  return bands;
}}

function drawHistogram(finalPrices, currentPrice) {{
  const svg = document.getElementById('chart-hist');
  const W = 860, H = 240, padL = 56, padR = 16, padT = 16, padB = 28;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
  svg.innerHTML = '';
  const cs = getComputedStyle(document.documentElement);
  const col = n => cs.getPropertyValue(n).trim();
  const ns = 'http://www.w3.org/2000/svg';
  const el = (tag, attrs) => {{ const e = document.createElementNS(ns, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; }};

  const nBins = 30;
  const minV = Math.min(...finalPrices), maxV = Math.max(...finalPrices);
  const binW = (maxV - minV) / nBins || 1;
  const bins = new Array(nBins).fill(0);
  finalPrices.forEach(v => {{
    let idx = Math.floor((v - minV) / binW);
    if (idx >= nBins) idx = nBins - 1;
    if (idx < 0) idx = 0;
    bins[idx]++;
  }});
  const maxCount = Math.max(...bins);

  const x = i => padL + (i / nBins) * plotW;
  const y = c => padT + plotH - (c / maxCount) * plotH;
  const barW = plotW / nBins;

  bins.forEach((c, i) => {{
    const binCenter = minV + (i + 0.5) * binW;
    const isAboveCurrent = binCenter >= currentPrice;
    svg.appendChild(el('rect', {{
      x: x(i) + 1, y: y(c), width: Math.max(barW - 2, 1), height: plotH - (y(c) - padT),
      fill: isAboveCurrent ? col('--good') : col('--critical'), opacity: 0.55,
    }}));
  }});

  const curX = padL + ((currentPrice - minV) / (maxV - minV)) * plotW;
  svg.appendChild(el('line', {{x1:curX, x2:curX, y1:padT, y2:padT+plotH, stroke: col('--ink-1'), 'stroke-width':1.5, 'stroke-dasharray':'4 3'}}));
  const lbl = el('text', {{x:curX, y: padT - 4, 'text-anchor':'middle', fill: col('--ink-1'), 'font-size':10.5, 'font-family':'IBM Plex Mono, monospace', 'font-weight':600}});
  lbl.textContent = 'current: ₹' + currentPrice.toFixed(0);
  svg.appendChild(lbl);

  [0, Math.round(nBins/2), nBins].forEach(i => {{
    const v = minV + i * binW;
    const t = el('text', {{x: x(i), y: H-8, 'text-anchor': i===0?'start':(i===nBins?'end':'middle'), fill: col('--ink-muted'), 'font-size':10, 'font-family':'IBM Plex Mono, monospace'}});
    t.textContent = '₹' + Math.round(v).toLocaleString('en-IN');
    svg.appendChild(t);
  }});
}}

function computeRiskMetrics(paths, currentPrice) {{
  const finalPrices = paths.map(p => p[p.length - 1]);
  const finalReturns = finalPrices.map(v => (v / currentPrice - 1) * 100);
  const sortedReturns = [...finalReturns].sort((a,b) => a-b);
  const var95Idx = Math.floor(sortedReturns.length * 0.05);
  const var95 = sortedReturns[var95Idx]; // 5th percentile return = 95% VaR (as a loss, negative number)
  const tailLosses = sortedReturns.slice(0, var95Idx + 1);
  const cvar95 = tailLosses.reduce((a,b) => a+b, 0) / tailLosses.length;

  const maxDrawdowns = paths.map(path => {{
    let peak = path[0], maxDD = 0;
    for (const v of path) {{
      if (v > peak) peak = v;
      const dd = (v / peak - 1) * 100;
      if (dd < maxDD) maxDD = dd;
    }}
    return maxDD;
  }});
  const medianMaxDD = percentile(maxDrawdowns, 0.5);

  const touchUp = paths.filter(path => path.some(v => v >= currentPrice * 1.10)).length / paths.length;
  const touchDown = paths.filter(path => path.some(v => v <= currentPrice * 0.90)).length / paths.length;

  return {{ var95, cvar95, medianMaxDD, touchUp, touchDown, finalPrices }};
}}

function updateStats(ticker, bands, nSims, lastPriceStartOfPaths) {{
  const p = MC_PARAMS[ticker];
  const finalVals = {{p5: bands.p5[bands.p5.length-1], p50: bands.p50[bands.p50.length-1], p95: bands.p95[bands.p95.length-1]}};
  document.getElementById('mc-current').textContent = '₹' + p.last_price.toFixed(2);
  document.getElementById('mc-median').textContent = '₹' + finalVals.p50.toFixed(2);
  document.getElementById('mc-range').textContent = '₹' + finalVals.p5.toFixed(0) + ' – ₹' + finalVals.p95.toFixed(0);
  const annVol = (p.sigma * Math.sqrt(252) * 100).toFixed(1);
  document.getElementById('mc-vol').textContent = annVol + '%';
  const upColor = finalVals.p50 >= p.last_price ? 'var(--good)' : 'var(--critical)';
  document.getElementById('mc-median').style.color = upColor;
}}

function runSimulation() {{
  const ticker = document.getElementById('mc-ticker').value;
  const horizon = parseInt(document.getElementById('mc-horizon').value);
  const nSims = parseInt(document.getElementById('mc-nsims').value);
  const currentPrice = MC_PARAMS[ticker].last_price;
  const paths = simulate(ticker, horizon, nSims);
  const bands = drawFanChart(paths, horizon);

  const finalPrices = paths.map(p => p[p.length-1]);
  const pUp = finalPrices.filter(v => v > currentPrice).length / finalPrices.length;
  document.getElementById('mc-prob-up').textContent = (pUp*100).toFixed(1) + '%';
  updateStats(ticker, bands, nSims);

  drawHistogram(finalPrices, currentPrice);
  const risk = computeRiskMetrics(paths, currentPrice);
  document.getElementById('mc-var95').textContent = risk.var95.toFixed(1) + '%';
  document.getElementById('mc-cvar95').textContent = risk.cvar95.toFixed(1) + '%';
  document.getElementById('mc-maxdd-median').textContent = risk.medianMaxDD.toFixed(1) + '%';
  document.getElementById('mc-touch-up').textContent = (risk.touchUp*100).toFixed(1) + '%';
  document.getElementById('mc-touch-down').textContent = (risk.touchDown*100).toFixed(1) + '%';
}}

document.getElementById('mc-ticker').addEventListener('change', runSimulation);
document.getElementById('mc-horizon').addEventListener('change', runSimulation);
document.getElementById('mc-nsims').addEventListener('change', runSimulation);
document.getElementById('mc-reroll').addEventListener('click', runSimulation);
runSimulation();
</script>
"""
    write_page("montecarlo.html", page_shell("Monte Carlo Simulation", "montecarlo.html", body, bots.get("generated_at", "")[:16].replace("T"," ")))


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
    generate_montecarlo(ledger, bots)
    generate_backtest()
    print(f"Site generated in {DOCS}")


if __name__ == "__main__":
    main()
