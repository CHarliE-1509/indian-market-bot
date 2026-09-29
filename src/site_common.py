"""Shared CSS/nav/components for the GitHub Pages site — MANGrove, neon/dark theme.

Design: committed dark-only theme (neon doesn't read on a light ground) — true
near-black base, electric purple as the primary brand/action color, with
orange/red/lime doing semantic duty (warning/critical/good) rather than all
four colors competing decoratively. Glow is used sparingly, on focal elements
only (active nav, primary buttons) — everything glowing at once reads as
noise, not as a polished high-contrast interface. Orbitron (geometric,
sci-fi-adjacent display face) for the wordmark/headlines; IBM Plex Sans/Mono
stay for body/data since legibility matters more there than mood.

Chart series colors (--series-1..5) are UNCHANGED from the original
CVD-validated palette — only UI chrome uses the new neon system. Never
reassign the series tokens without re-validating adjacent-pair CVD safety.
"""

NAV_GROUPS = [
    ("Overview", [("index.html", "Overview", "grid")]),
    ("Analysis Bots", [
        ("manager.html", "Manager", "sitemap"),
        ("quant.html", "Quant", "bars"),
        ("technical.html", "Technical", "pulse"),
        ("sentiment.html", "Sentiment", "chat"),
    ]),
    ("Simulation", [("montecarlo.html", "Monte Carlo", "dice")]),
    ("Research", [
        ("backtest.html", "Backtest", "flask"),
        ("teamb.html", "Team B", "branch"),
    ]),
]

_ICONS = {
    "grid": '<rect x="2.5" y="2.5" width="6" height="6" rx="1.3"/><rect x="11.5" y="2.5" width="6" height="6" rx="1.3"/><rect x="2.5" y="11.5" width="6" height="6" rx="1.3"/><rect x="11.5" y="11.5" width="6" height="6" rx="1.3"/>',
    "sitemap": '<circle cx="10" cy="3.6" r="1.9"/><circle cx="3.8" cy="16.4" r="1.9"/><circle cx="16.2" cy="16.4" r="1.9"/><path d="M10 5.5v3.5M10 9l-6.2 5.5M10 9l6.2 5.5"/>',
    "bars": '<rect x="2.5" y="11" width="3.4" height="6.5" rx="0.6"/><rect x="8.3" y="6.5" width="3.4" height="11" rx="0.6"/><rect x="14.1" y="2.5" width="3.4" height="15" rx="0.6"/>',
    "pulse": '<polyline points="2,10.5 5.5,10.5 7.5,4 11,16.5 13,10.5 17.5,10.5"/>',
    "chat": '<path d="M3 4.5h14a1 1 0 011 1v7a1 1 0 01-1 1H9l-4 3.5v-3.5H3a1 1 0 01-1-1v-7a1 1 0 011-1z"/>',
    "dice": '<rect x="2.5" y="2.5" width="15" height="15" rx="3"/><circle cx="6.8" cy="6.8" r="1.15" fill="currentColor" stroke="none"/><circle cx="13.2" cy="6.8" r="1.15" fill="currentColor" stroke="none"/><circle cx="10" cy="10" r="1.15" fill="currentColor" stroke="none"/><circle cx="6.8" cy="13.2" r="1.15" fill="currentColor" stroke="none"/><circle cx="13.2" cy="13.2" r="1.15" fill="currentColor" stroke="none"/>',
    "flask": '<path d="M8 2.5h4M8.7 2.5v5.3l-4.4 7.6A1.4 1.4 0 005.5 17.5h9a1.4 1.4 0 001.2-2.1l-4.4-7.6V2.5"/><path d="M6.3 12.5h7.4"/>',
    "branch": '<circle cx="5.5" cy="4.5" r="1.9"/><circle cx="5.5" cy="15.5" r="1.9"/><circle cx="15" cy="10" r="1.9"/><path d="M5.5 6.4v7.2M7.3 10H13"/>',
}


def _icon_svg(name, size=17):
    inner = _ICONS.get(name, "")
    return (f'<svg class="nav-icon" width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" '
            f'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>')


# Original abstract mark: an angular circuit-tree hybrid — a geometric canopy
# (diamond) with a vertical trunk trace and two angled root/branch traces,
# echoing a circuit-board trace rather than an organic tree silhouette.
LOGO_SVG = '''<svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true" style="filter: drop-shadow(0 0 4px var(--brand));">
  <path d="M16 3 L25 12 L16 21 L7 12 Z" fill="none" stroke="var(--brand)" stroke-width="2" stroke-linejoin="round"/>
  <circle cx="16" cy="12" r="2.1" fill="var(--brand)"/>
  <path d="M16 21 L16 29 M16 24 L9 29 M16 24 L23 29" stroke="var(--brand)" stroke-width="2" fill="none" stroke-linecap="round"/>
  <circle cx="16" cy="29" r="1.3" fill="var(--accent-lime)"/>
  <circle cx="9" cy="29" r="1.3" fill="var(--accent-orange)"/>
  <circle cx="23" cy="29" r="1.3" fill="var(--accent-red)"/>
</svg>'''

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;600;700;800&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
  color-scheme: dark;
  --page: #08070d; --card: #12111c; --card-2: #0d0c16;
  --ink-1: #f1eefc; --ink-2: #b3abd4; --ink-muted: #756e94;
  --grid: #221e35; --baseline: #382f57; --border: rgba(176,38,255,0.16);

  --brand: #b026ff; --brand-strong: #cf5bff; --brand-wash: rgba(176,38,255,0.13);
  --accent-orange: #ff8a1e; --accent-orange-wash: rgba(255,138,30,0.14);
  --accent-red: #ff2d55; --accent-red-wash: rgba(255,45,85,0.14);
  --accent-lime: #c6ff1a; --accent-lime-wash: rgba(198,255,26,0.13);

  --sidebar-bg: #050408; --sidebar-bg-2: #14101e; --sidebar-ink: #8f86ac;
  --sidebar-ink-strong: #f5f2ff; --sidebar-border: rgba(176,38,255,0.18);

  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-4: #c98500; --series-5: #9085e9;

  --good: var(--accent-lime); --warning: var(--accent-orange); --critical: var(--accent-red);
  --good-bg: var(--accent-lime-wash); --warning-bg: var(--accent-orange-wash); --critical-bg: var(--accent-red-wash);
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.35), 0 1px 10px rgba(0,0,0,0.3);
  --glow-brand: 0 0 14px rgba(176,38,255,0.45);
}

* { box-sizing: border-box; }
html, body { margin: 0; background: var(--page); }
body {
  font-family: "IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  color: var(--ink-1);
}
.num { font-family: "IBM Plex Mono", ui-monospace, monospace; font-variant-numeric: tabular-nums; }
a { color: var(--brand); }
.wrap { max-width: 1040px; margin: 0 auto; padding: 0 28px; }

/* ---------- shell layout ---------- */
.app-shell { display: flex; min-height: 100vh; align-items: stretch; }
.sidebar {
  width: 234px; flex-shrink: 0; background: var(--sidebar-bg);
  position: sticky; top: 0; align-self: flex-start; height: 100vh;
  overflow-y: auto; display: flex; flex-direction: column;
  border-right: 1px solid var(--sidebar-border);
}
.content { flex: 1; min-width: 0; padding-bottom: 64px; }

.sidebar-brand {
  display: flex; align-items: center; gap: 9px; padding: 22px 20px 18px;
  border-bottom: 1px solid var(--sidebar-border);
}
.sidebar-brand .wordmark {
  font-family: "Orbitron", system-ui, sans-serif; font-weight: 700; font-size: 17px;
  color: var(--sidebar-ink-strong); letter-spacing: 0.02em; text-shadow: 0 0 10px rgba(176,38,255,0.5);
}

nav.sidenav { padding: 16px 12px; flex: 1; }
.nav-group { margin-bottom: 18px; }
.nav-group-label {
  font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase;
  color: #524a70; font-weight: 600; padding: 0 10px 6px;
}
a.nav-item {
  display: flex; align-items: center; gap: 10px; padding: 8px 10px;
  border-radius: 8px; color: var(--sidebar-ink); text-decoration: none;
  font-size: 13.5px; font-weight: 500; margin-bottom: 1px;
  border-left: 2.5px solid transparent; transition: background 0.12s, color 0.12s, box-shadow 0.12s;
}
a.nav-item .nav-icon { flex-shrink: 0; opacity: 0.8; }
a.nav-item:hover { background: var(--sidebar-bg-2); color: var(--sidebar-ink-strong); }
a.nav-item.active {
  background: var(--sidebar-bg-2); color: var(--sidebar-ink-strong);
  border-left-color: var(--brand); font-weight: 600;
  box-shadow: inset 3px 0 8px -2px rgba(176,38,255,0.4);
}
a.nav-item.active .nav-icon { color: var(--brand); opacity: 1; filter: drop-shadow(0 0 3px var(--brand)); }

.sidebar-foot {
  padding: 14px 20px 18px; border-top: 1px solid var(--sidebar-border);
  font-size: 11px; color: #55507a; line-height: 1.6;
}

.content-topbar {
  display: flex; justify-content: flex-end; align-items: center;
  padding: 14px 28px 0; gap: 10px;
}
.updated-badge {
  font-size: 11.5px; color: var(--ink-muted); display: flex; align-items: center; gap: 6px;
}
.updated-badge .live-dot {
  width: 6px; height: 6px; border-radius: 50%; background: var(--accent-lime); display: inline-block;
  box-shadow: 0 0 6px 1px var(--accent-lime);
}

@media (max-width: 900px) {
  .app-shell { flex-direction: column; }
  .sidebar { width: 100%; height: auto; position: static; }
  .sidebar-brand { padding: 14px 16px; border-bottom: none; }
  nav.sidenav { display: flex; overflow-x: auto; padding: 0 10px 12px; gap: 2px; }
  .nav-group { display: contents; }
  .nav-group-label { display: none; }
  a.nav-item { white-space: nowrap; border-left: none; border-bottom: 2.5px solid transparent; border-radius: 7px 7px 0 0; }
  a.nav-item.active { border-left-color: transparent; border-bottom-color: var(--brand); box-shadow: inset 0 -3px 8px -2px rgba(176,38,255,0.4); }
  .sidebar-foot { display: none; }
  .wrap { padding: 0 18px; }
  .content-topbar { padding: 10px 18px 0; }
}

/* ---------- typography ---------- */
header.page-head { padding: 22px 0 10px; }
.eyebrow { font-size: 11.5px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--brand-strong); font-weight: 700; margin-bottom: 8px; }
h1 { font-family: "Orbitron", system-ui, sans-serif; font-size: 27px; font-weight: 700; margin: 0 0 10px; letter-spacing: 0.005em; text-wrap: balance; }
p.lede { color: var(--ink-2); font-size: 14.5px; line-height: 1.65; max-width: 68ch; }

section { margin: 32px 0; }
h2 {
  font-family: "Orbitron", system-ui, sans-serif; font-size: 13.5px; font-weight: 600; color: var(--ink-1);
  letter-spacing: 0.04em; text-transform: uppercase;
  margin: 0 0 14px; padding-bottom: 10px; border-bottom: 1px solid var(--border);
}
h3 { font-size: 14.5px; font-weight: 600; margin: 0 0 9px; color: var(--ink-1); }

/* ---------- components ---------- */
.kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.kpi {
  background: var(--card); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px; box-shadow: var(--shadow-sm); transition: transform 0.12s, border-color 0.12s;
}
.kpi:hover { transform: translateY(-1px); border-color: var(--brand); }
.kpi .label { font-size: 11px; color: var(--ink-muted); margin-bottom: 6px; font-weight: 500; }
.kpi .value { font-size: 20px; font-weight: 600; font-family: "IBM Plex Mono", monospace; font-variant-numeric: tabular-nums; }
.kpi .value.pos { color: var(--good); } .kpi .value.neg { color: var(--critical); }

.card {
  background: var(--card); border: 1px solid var(--border); border-radius: 10px;
  padding: 18px 20px; box-shadow: var(--shadow-sm);
}

table { width: 100%; border-collapse: collapse; font-size: 12.5px; color: inherit; }
table, tbody, tr, th, td { color: inherit; }
th, td { text-align: right; padding: 9px 11px; border-bottom: 1px solid var(--border); }
th:first-child, td:first-child { text-align: left; }
th { color: var(--ink-muted); font-weight: 600; font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.03em; }
td { font-family: "IBM Plex Mono", monospace; font-variant-numeric: tabular-nums; }
td:first-child { font-family: "IBM Plex Sans", sans-serif; color: var(--ink-1); font-weight: 500; }
tbody tr:nth-child(even) { background: var(--card-2); }
tbody tr:hover { background: var(--brand-wash); }
.table-scroll { overflow-x: auto; border-radius: 8px; }

.chip {
  display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 20px;
  font-size: 10.5px; font-family: "IBM Plex Sans", sans-serif; font-weight: 600; letter-spacing: 0.01em;
}
.chip.good { background: var(--good-bg); color: var(--good); }
.chip.warning { background: var(--warning-bg); color: var(--warning); }
.chip.critical { background: var(--critical-bg); color: var(--critical); }
.chip.neutral { background: var(--grid); color: var(--ink-2); }

.callout { background: var(--warning-bg); border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px; font-size: 13.5px; line-height: 1.65; }
.callout.info { background: var(--brand-wash); border-left: 3px solid var(--brand); border-radius: 4px 10px 10px 4px; }

.headline-item { padding: 9px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
.headline-item:last-child { border-bottom: none; }
.headline-item .src { color: var(--ink-muted); font-size: 11px; }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 700px) { .grid-2 { grid-template-columns: 1fr; } }

button, select {
  font-family: "IBM Plex Sans", sans-serif;
}
select {
  appearance: none; -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%23756e94' stroke-width='1.4' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 10px center; padding-right: 28px !important;
}
.field { display: flex; flex-direction: column; gap: 5px; }
.field label { font-size: 11px; color: var(--ink-muted); font-weight: 500; }
.field-select, select.field-select {
  padding: 8px 30px 8px 12px; border-radius: 8px; border: 1px solid var(--border);
  background-color: var(--card); color: var(--ink-1); font-size: 13px; min-width: 160px;
}
.controls-row { display: flex; gap: 16px; flex-wrap: wrap; align-items: flex-end; margin-bottom: 16px; }
.btn-primary {
  background: var(--brand); color: #fff; border: none; border-radius: 8px;
  padding: 8px 18px; font-weight: 600; font-size: 13px; cursor: pointer;
  transition: background 0.12s, box-shadow 0.12s; box-shadow: var(--glow-brand);
}
.btn-primary:hover { background: var(--brand-strong); box-shadow: 0 0 20px rgba(207,91,255,0.6); }

footer.site-footer { margin-top: 48px; padding-top: 18px; border-top: 1px solid var(--border); font-size: 11.5px; color: var(--ink-muted); }

/* chart chrome — shared by every page that draws a chart, not just ones using CHART_JS's drawMultiLine */
.chart-card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 18px 18px 10px; position: relative; box-shadow: var(--shadow-sm); }
.chart-wrap { position: relative; }
.tooltip { position: absolute; pointer-events: none; background: #050408; color: var(--ink-1); border: 1px solid var(--border);
  font-family: "IBM Plex Mono", monospace; font-size: 11px; padding: 7px 9px; border-radius: 6px;
  line-height: 1.5; opacity: 0; transition: opacity .1s; white-space: nowrap; z-index: 5; }
.legend { display: flex; gap: 14px; font-size: 11.5px; color: var(--ink-2); flex-wrap: wrap; margin-bottom: 8px; }
.legend-item { display: flex; align-items: center; gap: 5px; }
.legend-swatch { width: 12px; height: 2px; display: inline-block; border-radius: 1px; flex-shrink: 0; }
</style>
"""


def render_sidebar(active_page, updated_at=""):
    groups_html = ""
    for group_label, items in NAV_GROUPS:
        links = "".join(
            f'<a class="nav-item{" active" if href == active_page else ""}" href="{href}">'
            f'{_icon_svg(icon)}<span>{label}</span></a>'
            for href, label, icon in items
        )
        groups_html += f'<div class="nav-group"><div class="nav-group-label">{group_label}</div>{links}</div>'

    return f'''<aside class="sidebar">
      <div class="sidebar-brand">{LOGO_SVG}<span class="wordmark">MANGrove</span></div>
      <nav class="sidenav">{groups_html}</nav>
      <div class="sidebar-foot">Regime-adaptive NSE paper trading &mdash; not investment advice.</div>
    </aside>'''


def page_shell(title, active_page, body_html, updated_at=""):
    badge = (f'<span class="updated-badge"><span class="live-dot"></span>Updated {updated_at}</span>'
             if updated_at else "")
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &middot; MANGrove</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{CSS}
<div class="app-shell">
{render_sidebar(active_page, updated_at)}
<main class="content">
  <div class="content-topbar">{badge}</div>
  <div class="wrap">
{body_html}
    <footer class="site-footer">
      MANGrove &mdash; paper-trading research platform, not investment advice. Backtested and live-run on NSE data; see the Backtest page for methodology and honest limitations.
    </footer>
  </div>
</main>
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
"""


def fmt_rs(v):
    v = round(v)
    if abs(v) >= 100000:
        return f"₹{v/100000:.2f}L"
    if abs(v) >= 1000:
        return f"₹{v/1000:.1f}K"
    return f"₹{v}"
