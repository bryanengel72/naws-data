#!/usr/bin/env python3
"""Inject Geography + Funding tabs into index.html (the canonical dashboard).

Idempotent: removes any prior auto-injected blocks before adding fresh ones.
Run after build_geography.py and build_funding.py.
"""
import json
import re
from pathlib import Path

ROOT = Path("/Users/bryanengel/NAWS Data")
HTML = ROOT / "index.html"
GEO = ROOT / "geography_data.json"
FUND = ROOT / "funding_data.json"

TAB_START = "<!-- ═══ EXTRAS TABS (auto) ═══ -->"
TAB_END = "<!-- ═══ /EXTRAS TABS (auto) ═══ -->"
JS_START = "/* ═══ EXTRAS JS (auto) ═══ */"
JS_END = "/* ═══ /EXTRAS JS (auto) ═══ */"
CSS_START = "/* ═══ EXTRAS CSS (auto) ═══ */"
CSS_END = "/* ═══ /EXTRAS CSS (auto) ═══ */"
NAV_START = "<!-- EXTRAS NAV (auto) -->"
NAV_END = "<!-- /EXTRAS NAV (auto) -->"
CDN_TAG = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js" data-extras-auto></script>'

geo_json = json.dumps(json.loads(GEO.read_text()), separators=(",", ":"))
fund_json = json.dumps(json.loads(FUND.read_text()), separators=(",", ":"))

# ----------------------------------------------------------------------
# CSS — combined Geography + Funding tab styles
# ----------------------------------------------------------------------
CSS = f"""{CSS_START}
.x-kpi-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}}
.x-kpi {{
  background: var(--surface, var(--card, #161b22));
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  padding: 1rem 1.2rem;
  position: relative;
  overflow: hidden;
}}
.x-kpi::before {{
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: var(--accent-color, var(--teal));
}}
.x-kpi-label {{ font-size: 0.68rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.07em; }}
.x-kpi-value {{ font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em; margin-top: 4px; color: var(--text); }}
.x-kpi-sub {{ font-size: 0.7rem; color: var(--muted); margin-top: 4px; }}

.x-section-header {{ display:flex; align-items:center; gap:10px; margin: 2rem 0 1rem; }}
.x-section-dot {{ width:8px; height:8px; border-radius:50%; background: var(--teal); }}
.x-section-title {{ font-size: 1.05rem; font-weight: 700; letter-spacing: -0.02em; color: var(--text); }}
.x-section-line {{ flex: 1; height: 1px; background: var(--border, #30363d); }}
.x-section-badge {{
  font-size: 0.7rem; color: var(--muted);
  background: var(--surface2, #21262d); border: 1px solid var(--border, #30363d);
  border-radius: 12px; padding: 3px 10px;
}}

.x-card {{
  background: var(--surface, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  padding: 1.5rem;
}}
.x-card .x-card-title {{ font-size: 0.85rem; font-weight: 600; margin-bottom: 3px; color: var(--text); }}
.x-card .x-card-sub {{ font-size: 0.72rem; color: var(--muted); margin-bottom: 1.25rem; }}

.x-grid-1-2 {{ display: grid; grid-template-columns: 1fr 2fr; gap: 1rem; }}
.x-grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
@media (max-width: 900px) {{
  .x-grid-1-2, .x-grid-2 {{ grid-template-columns: 1fr; }}
}}

.x-table {{ width: 100%; border-collapse: collapse; }}
.x-table th {{
  font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--muted); padding: 8px 12px; text-align: left;
  border-bottom: 1px solid var(--border, #30363d);
  position: sticky; top: 0; background: var(--surface, #161b22);
}}
.x-table th.num, .x-table td.num {{ text-align: right; }}
.x-table td {{
  font-size: 0.8rem; padding: 9px 12px;
  border-bottom: 1px solid var(--border, #30363d);
  color: var(--text);
}}
.x-table tr:last-child td {{ border-bottom: none; }}
.x-table tbody tr:hover td {{ background: var(--surface2, #21262d); cursor: pointer; }}
.x-table tbody tr.selected td {{ background: rgba(26,188,156,0.12); }}
.x-table .zip-cell {{ font-family: 'Menlo','Monaco',monospace; font-size: 0.78rem; color: var(--teal); }}
.x-table .muted {{ color: var(--muted); font-size: 0.72rem; }}
.x-table .mono {{ font-family: 'Menlo','Monaco',monospace; font-size: 0.74rem; }}
.x-table .canceled-row td {{ opacity: 0.55; }}
.x-table .note {{ color: var(--muted); font-size: 0.72rem; font-style: italic; max-width: 320px; }}

.x-scroll {{ max-height: 480px; overflow-y: auto; }}

.x-bar-wrap {{
  display: inline-block; width: 80px; height: 6px;
  background: var(--surface2, #21262d); border-radius: 3px; overflow: hidden;
  vertical-align: middle; margin-right: 6px;
}}
.x-bar {{ height: 100%; background: var(--teal); border-radius: 3px; }}

.x-svc-list {{ list-style: none; padding: 0; margin: 0; }}
.x-svc-list li {{
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0; border-bottom: 1px solid var(--border, #30363d); font-size: 0.78rem;
  color: var(--text);
}}
.x-svc-list li:last-child {{ border-bottom: none; }}
.x-svc-name {{ flex: 1; }}
.x-svc-count {{ width: 60px; text-align: right; color: var(--muted); font-size: 0.72rem; }}
.x-svc-rev {{ width: 90px; text-align: right; font-weight: 600; }}

.x-dup-card {{
  background: var(--surface2, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
}}
.x-dup-name {{ font-weight: 700; font-size: 0.85rem; margin-bottom: 6px; color: var(--amber, #fbbf24); }}
.x-dup-row {{ font-size: 0.74rem; color: var(--muted); padding: 3px 0; font-family: 'Menlo','Monaco',monospace; }}
.x-dup-row .cid {{ color: var(--cyan, #22d3ee); }}
.x-dup-row .active-flag {{ color: var(--green, #4ade80); font-weight: 700; }}

.x-search {{
  width: 100%; padding: 8px 12px; font-size: 0.8rem;
  background: var(--surface2, #21262d); color: var(--text);
  border: 1px solid var(--border, #30363d); border-radius: 8px;
  margin-bottom: 10px;
}}
.x-search:focus {{ outline: none; border-color: var(--teal); }}

.x-detail-empty {{ color: var(--muted); font-size: 0.78rem; padding: 20px; text-align: center; }}

.x-pill {{
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
}}
.x-pill.grant {{ background: rgba(74,222,128,0.15); color: var(--green, #4ade80); }}
.x-pill.donation {{ background: rgba(167,139,250,0.15); color: var(--purple, #a78bfa); }}
.x-pill.cc {{ background: rgba(76,154,255,0.15); color: var(--blue, #4c9aff); }}
.x-pill.cash {{ background: rgba(251,191,36,0.15); color: var(--amber, #fbbf24); }}
.x-pill.check {{ background: rgba(34,211,238,0.15); color: var(--cyan, #22d3ee); }}
.x-pill.other {{ background: rgba(139,148,158,0.15); color: var(--muted); }}
.x-pill.canceled {{ background: rgba(248,113,113,0.15); color: var(--red, #f87171); }}
.x-pill.payment {{ background: rgba(74,222,128,0.15); color: var(--green, #4ade80); }}
.x-pill.refund {{ background: rgba(251,146,60,0.15); color: var(--orange, #fb923c); }}

.x-pair {{
  background: var(--surface2, #21262d);
  border: 1px solid var(--border, #30363d);
  border-left: 3px solid var(--orange, #fb923c);
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 10px;
  font-size: 0.78rem;
  color: var(--text);
}}
.x-pair-header {{ font-weight: 700; margin-bottom: 6px; }}
.x-pair-detail {{ color: var(--muted); font-size: 0.74rem; }}

.x-main {{ padding: 2rem; max-width: 1400px; margin: 0 auto; }}
{CSS_END}"""

# ----------------------------------------------------------------------
# Tab nav buttons
# ----------------------------------------------------------------------
NAV_BUTTONS = (
    f"{NAV_START}"
    """<button class="tab-btn" onclick="switchTab('geography',this)">🗺️ Geography</button>"""
    """<button class="tab-btn" onclick="switchTab('funding',this)">💵 Funding</button>"""
    f"{NAV_END}"
)

# ----------------------------------------------------------------------
# Tab page HTML (Geography + Funding)
# ----------------------------------------------------------------------
TAB_HTML = f"""{TAB_START}
<!-- ══════════════════════════════════════════ GEOGRAPHY -->
<div id="tab-geography" class="tab-page">
<main class="x-main">

  <div class="x-section-header">
    <div class="x-section-dot" style="background:var(--pink,#f472b6);"></div>
    <div class="x-section-title">Geographic Footprint</div>
    <div class="x-section-line"></div>
    <div class="x-section-badge" id="xGeoBadge">2025 + 2026 YTD</div>
  </div>

  <div class="x-kpi-grid">
    <div class="x-kpi" style="--accent-color: var(--teal);">
      <div class="x-kpi-label">Total Clients</div>
      <div class="x-kpi-value" id="xGeoTotalClients">0</div>
      <div class="x-kpi-sub" id="xGeoActiveDormant">Active vs dormant</div>
    </div>
    <div class="x-kpi" style="--accent-color: var(--green,#4ade80);">
      <div class="x-kpi-label">Active Clients</div>
      <div class="x-kpi-value" id="xGeoActiveClients">0</div>
      <div class="x-kpi-sub">With 2025 or 2026 activity</div>
    </div>
    <div class="x-kpi" style="--accent-color: var(--red,#f87171);">
      <div class="x-kpi-label">Dormant Clients</div>
      <div class="x-kpi-value" id="xGeoDormantClients">0</div>
      <div class="x-kpi-sub">No activity 2025–2026</div>
    </div>
    <div class="x-kpi" style="--accent-color: var(--blue,#4c9aff);">
      <div class="x-kpi-label">Zip Codes Served</div>
      <div class="x-kpi-value" id="xGeoZipsServed">0</div>
      <div class="x-kpi-sub" id="xGeoMatchRate"></div>
    </div>
    <div class="x-kpi" style="--accent-color: var(--amber,#fbbf24);">
      <div class="x-kpi-label">Duplicate Groups</div>
      <div class="x-kpi-value" id="xGeoDupGroups">0</div>
      <div class="x-kpi-sub" id="xGeoDupRecords"></div>
    </div>
    <div class="x-kpi" style="--accent-color: var(--purple,#a78bfa);">
      <div class="x-kpi-label">Linked Revenue</div>
      <div class="x-kpi-value" id="xGeoLinkedRev">$0</div>
      <div class="x-kpi-sub" id="xGeoLinkedSub"></div>
    </div>
  </div>

  <div class="x-section-header">
    <div class="x-section-dot" style="background:var(--teal);"></div>
    <div class="x-section-title">Revenue & Volume by Zip Code</div>
    <div class="x-section-line"></div>
    <div class="x-section-badge">Click a row to see service mix</div>
  </div>

  <div class="x-grid-1-2" style="margin-bottom:1rem;">
    <div class="x-card">
      <div class="x-card-title">By State</div>
      <div class="x-card-sub">Aggregate revenue and procedure count</div>
      <table class="x-table">
        <thead><tr><th>State</th><th class="num">Procedures</th><th class="num">Revenue</th></tr></thead>
        <tbody id="xGeoStateBody"></tbody>
      </table>
    </div>
    <div class="x-card">
      <div class="x-card-title">Top 20 Zip Codes by Revenue</div>
      <div class="x-card-sub">Procedures performed for clients in each zip</div>
      <div style="position:relative;height:360px;">
        <canvas id="xGeoZipChart"></canvas>
      </div>
    </div>
  </div>

  <div class="x-grid-2" style="margin-bottom:1rem;">
    <div class="x-card">
      <div class="x-card-title">All Zips (sortable)</div>
      <div class="x-card-sub">Click a row to load service breakdown →</div>
      <input id="xGeoZipSearch" class="x-search" placeholder="Filter by zip or city…" />
      <div class="x-scroll">
        <table class="x-table">
          <thead><tr><th>Zip</th><th>City</th><th>State</th><th class="num">Count</th><th class="num">Revenue</th></tr></thead>
          <tbody id="xGeoZipBody"></tbody>
        </table>
      </div>
    </div>
    <div class="x-card">
      <div class="x-card-title" id="xGeoDetailTitle">Service Mix</div>
      <div class="x-card-sub" id="xGeoDetailSub">Select a zip on the left</div>
      <div id="xGeoDetailBox" class="x-detail-empty">No zip selected.</div>
    </div>
  </div>

  <div class="x-section-header">
    <div class="x-section-dot" style="background:var(--orange,#fb923c);"></div>
    <div class="x-section-title">Top Cities by Revenue</div>
    <div class="x-section-line"></div>
  </div>

  <div class="x-card" style="margin-bottom:1rem;">
    <div class="x-scroll">
      <table class="x-table">
        <thead><tr><th>City</th><th>State</th><th class="num">Procedures</th><th class="num">Revenue</th></tr></thead>
        <tbody id="xGeoCityBody"></tbody>
      </table>
    </div>
  </div>

  <div class="x-section-header">
    <div class="x-section-dot" style="background:var(--amber,#fbbf24);"></div>
    <div class="x-section-title">Data Quality — Duplicate Client Names</div>
    <div class="x-section-line"></div>
    <div class="x-section-badge" id="xGeoDupBadge">Top 30 by group size</div>
  </div>

  <div class="x-card">
    <div class="x-card-sub" style="margin-bottom:1rem;">
      Same name across multiple Client IDs. Active = had 2025/2026 activity.
      A green active flag on multiple records in one group likely means a true duplicate worth merging.
    </div>
    <div class="x-scroll" id="xGeoDupBox"></div>
  </div>

</main>
</div>

<!-- ══════════════════════════════════════════ FUNDING -->
<div id="tab-funding" class="tab-page">
<main class="x-main">

  <div class="x-section-header">
    <div class="x-section-dot" style="background:var(--green,#4ade80);"></div>
    <div class="x-section-title">Funding &amp; Payment Mix</div>
    <div class="x-section-line"></div>
    <div class="x-section-badge" id="xFundPeriod">Q1 2026</div>
  </div>

  <div class="x-kpi-grid">
    <div class="x-kpi" style="--accent-color: var(--teal);">
      <div class="x-kpi-label">Total Collected (Net)</div>
      <div class="x-kpi-value" id="xFundTotalNet">$0</div>
      <div class="x-kpi-sub" id="xFundRowCount">0 transactions</div>
    </div>
    <div class="x-kpi" style="--accent-color: var(--green,#4ade80);">
      <div class="x-kpi-label">Grant Revenue</div>
      <div class="x-kpi-value" id="xFundGrantNet">$0</div>
      <div class="x-kpi-sub">MO Dept Ag Grant 2026</div>
    </div>
    <div class="x-kpi" style="--accent-color: var(--purple,#a78bfa);">
      <div class="x-kpi-label">Donation Revenue</div>
      <div class="x-kpi-value" id="xFundDonationNet">$0</div>
      <div class="x-kpi-sub">Mr. Donation fund</div>
    </div>
    <div class="x-kpi" style="--accent-color: var(--amber,#fbbf24);">
      <div class="x-kpi-label">Subsidized %</div>
      <div class="x-kpi-value" id="xFundSubsidPct">0%</div>
      <div class="x-kpi-sub">Grant + Donation share of total</div>
    </div>
    <div class="x-kpi" style="--accent-color: var(--blue,#4c9aff);">
      <div class="x-kpi-label">Credit Card</div>
      <div class="x-kpi-value" id="xFundCCNet">$0</div>
      <div class="x-kpi-sub" id="xFundCCSub">Visa + MC + Amex + Discover</div>
    </div>
    <div class="x-kpi" style="--accent-color: var(--red,#f87171);">
      <div class="x-kpi-label">Cancel / Re-entry Pairs</div>
      <div class="x-kpi-value" id="xFundPairs">0</div>
      <div class="x-kpi-sub">Adjustments handled (net excludes these)</div>
    </div>
  </div>

  <div class="x-section-header">
    <div class="x-section-dot" style="background:var(--teal);"></div>
    <div class="x-section-title">Net Revenue by Payment Type</div>
    <div class="x-section-line"></div>
    <div class="x-section-badge">Canceled rows excluded</div>
  </div>

  <div class="x-grid-1-2" style="margin-bottom:1rem;">
    <div class="x-card">
      <div class="x-card-title">Payment Type Mix</div>
      <div class="x-card-sub">Share of net revenue</div>
      <div style="position:relative;height:300px;">
        <canvas id="xFundMixChart"></canvas>
      </div>
    </div>
    <div class="x-card">
      <div class="x-card-title">All Payment Types</div>
      <div class="x-card-sub">Sorted by net revenue. Gross = before any cancels/refunds.</div>
      <div class="x-scroll">
        <table class="x-table">
          <thead><tr>
            <th>Type</th><th>Category</th>
            <th class="num">Net $</th><th class="num">Net #</th>
            <th class="num">Canceled</th><th class="num">Refunds</th>
          </tr></thead>
          <tbody id="xFundTypeBody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="x-section-header">
    <div class="x-section-dot" style="background:var(--green,#4ade80);"></div>
    <div class="x-section-title">MO Dept Ag Grant 2026 — Transactions</div>
    <div class="x-section-line"></div>
    <div class="x-section-badge" id="xFundGrantBadge">0 transactions</div>
  </div>

  <div class="x-card" style="margin-bottom:1rem;">
    <div class="x-card-sub" style="margin-bottom:1rem;">
      Net Jan / Feb / Mar: <span id="xFundGrantMonthly" style="font-weight:600;color:var(--text);">—</span>
    </div>
    <div class="x-scroll">
      <table class="x-table">
        <thead><tr>
          <th>Date</th><th>Client</th><th>Patients</th><th>Invoice</th>
          <th class="num">Amount</th><th>Status</th><th>Note</th><th>Staff</th>
        </tr></thead>
        <tbody id="xFundGrantBody"></tbody>
      </table>
    </div>
  </div>

  <div class="x-section-header">
    <div class="x-section-dot" style="background:var(--purple,#a78bfa);"></div>
    <div class="x-section-title">Mr. Donation Fund — Transactions</div>
    <div class="x-section-line"></div>
    <div class="x-section-badge" id="xFundDonationBadge">0 transactions</div>
  </div>

  <div class="x-card" style="margin-bottom:1rem;">
    <div class="x-card-sub" style="margin-bottom:1rem;">
      Net Jan / Feb / Mar: <span id="xFundDonationMonthly" style="font-weight:600;color:var(--text);">—</span>
    </div>
    <div class="x-scroll">
      <table class="x-table">
        <thead><tr>
          <th>Date</th><th>Client</th><th>Patients</th><th>Invoice</th>
          <th class="num">Amount</th><th>Status</th><th>Note</th><th>Staff</th>
        </tr></thead>
        <tbody id="xFundDonationBody"></tbody>
      </table>
    </div>
  </div>

  <div class="x-section-header">
    <div class="x-section-dot" style="background:var(--orange,#fb923c);"></div>
    <div class="x-section-title">Cancel / Re-entry Pairs</div>
    <div class="x-section-line"></div>
    <div class="x-section-badge">Adjustments collapsed in net</div>
  </div>

  <div class="x-card">
    <div class="x-card-sub" style="margin-bottom:1rem;">
      Same invoice + same payment type with a Canceled row and one (or more) kept Payment rows.
      The "Net" KPIs and the totals above already exclude the canceled amounts — these are listed for audit trail.
    </div>
    <div id="xFundPairBox"></div>
  </div>

</main>
</div>
{TAB_END}"""

# ----------------------------------------------------------------------
# JS — Geography + Funding init + data
# ----------------------------------------------------------------------
JS = f"""{JS_START}
const GEO_DATA = {geo_json};
const FUND_DATA = {fund_json};

function xMoney(n) {{ return '$' + Math.round(n).toLocaleString(); }}
function xMoneyShort(n) {{
  if (n >= 1000) return '$' + (n/1000).toFixed(1).replace(/\\.0$/,'') + 'K';
  return '$' + Math.round(n).toLocaleString();
}}

/* ─── GEOGRAPHY ─── */
function initGeography() {{
  const s = GEO_DATA.summary;
  document.getElementById('xGeoTotalClients').textContent = s.totalClients.toLocaleString();
  document.getElementById('xGeoActiveClients').textContent = s.activeClients.toLocaleString();
  document.getElementById('xGeoDormantClients').textContent = s.dormantClients.toLocaleString();
  document.getElementById('xGeoZipsServed').textContent = s.distinctZipsServed.toLocaleString();
  document.getElementById('xGeoDupGroups').textContent = s.duplicateGroups.toLocaleString();
  document.getElementById('xGeoLinkedRev').textContent = xMoney(s.totalRevenue - s.unknownClientRevenue - s.noZipRevenue);

  const activePct = (s.activeClients / s.totalClients * 100).toFixed(1);
  document.getElementById('xGeoActiveDormant').textContent = `${{activePct}}% active`;
  document.getElementById('xGeoDupRecords').textContent = `${{s.duplicateRecords.toLocaleString()}} client records`;
  document.getElementById('xGeoMatchRate').textContent = `${{s.unparsedAddresses}} unparsed addresses`;
  document.getElementById('xGeoLinkedSub').textContent = `${{s.totalLineItems.toLocaleString()}} line items joined`;

  const stateBody = document.getElementById('xGeoStateBody');
  const maxStateRev = Math.max(...GEO_DATA.states.map(r => r.revenue));
  stateBody.innerHTML = GEO_DATA.states.map(r => `
    <tr>
      <td><strong>${{r.state}}</strong></td>
      <td class="num">${{r.count.toLocaleString()}}</td>
      <td class="num">
        <span class="x-bar-wrap"><span class="x-bar" style="width:${{(r.revenue/maxStateRev*100).toFixed(1)}}%"></span></span>
        ${{xMoney(r.revenue)}}
      </td>
    </tr>
  `).join('');

  xRenderZipTable(GEO_DATA.zips);

  const cityBody = document.getElementById('xGeoCityBody');
  cityBody.innerHTML = GEO_DATA.cities.slice(0, 60).map(r => `
    <tr>
      <td><strong>${{r.city}}</strong></td>
      <td class="muted">${{r.state || '?'}}</td>
      <td class="num">${{r.count.toLocaleString()}}</td>
      <td class="num">${{xMoney(r.revenue)}}</td>
    </tr>
  `).join('');

  const top = GEO_DATA.zips.slice(0, 20);
  new Chart(document.getElementById('xGeoZipChart'), {{
    type: 'bar',
    data: {{
      labels: top.map(r => r.zip + ' · ' + r.city),
      datasets: [{{
        label: 'Revenue',
        data: top.map(r => r.revenue),
        backgroundColor: 'rgba(26,188,156,0.7)',
        borderColor: 'rgba(26,188,156,1)',
        borderWidth: 1,
      }}]
    }},
    options: {{
      indexAxis: 'y',
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label: ctx => {{
              const r = top[ctx.dataIndex];
              return [`Revenue: ${{xMoney(r.revenue)}}`, `Procedures: ${{r.count.toLocaleString()}}`];
            }}
          }}
        }}
      }},
      scales: {{
        x: {{ ticks: {{ color: '#8b949e', callback: v => xMoneyShort(v) }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }},
        y: {{ ticks: {{ color: '#8b949e' }}, grid: {{ display: false }} }}
      }}
    }}
  }});

  const dupBox = document.getElementById('xGeoDupBox');
  dupBox.innerHTML = GEO_DATA.duplicates.map(g => {{
    const rows = g.records.map(r =>
      `<div class="x-dup-row"><span class="cid">${{r.clientId}}</span> · ${{r.name}} · ${{r.zip || '----'}} ${{r.city || ''}} ${{r.state || ''}} ${{r.active ? '<span class="active-flag">● ACTIVE</span>' : ''}}</div>`
    ).join('');
    return `<div class="x-dup-card">
      <div class="x-dup-name">${{g.records[0].name}} <span style="font-weight:400;color:var(--muted);font-size:0.72rem;">(${{g.records.length}} records)</span></div>
      ${{rows}}
    </div>`;
  }}).join('');
  document.getElementById('xGeoDupBadge').textContent = `Showing ${{GEO_DATA.duplicates.length}} of ${{s.duplicateGroups}}`;

  document.getElementById('xGeoZipSearch').addEventListener('input', (e) => {{
    const q = e.target.value.trim().toLowerCase();
    if (!q) {{ xRenderZipTable(GEO_DATA.zips); return; }}
    const filt = GEO_DATA.zips.filter(r =>
      r.zip.includes(q) || (r.city || '').toLowerCase().includes(q)
    );
    xRenderZipTable(filt);
  }});
}}

function xRenderZipTable(rows) {{
  const body = document.getElementById('xGeoZipBody');
  body.innerHTML = rows.map(r => `
    <tr onclick="xSelectZip('${{r.zip}}', this)">
      <td class="zip-cell">${{r.zip}}</td>
      <td>${{r.city || '<span class="muted">?</span>'}}</td>
      <td class="muted">${{r.state || '?'}}</td>
      <td class="num">${{r.count.toLocaleString()}}</td>
      <td class="num">${{xMoney(r.revenue)}}</td>
    </tr>
  `).join('');
}}

function xSelectZip(zip, el) {{
  document.querySelectorAll('#xGeoZipBody tr').forEach(t => t.classList.remove('selected'));
  el.classList.add('selected');
  const z = GEO_DATA.zips.find(r => r.zip === zip);
  if (!z) return;
  document.getElementById('xGeoDetailTitle').textContent = `${{z.zip}} · ${{z.city || ''}}, ${{z.state || ''}}`;
  document.getElementById('xGeoDetailSub').textContent = `${{z.count.toLocaleString()}} procedures · ${{xMoney(z.revenue)}} revenue · top 5 services`;
  const box = document.getElementById('xGeoDetailBox');
  box.classList.remove('x-detail-empty');
  if (!z.topServices.length) {{
    box.innerHTML = '<div class="x-detail-empty">No services found.</div>';
    return;
  }}
  box.innerHTML = '<ul class="x-svc-list">' + z.topServices.map(s =>
    `<li>
      <span class="x-svc-name">${{s.name}}</span>
      <span class="x-svc-count">${{s.count}}×</span>
      <span class="x-svc-rev">${{xMoney(s.revenue)}}</span>
    </li>`
  ).join('') + '</ul>';
}}

/* ─── FUNDING ─── */
function initFunding() {{
  const s = FUND_DATA.summary;
  document.getElementById('xFundPeriod').textContent = FUND_DATA.period;
  document.getElementById('xFundTotalNet').textContent = xMoney(s.totalNet);
  document.getElementById('xFundRowCount').textContent = s.totalRows.toLocaleString() + ' transactions';
  document.getElementById('xFundGrantNet').textContent = xMoney(s.grantNet);
  document.getElementById('xFundDonationNet').textContent = xMoney(s.donationNet);
  document.getElementById('xFundSubsidPct').textContent = s.subsidizedPct.toFixed(2) + '%';
  document.getElementById('xFundCCNet').textContent = xMoney(s.creditCard.net_amount);
  document.getElementById('xFundCCSub').textContent = `${{s.creditCard.net_count.toLocaleString()}} transactions`;
  document.getElementById('xFundPairs').textContent = FUND_DATA.cancelPairs.length;

  const body = document.getElementById('xFundTypeBody');
  const maxNet = Math.max(...FUND_DATA.paymentTypes.map(t => t.netAmount));
  body.innerHTML = FUND_DATA.paymentTypes.map(t => {{
    const cat = (t.category || 'other').toLowerCase().replace(' ', '');
    const pillClass = ({{grant:'grant', donation:'donation', creditcard:'cc', cash:'cash', check:'check'}})[cat] || 'other';
    return `<tr>
      <td><strong>${{t.name}}</strong></td>
      <td><span class="x-pill ${{pillClass}}">${{t.category}}</span></td>
      <td class="num">
        <span class="x-bar-wrap"><span class="x-bar" style="width:${{Math.max(2, (t.netAmount/maxNet*100)).toFixed(1)}}%"></span></span>
        ${{xMoney(t.netAmount)}}
      </td>
      <td class="num">${{t.netCount.toLocaleString()}}</td>
      <td class="num muted">${{t.canceledCount ? xMoney(t.canceledAmount) + ' (' + t.canceledCount + ')' : '—'}}</td>
      <td class="num muted">${{t.refundCount ? xMoney(t.refundAmount) + ' (' + t.refundCount + ')' : '—'}}</td>
    </tr>`;
  }}).join('');

  const COLORS = [
    'rgba(76,154,255,0.8)','rgba(251,191,36,0.8)','rgba(167,139,250,0.8)','rgba(34,211,238,0.8)',
    'rgba(74,222,128,0.8)','rgba(248,113,113,0.8)','rgba(251,146,60,0.8)','rgba(244,114,182,0.8)',
    'rgba(139,148,158,0.7)','rgba(26,188,156,0.8)',
  ];
  const mixData = FUND_DATA.paymentTypes.filter(t => t.netAmount > 0);
  new Chart(document.getElementById('xFundMixChart'), {{
    type: 'doughnut',
    data: {{
      labels: mixData.map(t => t.name),
      datasets: [{{
        data: mixData.map(t => t.netAmount),
        backgroundColor: COLORS,
        borderColor: '#0d1117',
        borderWidth: 2,
      }}]
    }},
    options: {{
      maintainAspectRatio: false,
      cutout: '60%',
      plugins: {{
        legend: {{ position: 'right', labels: {{ font: {{ size: 10 }}, color: '#8b949e', boxWidth: 10 }} }},
        tooltip: {{
          callbacks: {{ label: ctx => `${{ctx.label}}: ${{xMoney(ctx.parsed)}}` }}
        }}
      }}
    }}
  }});

  xRenderFundDetail('xFundGrantBody', FUND_DATA.moGrant2026);
  xRenderFundDetail('xFundDonationBody', FUND_DATA.mrDonation);
  document.getElementById('xFundGrantBadge').textContent = `${{FUND_DATA.moGrant2026.length}} transactions`;
  document.getElementById('xFundDonationBadge').textContent = `${{FUND_DATA.mrDonation.length}} transactions`;

  const fmtMonthly = (arr) => arr.map((v, i) => `${{['Jan','Feb','Mar'][i]}} ${{xMoney(v)}}`).join(' · ');
  document.getElementById('xFundGrantMonthly').textContent = fmtMonthly(FUND_DATA.monthly['MO.DEPT AG GRANT 2026']);
  document.getElementById('xFundDonationMonthly').textContent = fmtMonthly(FUND_DATA.monthly['Mr. Donation']);

  const pairBox = document.getElementById('xFundPairBox');
  if (!FUND_DATA.cancelPairs.length) {{
    pairBox.innerHTML = '<div class="muted" style="text-align:center;padding:20px;">No cancel/re-entry pairs detected.</div>';
  }} else {{
    pairBox.innerHTML = FUND_DATA.cancelPairs.map(p => {{
      const cancels = p.canceled.map(c => `${{c.date}} ${{xMoney(c.amount)}}`).join(', ');
      const kept = p.kept.map(c => `${{c.date}} ${{xMoney(c.amount)}}`).join(', ');
      return `<div class="x-pair">
        <div class="x-pair-header">${{p.client}} — Invoice ${{p.invoiceId}} <span class="muted" style="font-weight:400;">· ${{p.paymentType}}</span></div>
        <div class="x-pair-detail">
          <span class="x-pill canceled">Canceled</span> ${{cancels}} &nbsp;→&nbsp;
          <span class="x-pill payment">Kept</span> ${{kept}}
        </div>
      </div>`;
    }}).join('');
  }}
}}

function xRenderFundDetail(elId, rows) {{
  const body = document.getElementById(elId);
  if (!rows.length) {{
    body.innerHTML = '<tr><td colspan="8" class="muted" style="text-align:center;">No transactions.</td></tr>';
    return;
  }}
  body.innerHTML = rows.map(r => {{
    const isCanceled = r.type === 'Canceled';
    const pillCls = isCanceled ? 'canceled' : r.type === 'Refund' ? 'refund' : 'payment';
    return `<tr class="${{isCanceled ? 'canceled-row' : ''}}">
      <td class="mono">${{r.date}}</td>
      <td>${{r.client}}</td>
      <td class="muted">${{r.patients && r.patients !== '-' ? r.patients : '—'}}</td>
      <td class="mono muted">${{r.invoice && r.invoice !== '-' ? r.invoice : '—'}}</td>
      <td class="num"><strong>${{xMoney(r.amount)}}</strong></td>
      <td><span class="x-pill ${{pillCls}}">${{r.type}}</span></td>
      <td class="note">${{r.note || ''}}</td>
      <td class="muted">${{r.user || ''}}</td>
    </tr>`;
  }}).join('');
}}

/* Both tabs lazy-init via switchTab; mark uninitialized so the dispatcher fires our init.
   The existing dispatcher only knows the original tabs, so we run our init the first
   time the tab is clicked by listening for the click ourselves. */
(function wireExtras() {{
  const tabs = {{ geography: initGeography, funding: initFunding }};
  document.querySelectorAll('.tab-btn').forEach(btn => {{
    const m = (btn.getAttribute('onclick') || '').match(/switchTab\\('([^']+)'/);
    if (!m) return;
    const name = m[1];
    if (tabs[name]) {{
      btn.addEventListener('click', () => {{
        if (!window['__x_init_' + name]) {{
          window['__x_init_' + name] = true;
          // The original switchTab dispatcher will throw because it doesn't know
          // these tabs — but since it's wrapped in setTimeout, we can suppress
          // by marking inited first.
          try {{ inited[name] = true; }} catch (e) {{}}
          setTimeout(() => tabs[name](), 60);
        }}
      }});
    }}
  }});
}})();
{JS_END}"""


# ----------------------------------------------------------------------
# Apply edits
# ----------------------------------------------------------------------
html = HTML.read_text()

# Strip prior auto-injected blocks (idempotent)
for s, e in [(CSS_START, CSS_END), (TAB_START, TAB_END), (JS_START, JS_END),
             (NAV_START, NAV_END)]:
    html = re.sub(re.escape(s) + r".*?" + re.escape(e), "", html, flags=re.DOTALL)

# Strip prior Chart.js CDN if present (idempotent)
html = re.sub(r'<script src="[^"]*chart\.umd\.min\.js" data-extras-auto></script>\s*', "", html)

# 1) Add Chart.js CDN after the existing echarts script
html = re.sub(
    r'(<script src="https://cdn\.jsdelivr\.net/npm/echarts@[^"]+"></script>)',
    r'\1\n' + CDN_TAG,
    html,
    count=1
)

# 2) Add tab nav buttons after the AI Insights button
html = html.replace(
    '<button class="tab-btn" onclick="switchTab(\'ai\',this)">✨ AI Insights</button>',
    '<button class="tab-btn" onclick="switchTab(\'ai\',this)">✨ AI Insights</button>\n  '
    + NAV_BUTTONS,
    1
)

# 3) Insert CSS before </style>
html = html.replace("</style>", CSS + "\n</style>", 1)

# 4) Insert tab HTML before <footer>
html = html.replace("<footer>", TAB_HTML + "\n\n<footer>", 1)

# 5) Insert JS before final </script>
m = re.search(r'(initOverview\(\); inited\.overview=true;\s*)(</script>)', html)
if not m:
    raise SystemExit("Could not find JS injection anchor")
html = html[:m.end(1)] + "\n" + JS + "\n" + html[m.end(1):]

HTML.write_text(html)
print(f"Updated {HTML} -> {len(html):,} bytes")
