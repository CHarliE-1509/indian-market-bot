import json
from pathlib import Path

import pandas as pd

RESULTS = Path(__file__).resolve().parent.parent / "results"
data = json.load(open(RESULTS / "dashboard_data.json"))

YEARS_COVERED = 7.99

single_summary = {r["mode"]: r for r in data["single_asset_summary"]}
mr = single_summary["mean_reversion_only"]
tp = single_summary["trend_pullback_hybrid"]
mom = data["momentum_metrics"]
nifty = data["nifty_bh"]
ew = data["ew_bh"]
rs5000 = data["rs5000_metrics"]

smallcap = pd.read_csv(RESULTS / "smallcap_hybrid_results.csv").sort_values("Sharpe", ascending=False)
basket = json.load(open(RESULTS / "rs5000_basket_summary.json"))
sensitivity = pd.read_csv(RESULTS / "capital_sensitivity.csv")
mc = json.load(open(RESULTS / "monte_carlo_momentum.json"))

wide_top5 = json.load(open(RESULTS / "wide_momentum_top5_metrics.json"))
wide_top8 = json.load(open(RESULTS / "wide_momentum_top8_metrics.json"))
wide_mc = json.load(open(RESULTS / "wide_monte_carlo.json"))
wide_summary = json.load(open(RESULTS / "wide_summary.json"))
wide_sensitivity = pd.read_csv(RESULTS / "wide_capital_sensitivity.csv")

payload = {
    "portfolio_chart": data["portfolio_chart"],
    "rs5000_chart": data["rs5000_chart"],
}

html = r"""<meta charset="utf-8">
<title>NSE Alpha Backtest</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  .viz-root {
    color-scheme: light;
    --surface-1:   #fcfcfb;
    --page:        #f9f9f7;
    --ink-1:       #0b0b0b;
    --ink-2:       #52514e;
    --ink-muted:   #898781;
    --grid:        #e1e0d9;
    --baseline:    #c3c2b7;
    --border:      rgba(11,11,11,0.10);
    --card:        #ffffff;
    --series-1:    #2a78d6; /* momentum */
    --series-2:    #eb6834; /* nifty bh */
    --series-3:    #1baf7a; /* equal-weight bh */
    --good:        #0ca30c;
    --warning:     #b5790a;
    --critical:    #d03b3b;
    --good-bg:     #eaf7ea;
    --warning-bg:  #fbf1de;
    --critical-bg: #fbebea;
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) .viz-root {
      color-scheme: dark;
      --surface-1:   #1a1a19;
      --page:        #0d0d0d;
      --ink-1:       #ffffff;
      --ink-2:       #c3c2b7;
      --ink-muted:   #898781;
      --grid:        #2c2c2a;
      --baseline:    #383835;
      --border:      rgba(255,255,255,0.10);
      --card:        #202020;
      --series-1:    #3987e5;
      --series-2:    #d95926;
      --series-3:    #199e70;
      --good:        #0ca30c;
      --warning:     #d99a1f;
      --critical:    #e66767;
      --good-bg:     #10230f;
      --warning-bg:  #2a2010;
      --critical-bg: #2a1412;
    }
  }
  :root[data-theme="dark"] .viz-root {
    color-scheme: dark;
    --surface-1:   #1a1a19;
    --page:        #0d0d0d;
    --ink-1:       #ffffff;
    --ink-2:       #c3c2b7;
    --ink-muted:   #898781;
    --grid:        #2c2c2a;
    --baseline:    #383835;
    --border:      rgba(255,255,255,0.10);
    --card:        #202020;
    --series-1:    #3987e5;
    --series-2:    #d95926;
    --series-3:    #199e70;
    --good:        #0ca30c;
    --warning:     #d99a1f;
    --critical:    #e66767;
    --good-bg:     #10230f;
    --warning-bg:  #2a2010;
    --critical-bg: #2a1412;
  }

  * { box-sizing: border-box; }
  .viz-root {
    background: var(--page);
    color: var(--ink-1);
    font-family: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
    padding: 40px 20px 80px;
  }
  .wrap { max-width: 900px; margin: 0 auto; }
  .num { font-family: "IBM Plex Mono", ui-monospace, monospace; }

  header.page-head { margin-bottom: 32px; }
  .eyebrow {
    font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ink-muted); font-weight: 600; margin-bottom: 8px;
  }
  h1 { font-size: 28px; font-weight: 700; margin: 0 0 6px; text-wrap: balance; letter-spacing: -0.01em; }
  .subhead { color: var(--ink-2); font-size: 14.5px; max-width: 62ch; line-height: 1.5; }
  .meta-row { display: flex; gap: 20px; margin-top: 16px; flex-wrap: wrap; }
  .meta-item { font-size: 12.5px; color: var(--ink-muted); }
  .meta-item b { color: var(--ink-2); font-weight: 600; }

  section { margin: 40px 0; }
  h2 {
    font-size: 12px; letter-spacing: 0.07em; text-transform: uppercase;
    color: var(--ink-muted); font-weight: 600; margin: 0 0 14px;
    padding-bottom: 8px; border-bottom: 1px solid var(--border);
  }
  h3 { font-size: 17px; font-weight: 600; margin: 0 0 6px; }
  p.lede { color: var(--ink-2); font-size: 14.5px; line-height: 1.6; max-width: 68ch; }

  .verdict {
    background: var(--card); border: 1px solid var(--border); border-radius: 10px;
    padding: 20px 22px; border-left: 3px solid var(--series-1);
  }
  .verdict p { margin: 0 0 10px; font-size: 14.5px; line-height: 1.6; color: var(--ink-2); }
  .verdict p:last-child { margin-bottom: 0; }
  .verdict strong { color: var(--ink-1); }

  .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
  .kpi {
    background: var(--card); border: 1px solid var(--border); border-radius: 10px;
    padding: 14px 16px;
  }
  .kpi .label { font-size: 11.5px; color: var(--ink-muted); margin-bottom: 6px; }
  .kpi .value { font-size: 22px; font-weight: 600; font-family: "IBM Plex Mono", monospace; }
  .kpi .value.pos { color: var(--good); }
  .kpi .value.neg { color: var(--critical); }

  .chart-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 10px;
    padding: 18px 18px 8px;
  }
  .chart-title-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; flex-wrap: wrap; gap: 8px; }
  .chart-title { font-size: 14px; font-weight: 600; }
  .legend { display: flex; gap: 16px; font-size: 12px; color: var(--ink-2); }
  .legend-item { display: flex; align-items: center; gap: 6px; }
  .legend-swatch { width: 14px; height: 2px; border-radius: 1px; display: inline-block; }
  svg text { fill: var(--ink-muted); font-size: 10.5px; font-family: "IBM Plex Mono", monospace; }
  svg .axis-line { stroke: var(--baseline); stroke-width: 1; }
  svg .gridline { stroke: var(--grid); stroke-width: 1; }
  .tooltip {
    position: absolute; pointer-events: none; background: var(--ink-1); color: var(--page);
    font-family: "IBM Plex Mono", monospace; font-size: 11.5px; padding: 8px 10px;
    border-radius: 6px; line-height: 1.6; opacity: 0; transition: opacity 0.1s; white-space: nowrap;
    z-index: 5;
  }
  .tooltip .row { display: flex; gap: 10px; justify-content: space-between; }
  .tooltip .row .k { display: flex; align-items: center; gap: 6px; opacity: 0.85; }
  .tooltip .row .k .dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
  .chart-wrap { position: relative; }
  .crosshair { stroke: var(--ink-muted); stroke-width: 1; stroke-dasharray: 2 2; opacity: 0; }

  table { width: 100%; border-collapse: collapse; font-size: 13px; color: inherit; }
  table, tbody, tr, th, td { color: inherit; }
  th, td { text-align: right; padding: 9px 10px; border-bottom: 1px solid var(--border); }
  th:first-child, td:first-child { text-align: left; }
  th { color: var(--ink-muted); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; }
  td { font-family: "IBM Plex Mono", monospace; }
  td:first-child { font-family: "IBM Plex Sans", sans-serif; color: var(--ink-1); }
  .table-scroll { overflow-x: auto; }
  .chip {
    display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 11px;
    font-family: "IBM Plex Sans", sans-serif; font-weight: 600;
  }
  .chip.good { background: var(--good-bg); color: var(--good); }
  .chip.warning { background: var(--warning-bg); color: var(--warning); }
  .chip.critical { background: var(--critical-bg); color: var(--critical); }
  .chip.neutral { background: var(--grid); color: var(--ink-2); }

  .callout {
    background: var(--warning-bg); border: 1px solid var(--border); border-radius: 10px;
    padding: 16px 18px; font-size: 13.5px; line-height: 1.6; color: var(--ink-1);
  }
  .callout b { color: var(--ink-1); }

  .rules-table td, .rules-table th { text-align: left; }
  .rules-table td:last-child, .rules-table th:last-child { font-family: "IBM Plex Mono", monospace; }

  ol.steps { padding-left: 20px; margin: 0; color: var(--ink-2); font-size: 14px; line-height: 1.9; }
  ol.steps li::marker { color: var(--ink-muted); font-family: "IBM Plex Mono", monospace; }

  footer { margin-top: 48px; padding-top: 16px; border-top: 1px solid var(--border); font-size: 12px; color: var(--ink-muted); }

  @media (max-width: 640px) {
    .kpi-row { grid-template-columns: repeat(2, 1fr); }
  }
</style>

<div class="viz-root">
<div class="wrap">

  <header class="page-head">
    <div class="eyebrow">Backtest report &middot; NSE equities</div>
    <h1>Does a retail algo have alpha on NSE?</h1>
    <p class="subhead">Four rule-based strategies, tested on 19 liquid NIFTY constituents and the index itself, Oct 2018&ndash;Sep 2026, with realistic Indian delivery-trading costs (STT, stamp duty, exchange fees, GST, slippage) baked into every trade.</p>
    <div class="meta-row">
      <div class="meta-item"><b>Period</b> 7.99 years</div>
      <div class="meta-item"><b>Universe</b> 19 stocks + NIFTY 50</div>
      <div class="meta-item"><b>Cost model</b> ~0.38% round trip</div>
      <div class="meta-item"><b>Data</b> Yahoo Finance (.NS), daily bars</div>
    </div>
  </header>

  <section>
    <div class="verdict">
      <p><strong>The honest finding:</strong> single-stock technical rules &mdash; mean-reversion, and even a trend-filtered version of it &mdash; lose money on average, confirmed across both a 19-stock and an 85-stock liquid universe, once real costs are applied. The one strategy with a genuine, non-overfit edge is a <strong>diversified, regime-filtered momentum portfolio</strong> &mdash; and widening the universe to ~85 liquid names makes it materially better: <strong>13.8% CAGR versus NIFTY's 9.5%, at less than half the drawdown</strong> (-15.9% vs -38.4%). That combination &mdash; beating the index on return <em>and</em> risk &mdash; is the actual alpha claim of this build.</p>
      <p><strong>The capital problem:</strong> that edge only appears when spread across ~5 names at once. Rs 5,000 cannot hold 5 positions in liquid stocks &mdash; it holds one. A single-name version of this strategy has no demonstrated edge in this backtest, in either universe. Capital sensitivity testing shows the momentum portfolio holds up from as little as <strong>Rs 25,000</strong> &mdash; that's the realistic floor for accessing the actual edge, not Rs 5,000.</p>
    </div>
  </section>

  <section>
    <h2>Portfolio-level results</h2>
    <div class="kpi-row">
      __KPI_ROWS__
    </div>
  </section>

  <section>
    <div class="chart-card">
      <div class="chart-title-row">
        <div class="chart-title">Growth of Rs 5,00,000 &mdash; monthly rebalance, Oct 2018&ndash;Sep 2026</div>
        <div class="legend" id="legend-portfolio"></div>
      </div>
      <div class="chart-wrap"><svg id="chart-portfolio" viewBox="0 0 860 320" style="width:100%;height:auto;"></svg>
      <div class="tooltip" id="tt-portfolio"></div></div>
    </div>
  </section>

  <section>
    <h2>Why momentum, and not the others</h2>
    <p class="lede">Momentum works here for a specific, explainable reason: the regime filter (only rebalance into names when NIFTY itself is above its 200-day average) sits in cash through the worst drawdowns &mdash; the 2020 crash and the 2022 correction &mdash; that buy-and-hold has to sit through in full. That's the entire source of the edge in this backtest: not better stock-picking, but avoiding the worst months.</p>
    <div class="table-scroll">
      <table>
        <thead><tr><th>Strategy</th><th>CAGR</th><th>Max drawdown</th><th>Sharpe</th><th>Verdict</th></tr></thead>
        <tbody>
          __PORTFOLIO_ROWS__
        </tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>Single-name technical rules (isolated, Rs 5L each, averaged across 19 stocks)</h2>
    <p class="lede">Before recommending momentum, I tested whether simpler single-stock rules had any edge on their own &mdash; the kind of thing most retail "trading bots" actually run. Averaged across the universe, both lose money net of costs.</p>
    <div class="table-scroll">
      <table>
        <thead><tr><th>Strategy</th><th>Avg CAGR</th><th>Avg max DD</th><th>Avg Sharpe</th><th>Trades/yr</th><th>Win rate</th><th>Verdict</th></tr></thead>
        <tbody>
          __SINGLE_ROWS__
        </tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>The Rs 5,000 reality check</h2>
    <p class="lede">Running the trend+pullback hybrid on a single stock, sized to a Rs 5,000 starting balance. <b>__BEST_TICKER__</b> was the best-performing single name <em>in this backtest</em> &mdash; that's hindsight, not a stock-picking signal the strategy actually has. Read this as "what one lucky/skilled single-name pick could look like," not as a forecast.</p>
    <div class="kpi-row" style="grid-template-columns: repeat(3, 1fr); margin-bottom:16px;">
      __RS5000_KPI__
    </div>
    <div class="chart-card">
      <div class="chart-title-row">
        <div class="chart-title">Rs 5,000 &rarr; __RS5000_FINAL__, __BEST_TICKER__ only</div>
      </div>
      <div class="chart-wrap"><svg id="chart-rs5000" viewBox="0 0 860 260" style="width:100%;height:auto;"></svg>
      <div class="tooltip" id="tt-rs5000"></div></div>
    </div>
    <div class="callout" style="margin-top:14px;">
      <b>Why I won't call this a validated strategy yet:</b> one stock, chosen after the fact, is a single sample &mdash; the sample size that proves nothing in backtesting. The only honest use of Rs 5,000 right now is as a <b>paper-trading proof of process</b> (does the execution, risk control and kill-switch logic actually work in real time), not as a capital-growth bet.
    </div>
  </section>

  <section>
    <h2>Does the edge survive a wider universe?</h2>
    <p class="lede">The result above was on 19 large-caps. You asked to widen it before building anything live &mdash; good instinct, since a momentum strategy's edge should get <em>better</em> with more names to rank, not worse. Re-ran everything on ~85 liquid NIFTY 100/150-class stocks across sectors.</p>
    <div class="table-scroll">
      <table>
        <thead><tr><th>Universe</th><th>Top-K</th><th>CAGR</th><th>Max drawdown</th><th>Sharpe</th><th>Chance of breaching 20% DD*</th></tr></thead>
        <tbody>
          <tr><td>19 stocks (original)</td><td>5</td><td>8.33%</td><td>-14.45%</td><td>0.75</td><td>20.9%</td></tr>
          <tr><td>85 stocks (wide)</td><td>5</td><td>__WIDE5_CAGR__%</td><td>__WIDE5_DD__%</td><td>__WIDE5_SHARPE__</td><td>__WIDE_MC_BREACH20__%</td></tr>
          <tr><td>85 stocks (wide)</td><td>8</td><td>__WIDE8_CAGR__%</td><td>__WIDE8_DD__%</td><td>__WIDE8_SHARPE__</td><td>&mdash;</td></tr>
          <tr><td>85 stocks, single name (avg)</td><td>1</td><td>__WIDE_SINGLE_CAGR__%</td><td>__WIDE_SINGLE_DD__%</td><td>__WIDE_SINGLE_SHARPE__</td><td>&mdash;</td></tr>
        </tbody>
      </table>
    </div>
    <p class="lede" style="font-size:12px;">*Monte Carlo bootstrap, 5,000 resamples of the strategy's own monthly returns &mdash; see below.</p>
    <p class="lede">Two things are true at once here, and I don't want to bury the second one under the first: the wide universe is a <strong>better strategy</strong> (higher return, still much lower drawdown than the index) <em>and</em> it is <strong>riskier than the 19-stock version looked</strong> &mdash; the Monte Carlo chance of tripping a 20% kill-switch rises from 20.9% to <strong>__WIDE_MC_BREACH20__%</strong>, and a 25%-drawdown breach happens in __WIDE_MC_BREACH25__% of simulated histories. More names to rank means more dispersion &mdash; that cuts both ways. Single-name technical trading stays unprofitable on average (__WIDE_SINGLE_CAGR__% CAGR) even with 85 names to choose from, confirming this isn't a small-sample artifact.</p>
    <p class="lede"><b>Capital check on the wide universe:</b> holds up just as well down to Rs 25,000 (Sharpe __WIDE25K_SHARPE__ there, actually its best reading) &mdash; so Rs 25,000&ndash;50,000 is a realistic amount to paper-trade this strategy for real, not just a mechanics test.</p>
  </section>

  <section>
    <h2>Follow-up: small caps, a diversified Rs 5,000, and how much capital is enough</h2>
    <p class="lede">Four questions worth testing rather than guessing at.</p>

    <h3 style="margin-top:22px;">a) Does trading volatile small/mid-caps do better?</h3>
    <p class="lede">Same hybrid strategy, 14 high-volatility small/mid-cap names, slippage assumption raised to 0.30%/side (large-cap 0.08% is unrealistic here). No &mdash; average CAGR drops to <b class="num">__SC_AVG_CAGR__%</b>, average Sharpe <b class="num">__SC_AVG_SHARPE__</b>, average drawdown <b class="num">__SC_AVG_DD__%</b>. A couple of names look good in hindsight (NATIONALUM, IDEA); others are how retail accounts actually get wiped out (JPPOWER and RPOWER both drew down &gt;55%, YESBANK is the AT1-writeoff stock). Higher volatility is not the same thing as an edge.</p>
    <div class="table-scroll">
      <table>
        <thead><tr><th>Ticker</th><th>Ann. volatility</th><th>CAGR</th><th>Max DD</th><th>Sharpe</th></tr></thead>
        <tbody>
          __SMALLCAP_ROWS__
        </tbody>
      </table>
    </div>

    <h3 style="margin-top:26px;">b) Rs 5,000 split across 3 cheaper liquid stocks (WIPRO, ITC, KOTAKBANK)</h3>
    <p class="lede">Not cherry-picked &mdash; just the 3 cheapest names in the original 19-stock liquid universe, so this is a fair test of "diversify what little capital you have." Result: <b class="num">Rs 5,000 &rarr; Rs __BASKET_FINAL__</b> (__BASKET_CAGR__% CAGR). Worse than the single-stock hindsight pick, consistent with the honest single-name average above &mdash; spreading Rs 5,000 thinner doesn't create an edge that isn't there.</p>

    <h3 style="margin-top:26px;">c) How much capital does the momentum portfolio actually need?</h3>
    <p class="lede">Tested the one strategy that showed real edge at six capital levels, to see where share-rounding and unaffordable positions (a Rs 25,000 pot can't buy a single share of an 11,000-rupee stock) start to matter.</p>
    <div class="table-scroll">
      <table>
        <thead><tr><th>Capital</th><th>CAGR</th><th>Max DD</th><th>Sharpe</th></tr></thead>
        <tbody>
          __SENSITIVITY_ROWS__
        </tbody>
      </table>
    </div>
    <p class="lede">It holds up better than I expected down to Rs 25,000 &mdash; when a pick is unaffordable the portfolio just runs with fewer names that month rather than breaking. That's a property of <em>this specific 19-stock universe and top-5 rule</em>, not a guarantee; a live version pulling from the full NIFTY 500 would hit pricier stocks more often. Rs 50,000&ndash;1,00,000 is where I'd actually trust it, to leave room for a wider universe.</p>

    <h3 style="margin-top:26px;">d) Monte Carlo: what if market history had shuffled differently?</h3>
    <p class="lede">Everything above, including the dashboard at the top, is <b>one realized historical path</b>. To see the range of outcomes the same underlying edge could have produced under a different sequence of months, I bootstrap-resampled the momentum strategy's 83 monthly returns 5,000 times (i.i.d. resampling &mdash; each simulation reshuffles the same observed monthly returns with replacement).</p>
    <div class="callout" style="background:var(--critical-bg);">
      <b>This is the number that should actually set the kill-switch threshold:</b> in <b>__MC_BREACH_PCT__%</b> of simulated histories, the momentum strategy &mdash; the one with a real edge &mdash; would have breached a 20% drawdown at some point purely from sequencing, not because anything was broken. A kill-switch that halts permanently on first breach would misfire on a working strategy roughly 1 time in 5. CAGR range across simulations: 5th percentile __MC_CAGR_P5__%, median __MC_CAGR_P50__%, 95th percentile __MC_CAGR_P95__%.
    </div>

    <p class="lede" style="margin-top:14px;"><b>On method, since you asked directly:</b> everything above through section (c) is plain historical backtesting &mdash; one realized price path, no model of the data-generating process. Section (d) is the first Monte Carlo step: i.i.d. bootstrap of realized returns, which tests sequencing risk but still assumes the future looks statistically like 2018&ndash;2026. I have <b>not</b> fit a Markov regime-switching model &mdash; the "NIFTY above its 200-day average" filter is a hand-picked 2-state proxy, not an estimated transition matrix between latent market states &mdash; and I have <b>not</b> fit a stochastic volatility process (GARCH) or a mean-reversion process (Ornstein-Uhlenbeck) to set the RSI/ATR thresholds adaptively; they're fixed constants. Kelly criterion hasn't been used either &mdash; every backtest here deploys 100% of available capital into a position with no fractional sizing; a real implementation should size each position at a fraction of Kelly (estimated from the strategy's own win rate and payoff ratio) instead of going all-in. Sharpe ratio is the one criterion actually driving selection so far, and picking the "best Sharpe" stock after the fact (like BHARTIARTL above) is itself a form of in-sample overfitting worth naming, not hiding.</p>
  </section>

  <section>
    <h2>Risk framework &mdash; the literal "or it dies" logic</h2>
    <p class="lede">Turning the incentive into actual enforced rules, independent of the strategy code, so a losing streak can't be argued with:</p>
    <div class="table-scroll">
      <table class="rules-table">
        <thead><tr><th>Trigger</th><th>Action</th></tr></thead>
        <tbody>
          <tr><td>Single position stop hit (2.5&times; ATR from entry)</td><td class="num">Exit immediately, no override</td></tr>
          <tr><td>Daily loss &gt; 5% of current capital</td><td class="num">Halt new entries for the day</td></tr>
          <tr><td>Drawdown &gt; 20% from peak capital</td><td class="num">Halt all trading, flatten, alert</td></tr>
          <tr><td>Price feed stale &gt; 5 minutes during market hours</td><td class="num">Halt new entries, alert</td></tr>
          <tr><td>NIFTY regime filter turns negative</td><td class="num">No new entries; existing positions still exit on their own rules</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>What happens next &mdash; the actual choice</h2>
    <p class="lede">Two genuinely different things could be paper-traded, and they answer different questions:</p>
    <div class="table-scroll">
      <table class="rules-table">
        <thead><tr><th></th><th>Rs 5,000, single stock (scanner picks 1 of ~85)</th><th>Rs 25,000&ndash;50,000, top-5 momentum portfolio</th></tr></thead>
        <tbody>
          <tr><td>What it tests</td><td class="num">Execution &amp; kill-switch mechanics only</td><td class="num">The actual backtested edge</td></tr>
          <tr><td>Backtested CAGR</td><td class="num">-0.67% (loses money on average)</td><td class="num">13.8%, beats NIFTY's 9.5%</td></tr>
          <tr><td>Backtested max drawdown</td><td class="num">-21.3% average</td><td class="num">-15.9% (vs NIFTY's -38.4%)</td></tr>
          <tr><td>Chance of tripping a 20% kill-switch</td><td class="num">not modeled (no edge to model)</td><td class="num">33.1%, per Monte Carlo</td></tr>
        </tbody>
      </table>
    </div>
    <p class="lede">If the goal is proving the bot's plumbing works, Rs 5,000 is fine for that and costs nothing to be wrong about. If the goal is a live trial of something that might actually be worth scaling into real money, it needs to be the Rs 25,000+ momentum portfolio &mdash; a Rs 5,000 single-stock result, good or bad, won't tell you anything the backtest hasn't already shown.</p>
    <ol class="steps">
      <li>Confirm which of the two above to build (or both, run side by side)</li>
      <li>Run it live against delayed (~15 min) market data during NSE hours &mdash; no broker account needed for paper trading</li>
      <li>Log every signal, fill, and kill-switch check to a ledger you can audit</li>
      <li>Only after that track record exists: evaluate a real broker API (Zerodha Kite Connect) and real capital</li>
    </ol>
  </section>

  <footer>
    Backtest code: <span class="num">src/run_all.py</span>, <span class="num">src/backtest_single.py</span>, <span class="num">src/portfolio_momentum.py</span>. Cost assumptions in <span class="num">src/costs.py</span> &mdash; verify current STT/stamp-duty rates against your broker's rate card before trading real capital. Past performance in a backtest is not a forward guarantee.
  </footer>

</div>
</div>

<script id="dashboard-data" type="application/json">__DATA_JSON__</script>
<script>
(function(){
  const DATA = JSON.parse(document.getElementById('dashboard-data').textContent);
  const root = document.querySelector('.viz-root');
  const cs = getComputedStyle(root);
  const col = (name) => cs.getPropertyValue(name).trim();

  function fmtRs(v){
    v = Math.round(v);
    if (Math.abs(v) >= 100000) return '₹' + (v/100000).toFixed(2) + 'L';
    if (Math.abs(v) >= 1000) return '₹' + (v/1000).toFixed(1) + 'K';
    return '₹' + v;
  }

  function drawMultiLine(svgEl, ttEl, dates, series, opts){
    const W = 860, H = opts.h || 320, padL = 56, padR = 16, padT = 16, padB = 28;
    const plotW = W - padL - padR, plotH = H - padT - padB;
    svgEl.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svgEl.innerHTML = '';

    const allVals = series.flatMap(s => s.values);
    const minV = Math.min(...allVals), maxV = Math.max(...allVals);
    const pad = (maxV - minV) * 0.08;
    const yMin = minV - pad, yMax = maxV + pad;
    const n = dates.length;

    const x = i => padL + (i/(n-1)) * plotW;
    const y = v => padT + plotH - ((v - yMin)/(yMax - yMin)) * plotH;

    const ns = 'http://www.w3.org/2000/svg';
    function el(tag, attrs){ const e = document.createElementNS(ns, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; }

    // gridlines (4 horizontal steps)
    const steps = 4;
    for (let i=0;i<=steps;i++){
      const v = yMin + (yMax-yMin)*i/steps;
      const gy = y(v);
      svgEl.appendChild(el('line', {x1:padL, x2:W-padR, y1:gy, y2:gy, class:'gridline'}));
      const t = el('text', {x: padL-8, y: gy+3, 'text-anchor':'end'});
      t.textContent = fmtRs(v);
      svgEl.appendChild(t);
    }
    svgEl.appendChild(el('line', {x1:padL, x2:padL, y1:padT, y2:padT+plotH, class:'axis-line'}));

    // x labels: first, mid, last
    [0, Math.floor((n-1)/2), n-1].forEach(i => {
      const t = el('text', {x: x(i), y: H-8, 'text-anchor': i===0?'start':(i===n-1?'end':'middle')});
      t.textContent = dates[i];
      svgEl.appendChild(t);
    });

    series.forEach(s => {
      const pts = s.values.map((v,i) => `${x(i)},${y(v)}`).join(' ');
      svgEl.appendChild(el('polyline', {points: pts, fill:'none', stroke: s.color, 'stroke-width':2, 'stroke-linejoin':'round', 'stroke-linecap':'round'}));
      const lastI = n-1;
      svgEl.appendChild(el('circle', {cx: x(lastI), cy: y(s.values[lastI]), r:4, fill: s.color, stroke: col('--card'), 'stroke-width':2}));
    });

    const chx = el('line', Object.assign({y1:padT, y2:padT+plotH, class:'crosshair'}, {x1:padL,x2:padL}));
    svgEl.appendChild(chx);

    const hitRect = el('rect', {x:padL, y:padT, width:plotW, height:plotH, fill:'transparent'});
    svgEl.appendChild(hitRect);

    function showTooltip(evt){
      const rect = svgEl.getBoundingClientRect();
      const scale = W / rect.width;
      const mx = (evt.clientX - rect.left) * scale;
      let i = Math.round(((mx - padL) / plotW) * (n-1));
      i = Math.max(0, Math.min(n-1, i));
      chx.setAttribute('x1', x(i)); chx.setAttribute('x2', x(i)); chx.style.opacity = 1;

      let rows = series.map(s => `<div class="row"><span class="k"><span class="dot" style="background:${s.color}"></span>${s.label}</span><strong>${fmtRs(s.values[i])}</strong></div>`).join('');
      ttEl.innerHTML = `<div style="margin-bottom:4px;opacity:.7">${dates[i]}</div>${rows}`;
      ttEl.style.opacity = 1;
      const ttx = Math.min(Math.max((x(i)/W)*rect.width - 70, 0), rect.width - 160);
      ttEl.style.left = ttx + 'px';
      ttEl.style.top = '4px';
    }
    hitRect.addEventListener('pointermove', showTooltip);
    hitRect.addEventListener('pointerleave', () => { ttEl.style.opacity = 0; chx.style.opacity = 0; });
  }

  const pc = DATA.portfolio_chart;
  const portfolioSeries = [
    {label:'Momentum portfolio', values: pc.momentum, color: col('--series-1')},
    {label:'NIFTY 50 (buy & hold)', values: pc.nifty_bh, color: col('--series-2')},
    {label:'Equal-weight universe (buy & hold)', values: pc.equal_weight_bh, color: col('--series-3')},
  ];
  drawMultiLine(document.getElementById('chart-portfolio'), document.getElementById('tt-portfolio'), pc.dates, portfolioSeries, {h:320});
  const legend = document.getElementById('legend-portfolio');
  portfolioSeries.forEach(s => {
    const item = document.createElement('div'); item.className = 'legend-item';
    const sw = document.createElement('span'); sw.className = 'legend-swatch'; sw.style.background = s.color;
    const label = document.createElement('span'); label.textContent = s.label;
    item.appendChild(sw); item.appendChild(label); legend.appendChild(item);
  });

  const rc = DATA.rs5000_chart;
  drawMultiLine(document.getElementById('chart-rs5000'), document.getElementById('tt-rs5000'), rc.dates, [
    {label:'Portfolio value', values: rc.values, color: col('--series-1')}
  ], {h:260});
})();
</script>
"""

def kpi(label, value, positive=None):
    cls = ""
    if positive is True: cls = " pos"
    if positive is False: cls = " neg"
    return f'<div class="kpi"><div class="label">{label}</div><div class="value{cls}">{value}</div></div>'

def chip(label, kind):
    return f'<span class="chip {kind}">{label}</span>'

kpi_rows = "".join([
    kpi("Momentum CAGR", f"{mom['CAGR%']}%", mom['CAGR%'] > 0),
    kpi("Momentum max drawdown", f"{mom['MaxDD%']}%", False),
    kpi("Momentum Sharpe", f"{mom['Sharpe']}", mom['Sharpe'] > nifty['Sharpe']),
    kpi("NIFTY Sharpe (same period)", f"{nifty['Sharpe']}", None),
])

portfolio_rows = "".join([
    f'<tr><td>Momentum portfolio (top-5, regime filter)</td><td>{mom["CAGR%"]}%</td><td>{mom["MaxDD%"]}%</td><td>{mom["Sharpe"]}</td><td>{chip("recommended","good")}</td></tr>',
    f'<tr><td>NIFTY 50 (buy &amp; hold)</td><td>{nifty["CAGR%"]}%</td><td>{nifty["MaxDD%"]}%</td><td>{nifty["Sharpe"]}</td><td>{chip("benchmark","neutral")}</td></tr>',
    f'<tr><td>Equal-weight universe (buy &amp; hold)</td><td>{ew["CAGR%"]}%</td><td>{ew["MaxDD%"]}%</td><td>{ew["Sharpe"]}</td><td>{chip("benchmark","neutral")}</td></tr>',
])

single_rows = "".join([
    f'<tr><td>Mean reversion only (RSI2, no filters)</td><td>{mr["CAGR%"]}%</td><td>{mr["MaxDD%"]}%</td><td>{mr["Sharpe"]}</td><td>{mr["Trades"]/YEARS_COVERED:.1f}</td><td>{mr["WinRate%"]}%</td><td>{chip("not viable","critical")}</td></tr>',
    f'<tr><td>Trend + pullback hybrid, single stock</td><td>{tp["CAGR%"]}%</td><td>{tp["MaxDD%"]}%</td><td>{tp["Sharpe"]}</td><td>{tp["Trades"]/YEARS_COVERED:.1f}</td><td>{tp["WinRate%"]}%</td><td>{chip("not viable alone","warning")}</td></tr>',
])

rs5000_final = f"Rs {rs5000['FinalValue']:,.0f}"
rs5000_kpi = "".join([
    kpi("Final value", rs5000_final, rs5000['FinalValue'] > 5000),
    kpi("CAGR", f"{rs5000['CAGR%']}%", rs5000['CAGR%'] > 0),
    kpi("Max drawdown", f"{rs5000['MaxDD%']}%", False),
])

smallcap_rows = "".join([
    f'<tr><td>{r["ticker"].replace(".NS","")}</td><td>{r["ann_volatility_pct"]}%</td><td>{r["CAGR%"]}%</td><td>{r["MaxDD%"]}%</td><td>{r["Sharpe"]}</td></tr>'
    for _, r in smallcap.iterrows()
])
sensitivity_rows = "".join([
    f'<tr><td>Rs {int(r["capital"]):,}</td><td>{r["CAGR%"]}%</td><td>{r["MaxDD%"]}%</td><td>{r["Sharpe"]}</td></tr>'
    for _, r in sensitivity.iterrows()
])

html = html.replace("__SC_AVG_CAGR__", f"{smallcap['CAGR%'].mean():.2f}")
html = html.replace("__SC_AVG_SHARPE__", f"{smallcap['Sharpe'].mean():.2f}")
html = html.replace("__SC_AVG_DD__", f"{smallcap['MaxDD%'].mean():.2f}")
html = html.replace("__SMALLCAP_ROWS__", smallcap_rows)
html = html.replace("__BASKET_FINAL__", f"{basket['FinalValue']:,.0f}")
html = html.replace("__BASKET_CAGR__", f"{basket['CAGR%']}")
html = html.replace("__SENSITIVITY_ROWS__", sensitivity_rows)
html = html.replace("__MC_BREACH_PCT__", f"{mc['pct_sims_breaching_20pct_dd']}")
html = html.replace("__MC_CAGR_P5__", f"{mc['cagr_p5']}")
html = html.replace("__MC_CAGR_P50__", f"{mc['cagr_p50']}")
html = html.replace("__MC_CAGR_P95__", f"{mc['cagr_p95']}")

wide25k = wide_sensitivity[wide_sensitivity["capital"] == 25000].iloc[0]
html = html.replace("__WIDE5_CAGR__", f"{wide_top5['CAGR%']}")
html = html.replace("__WIDE5_DD__", f"{wide_top5['MaxDD%']}")
html = html.replace("__WIDE5_SHARPE__", f"{wide_top5['Sharpe']}")
html = html.replace("__WIDE8_CAGR__", f"{wide_top8['CAGR%']}")
html = html.replace("__WIDE8_DD__", f"{wide_top8['MaxDD%']}")
html = html.replace("__WIDE8_SHARPE__", f"{wide_top8['Sharpe']}")
html = html.replace("__WIDE_SINGLE_CAGR__", f"{wide_summary['single_asset_avg']['CAGR%']}")
html = html.replace("__WIDE_SINGLE_DD__", f"{wide_summary['single_asset_avg']['MaxDD%']}")
html = html.replace("__WIDE_SINGLE_SHARPE__", f"{wide_summary['single_asset_avg']['Sharpe']}")
html = html.replace("__WIDE_MC_BREACH20__", f"{wide_mc['pct_breach_20']}")
html = html.replace("__WIDE_MC_BREACH25__", f"{wide_mc['pct_breach_25']}")
html = html.replace("__WIDE25K_SHARPE__", f"{wide25k['Sharpe']}")

html = html.replace("__KPI_ROWS__", kpi_rows)
html = html.replace("__PORTFOLIO_ROWS__", portfolio_rows)
html = html.replace("__SINGLE_ROWS__", single_rows)
html = html.replace("__BEST_TICKER__", rs5000["ticker"].replace(".NS",""))
html = html.replace("__RS5000_FINAL__", rs5000_final)
html = html.replace("__RS5000_KPI__", rs5000_kpi)
html = html.replace("__DATA_JSON__", json.dumps(payload))

out_path = RESULTS / "dashboard.html"
out_path.write_text(html)
print(f"Wrote {out_path} ({len(html)} bytes)")
