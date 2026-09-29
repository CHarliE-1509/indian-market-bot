"""Shared CSS/nav/components for the GitHub Pages site. Same palette/fonts as
the backtest dashboard artifact, for visual consistency across everything
this project produces."""

NAV_ITEMS = [
    ("index.html", "Overview"),
    ("manager.html", "Manager"),
    ("quant.html", "Quant"),
    ("technical.html", "Technical"),
    ("sentiment.html", "Sentiment"),
    ("montecarlo.html", "Monte Carlo"),
    ("backtest.html", "Backtest"),
    ("teamb.html", "Team B"),
]

CSS = r"""
<style>
:root {
  color-scheme: light;
  --surface-1:   #fcfcfb; --page: #f9f9f7; --card: #ffffff;
  --ink-1: #0b0b0b; --ink-2: #52514e; --ink-muted: #898781;
  --grid: #e1e0d9; --baseline: #c3c2b7; --border: rgba(11,11,11,0.10);
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a; --series-4: #eda100; --series-5: #4a3aa7;
  --good: #0ca30c; --warning: #b5790a; --critical: #d03b3b;
  --good-bg: #eaf7ea; --warning-bg: #fbf1de; --critical-bg: #fbebea;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --surface-1: #1a1a19; --page: #0d0d0d; --card: #202020;
    --ink-1: #ffffff; --ink-2: #c3c2b7; --ink-muted: #898781;
    --grid: #2c2c2a; --baseline: #383835; --border: rgba(255,255,255,0.10);
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-4: #c98500; --series-5: #9085e9;
    --good: #0ca30c; --warning: #d99a1f; --critical: #e66767;
    --good-bg: #10230f; --warning-bg: #2a2010; --critical-bg: #2a1412;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --surface-1: #1a1a19; --page: #0d0d0d; --card: #202020;
  --ink-1: #ffffff; --ink-2: #c3c2b7; --ink-muted: #898781;
  --grid: #2c2c2a; --baseline: #383835; --border: rgba(255,255,255,0.10);
  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-4: #c98500; --series-5: #9085e9;
  --good: #0ca30c; --warning: #d99a1f; --critical: #e66767;
  --good-bg: #10230f; --warning-bg: #2a2010; --critical-bg: #2a1412;
}
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--page); }
body {
  font-family: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  color: var(--ink-1); padding-bottom: 60px;
}
.num { font-family: "IBM Plex Mono", ui-monospace, monospace; }
a { color: var(--series-1); }
.wrap { max-width: 1000px; margin: 0 auto; padding: 0 20px; }

nav.topnav {
  background: var(--card); border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 10;
}
nav.topnav .wrap { display: flex; align-items: center; gap: 4px; padding: 12px 20px; flex-wrap: wrap; }
nav.topnav .brand { font-weight: 700; margin-right: 16px; font-size: 14px; }
nav.topnav a.navlink {
  color: var(--ink-2); text-decoration: none; font-size: 13px; padding: 6px 12px;
  border-radius: 6px; font-weight: 500;
}
nav.topnav a.navlink:hover { background: var(--grid); }
nav.topnav a.navlink.active { background: var(--series-1); color: white; }
.updated-badge { margin-left: auto; font-size: 11px; color: var(--ink-muted); }

header.page-head { padding: 28px 0 8px; }
.eyebrow { font-size: 12px; letter-spacing: 0.07em; text-transform: uppercase; color: var(--ink-muted); font-weight: 600; margin-bottom: 6px; }
h1 { font-size: 24px; font-weight: 700; margin: 0 0 6px; letter-spacing: -0.01em; }
p.lede { color: var(--ink-2); font-size: 14px; line-height: 1.6; max-width: 68ch; }

section { margin: 28px 0; }
h2 { font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink-muted);
     font-weight: 600; margin: 0 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
h3 { font-size: 15px; font-weight: 600; margin: 0 0 8px; }

.kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
.kpi { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }
.kpi .label { font-size: 11px; color: var(--ink-muted); margin-bottom: 5px; }
.kpi .value { font-size: 19px; font-weight: 600; font-family: "IBM Plex Mono", monospace; }
.kpi .value.pos { color: var(--good); } .kpi .value.neg { color: var(--critical); }

.card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px; }

table { width: 100%; border-collapse: collapse; font-size: 12.5px; color: inherit; }
table, tbody, tr, th, td { color: inherit; }
th, td { text-align: right; padding: 8px 10px; border-bottom: 1px solid var(--border); }
th:first-child, td:first-child { text-align: left; }
th { color: var(--ink-muted); font-weight: 600; font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.03em; }
td { font-family: "IBM Plex Mono", monospace; }
td:first-child { font-family: "IBM Plex Sans", sans-serif; color: var(--ink-1); }
.table-scroll { overflow-x: auto; }

.chip { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 10.5px; font-family: "IBM Plex Sans", sans-serif; font-weight: 600; }
.chip.good { background: var(--good-bg); color: var(--good); }
.chip.warning { background: var(--warning-bg); color: var(--warning); }
.chip.critical { background: var(--critical-bg); color: var(--critical); }
.chip.neutral { background: var(--grid); color: var(--ink-2); }

.callout { background: var(--warning-bg); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; font-size: 13px; line-height: 1.6; }
.callout.info { background: var(--card); border-left: 3px solid var(--series-1); }

.headline-item { padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
.headline-item:last-child { border-bottom: none; }
.headline-item .src { color: var(--ink-muted); font-size: 11px; }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 700px) { .grid-2 { grid-template-columns: 1fr; } }

footer.site-footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border); font-size: 11.5px; color: var(--ink-muted); }
</style>
"""


def render_nav(active_page, updated_at=""):
    links = "".join(
        f'<a class="navlink{" active" if href == active_page else ""}" href="{href}">{label}</a>'
        for href, label in NAV_ITEMS
    )
    badge = f'<span class="updated-badge">Updated {updated_at}</span>' if updated_at else ""
    return f'''<nav class="topnav"><div class="wrap">
      <span class="brand">NSE Bot</span>{links}{badge}
    </div></nav>'''


def page_shell(title, active_page, body_html, updated_at=""):
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
{CSS}
{render_nav(active_page, updated_at)}
<div class="wrap">
{body_html}
<footer class="site-footer">
  Paper-trading bot &mdash; not investment advice. Backtested and live-run on NSE data; see the Backtest page for methodology and honest limitations.
</footer>
</div>
"""


def kpi(label, value, cls="", value_id=""):
    id_attr = f' id="{value_id}"' if value_id else ""
    return f'<div class="kpi"><div class="label">{label}</div><div class="value {cls}"{id_attr}>{value}</div></div>'


def chip(label, kind):
    return f'<span class="chip {kind}">{label}</span>'


CHART_JS = r"""
<script>
function fmtRsJS(v) {
  v = Math.round(v);
  if (Math.abs(v) >= 100000) return '₹' + (v/100000).toFixed(2) + 'L';
  if (Math.abs(v) >= 1000) return '₹' + (v/1000).toFixed(1) + 'K';
  return '₹' + v;
}
function drawMultiLine(svgEl, ttEl, dates, series, opts) {
  opts = opts || {};
  const W = 860, H = opts.h || 300, padL = 56, padR = 16, padT = 16, padB = 28;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  svgEl.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svgEl.innerHTML = '';
  const cs = getComputedStyle(document.documentElement);
  const col = (n) => cs.getPropertyValue(n).trim();

  const allVals = series.flatMap(s => s.values);
  const minV = Math.min(...allVals), maxV = Math.max(...allVals);
  const pad = (maxV - minV) * 0.08 || 1;
  const yMin = minV - pad, yMax = maxV + pad;
  const n = dates.length;
  const x = i => padL + (i/(n-1)) * plotW;
  const y = v => padT + plotH - ((v - yMin)/(yMax - yMin)) * plotH;
  const ns = 'http://www.w3.org/2000/svg';
  const el = (tag, attrs) => { const e = document.createElementNS(ns, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };

  for (let i=0;i<=4;i++) {
    const v = yMin + (yMax-yMin)*i/4, gy = y(v);
    svgEl.appendChild(el('line', {x1:padL, x2:W-padR, y1:gy, y2:gy, stroke: col('--grid'), 'stroke-width':1}));
    const t = el('text', {x: padL-8, y: gy+3, 'text-anchor':'end', fill: col('--ink-muted'), 'font-size':10.5, 'font-family':'IBM Plex Mono, monospace'});
    t.textContent = fmtRsJS(v);
    svgEl.appendChild(t);
  }
  svgEl.appendChild(el('line', {x1:padL, x2:padL, y1:padT, y2:padT+plotH, stroke: col('--baseline'), 'stroke-width':1}));
  [0, Math.floor((n-1)/2), n-1].forEach(i => {
    const t = el('text', {x: x(i), y: H-8, 'text-anchor': i===0?'start':(i===n-1?'end':'middle'), fill: col('--ink-muted'), 'font-size':10.5, 'font-family':'IBM Plex Mono, monospace'});
    t.textContent = dates[i];
    svgEl.appendChild(t);
  });
  series.forEach(s => {
    const pts = s.values.map((v,i) => `${x(i)},${y(v)}`).join(' ');
    svgEl.appendChild(el('polyline', {points: pts, fill:'none', stroke: s.color, 'stroke-width':2, 'stroke-linejoin':'round', 'stroke-linecap':'round'}));
    const li = n-1;
    svgEl.appendChild(el('circle', {cx: x(li), cy: y(s.values[li]), r:4, fill: s.color, stroke: col('--card'), 'stroke-width':2}));
  });
  if (ttEl) {
    const chx = el('line', {x1:padL, x2:padL, y1:padT, y2:padT+plotH, stroke: col('--ink-muted'), 'stroke-width':1, 'stroke-dasharray':'2 2', opacity:0});
    svgEl.appendChild(chx);
    const hitRect = el('rect', {x:padL, y:padT, width:plotW, height:plotH, fill:'transparent'});
    svgEl.appendChild(hitRect);
    hitRect.addEventListener('pointermove', (evt) => {
      const rect = svgEl.getBoundingClientRect();
      const scale = W / rect.width;
      const mx = (evt.clientX - rect.left) * scale;
      let i = Math.round(((mx - padL) / plotW) * (n-1));
      i = Math.max(0, Math.min(n-1, i));
      chx.setAttribute('x1', x(i)); chx.setAttribute('x2', x(i)); chx.style.opacity = 1;
      let rows = series.map(s => `<div style="display:flex;gap:10px;justify-content:space-between;"><span style="opacity:.8"><span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:${s.color};margin-right:6px;"></span>${s.label}</span><strong>${fmtRsJS(s.values[i])}</strong></div>`).join('');
      ttEl.innerHTML = `<div style="margin-bottom:4px;opacity:.7">${dates[i]}</div>${rows}`;
      ttEl.style.opacity = 1;
      const ttx = Math.min(Math.max((x(i)/W)*rect.width - 70, 0), rect.width - 160);
      ttEl.style.left = ttx + 'px'; ttEl.style.top = '4px';
    });
    hitRect.addEventListener('pointerleave', () => { ttEl.style.opacity = 0; chx.style.opacity = 0; });
  }
}
</script>
<style>
.chart-card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px 16px 8px; position: relative; }
.chart-wrap { position: relative; }
.tooltip { position: absolute; pointer-events: none; background: var(--ink-1); color: var(--page);
  font-family: "IBM Plex Mono", monospace; font-size: 11px; padding: 7px 9px; border-radius: 6px;
  line-height: 1.5; opacity: 0; transition: opacity .1s; white-space: nowrap; z-index: 5; }
.legend { display:flex; gap:14px; font-size:11.5px; color:var(--ink-2); flex-wrap:wrap; margin-bottom:6px; }
.legend-item { display:flex; align-items:center; gap:5px; }
.legend-swatch { width:12px; height:2px; display:inline-block; border-radius:1px; }
</style>
"""


def fmt_rs(v):
    v = round(v)
    if abs(v) >= 100000:
        return f"₹{v/100000:.2f}L"
    if abs(v) >= 1000:
        return f"₹{v/1000:.1f}K"
    return f"₹{v}"
