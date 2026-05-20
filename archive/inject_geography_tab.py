#!/usr/bin/env python3
"""Inject the Geography tab page + JS into naws-dashboard-2025.html.

Idempotent: replaces existing geography block if found, else inserts.
"""
import json
import re
from pathlib import Path

ROOT = Path("/Users/bryanengel/NAWS Data")
HTML = ROOT / "naws-dashboard-2025.html"
DATA = ROOT / "geography_data.json"

START_MARK = "<!-- ═══ GEOGRAPHY (auto) ═══ -->"
END_MARK = "<!-- ═══ /GEOGRAPHY (auto) ═══ -->"
JS_START = "/* ═══ GEOGRAPHY (auto) ═══ */"
JS_END = "/* ═══ /GEOGRAPHY (auto) ═══ */"
CSS_START = "/* ═══ GEOGRAPHY CSS (auto) ═══ */"
CSS_END = "/* ═══ /GEOGRAPHY CSS (auto) ═══ */"

geo_json = json.dumps(json.loads(DATA.read_text()), separators=(",", ":"))

# ----------------------------------------------------------------------
# CSS block
# ----------------------------------------------------------------------
GEO_CSS = f"""{CSS_START}
.geo-kpi-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}}
.geo-kpi {{
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1rem 1.2rem;
  position: relative;
  overflow: hidden;
}}
.geo-kpi::before {{
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: var(--accent-color, var(--teal));
}}
.geo-kpi-label {{ font-size: 0.68rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.07em; }}
.geo-kpi-value {{ font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em; margin-top: 4px; }}
.geo-kpi-sub {{ font-size: 0.7rem; color: var(--muted); margin-top: 4px; }}

.geo-table {{ width: 100%; border-collapse: collapse; }}
.geo-table th {{
  font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--muted); padding: 8px 12px; text-align: left;
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; background: var(--surface);
}}
.geo-table th.num, .geo-table td.num {{ text-align: right; }}
.geo-table td {{
  font-size: 0.8rem; padding: 9px 12px;
  border-bottom: 1px solid var(--border);
}}
.geo-table tbody tr:hover td {{ background: var(--surface2); cursor: pointer; }}
.geo-table tbody tr.selected td {{ background: rgba(26,188,156,0.12); }}
.geo-table tr:last-child td {{ border-bottom: none; }}
.geo-table .zip-cell {{ font-family: 'Menlo','Monaco',monospace; font-size: 0.78rem; color: var(--teal); }}
.geo-table .muted {{ color: var(--muted); font-size: 0.72rem; }}

.geo-scroll {{ max-height: 480px; overflow-y: auto; }}

.svc-list {{ list-style: none; padding: 0; margin: 0; }}
.svc-list li {{
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 0.78rem;
}}
.svc-list li:last-child {{ border-bottom: none; }}
.svc-list .svc-name {{ flex: 1; }}
.svc-list .svc-count {{ width: 60px; text-align: right; color: var(--muted); font-size: 0.72rem; }}
.svc-list .svc-rev {{ width: 90px; text-align: right; font-weight: 600; }}

.dup-card {{
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
}}
.dup-name {{ font-weight: 700; font-size: 0.85rem; margin-bottom: 6px; color: var(--amber); }}
.dup-row {{ font-size: 0.74rem; color: var(--muted); padding: 3px 0; font-family: 'Menlo','Monaco',monospace; }}
.dup-row .cid {{ color: var(--cyan); }}
.dup-row .active-flag {{ color: var(--green); font-weight: 700; }}

.geo-search {{
  width: 100%; padding: 8px 12px; font-size: 0.8rem;
  background: var(--surface2); color: var(--text);
  border: 1px solid var(--border); border-radius: 8px;
  margin-bottom: 10px;
}}
.geo-search:focus {{ outline: none; border-color: var(--teal); }}

.geo-bar-wrap {{
  display: inline-block; width: 80px; height: 6px;
  background: var(--surface2); border-radius: 3px; overflow: hidden;
  vertical-align: middle; margin-right: 6px;
}}
.geo-bar {{ height: 100%; background: var(--teal); border-radius: 3px; }}

.geo-detail-empty {{ color: var(--muted); font-size: 0.78rem; padding: 20px; text-align: center; }}
{CSS_END}"""

# ----------------------------------------------------------------------
# Tab page HTML
# ----------------------------------------------------------------------
GEO_TAB = f"""{START_MARK}
<div id="tab-geography" class="tab-page">
<main>

  <div class="section-header">
    <div class="section-dot" style="background:var(--pink);"></div>
    <div class="section-title">Geographic Footprint</div>
    <div class="section-line"></div>
    <div class="section-badge" id="geoBadge">2025 + 2026 YTD</div>
  </div>

  <div class="geo-kpi-grid">
    <div class="geo-kpi" style="--accent-color: var(--teal);">
      <div class="geo-kpi-label">Total Clients</div>
      <div class="geo-kpi-value" id="geoTotalClients">0</div>
      <div class="geo-kpi-sub" id="geoActiveDormant">Active vs dormant</div>
    </div>
    <div class="geo-kpi" style="--accent-color: var(--green);">
      <div class="geo-kpi-label">Active Clients</div>
      <div class="geo-kpi-value" id="geoActiveClients">0</div>
      <div class="geo-kpi-sub">With 2025 or 2026 activity</div>
    </div>
    <div class="geo-kpi" style="--accent-color: var(--red);">
      <div class="geo-kpi-label">Dormant Clients</div>
      <div class="geo-kpi-value" id="geoDormantClients">0</div>
      <div class="geo-kpi-sub">No activity 2025–2026</div>
    </div>
    <div class="geo-kpi" style="--accent-color: var(--blue);">
      <div class="geo-kpi-label">Zip Codes Served</div>
      <div class="geo-kpi-value" id="geoZipsServed">0</div>
      <div class="geo-kpi-sub" id="geoMatchRate"></div>
    </div>
    <div class="geo-kpi" style="--accent-color: var(--amber);">
      <div class="geo-kpi-label">Duplicate Groups</div>
      <div class="geo-kpi-value" id="geoDupGroups">0</div>
      <div class="geo-kpi-sub" id="geoDupRecords"></div>
    </div>
    <div class="geo-kpi" style="--accent-color: var(--purple);">
      <div class="geo-kpi-label">Linked Revenue</div>
      <div class="geo-kpi-value" id="geoLinkedRev">$0</div>
      <div class="geo-kpi-sub" id="geoLinkedSub"></div>
    </div>
  </div>

  <div class="section-header">
    <div class="section-dot" style="background:var(--teal);"></div>
    <div class="section-title">Revenue & Volume by Zip Code</div>
    <div class="section-line"></div>
    <div class="section-badge">Click a row to see service mix</div>
  </div>

  <div class="grid-1-2" style="margin-bottom:1rem;">
    <div class="chart-card">
      <div class="chart-title">By State</div>
      <div class="chart-subtitle">Aggregate revenue and procedure count</div>
      <table class="geo-table">
        <thead><tr><th>State</th><th class="num">Procedures</th><th class="num">Revenue</th></tr></thead>
        <tbody id="geoStateBody"></tbody>
      </table>
    </div>
    <div class="chart-card">
      <div class="chart-title">Top 20 Zip Codes by Revenue</div>
      <div class="chart-subtitle">Procedures performed for clients in each zip</div>
      <div class="chart-container" style="height:360px;">
        <canvas id="geoZipChart"></canvas>
      </div>
    </div>
  </div>

  <div class="grid-2" style="margin-bottom:1rem;">
    <div class="chart-card">
      <div class="chart-title">All Zips (sortable)</div>
      <div class="chart-subtitle">Click a row to load service breakdown →</div>
      <input id="geoZipSearch" class="geo-search" placeholder="Filter by zip or city…" />
      <div class="geo-scroll">
        <table class="geo-table">
          <thead><tr><th>Zip</th><th>City</th><th>State</th><th class="num">Count</th><th class="num">Revenue</th></tr></thead>
          <tbody id="geoZipBody"></tbody>
        </table>
      </div>
    </div>
    <div class="chart-card">
      <div class="chart-title" id="geoDetailTitle">Service Mix</div>
      <div class="chart-subtitle" id="geoDetailSub">Select a zip on the left</div>
      <div id="geoDetailBox" class="geo-detail-empty">No zip selected.</div>
    </div>
  </div>

  <div class="section-header">
    <div class="section-dot" style="background:var(--orange);"></div>
    <div class="section-title">Top Cities by Revenue</div>
    <div class="section-line"></div>
  </div>

  <div class="chart-card" style="margin-bottom:1rem;">
    <div class="geo-scroll">
      <table class="geo-table">
        <thead><tr><th>City</th><th>State</th><th class="num">Procedures</th><th class="num">Revenue</th></tr></thead>
        <tbody id="geoCityBody"></tbody>
      </table>
    </div>
  </div>

  <div class="section-header">
    <div class="section-dot" style="background:var(--amber);"></div>
    <div class="section-title">Data Quality — Duplicate Client Names</div>
    <div class="section-line"></div>
    <div class="section-badge" id="geoDupBadge">Top 30 by group size</div>
  </div>

  <div class="chart-card">
    <div class="chart-subtitle" style="margin-bottom:1rem;">
      Same name across multiple Client IDs. Active = had 2025/2026 activity.
      A green active flag on multiple records in one group likely means a true duplicate worth merging.
    </div>
    <div class="geo-scroll" id="geoDupBox"></div>
  </div>

</main>
</div>
{END_MARK}"""

# ----------------------------------------------------------------------
# JS block
# ----------------------------------------------------------------------
GEO_JS = f"""{JS_START}
const GEO_DATA = {geo_json};

function geoFmtMoney(n) {{
  if (n >= 1000) return '$' + (n/1000).toFixed(1).replace(/\\.0$/,'') + 'K';
  return '$' + Math.round(n).toLocaleString();
}}
function geoFmtMoneyFull(n) {{
  return '$' + Math.round(n).toLocaleString();
}}

function renderGeographyTab() {{
  const s = GEO_DATA.summary;
  document.getElementById('geoTotalClients').textContent = s.totalClients.toLocaleString();
  document.getElementById('geoActiveClients').textContent = s.activeClients.toLocaleString();
  document.getElementById('geoDormantClients').textContent = s.dormantClients.toLocaleString();
  document.getElementById('geoZipsServed').textContent = s.distinctZipsServed.toLocaleString();
  document.getElementById('geoDupGroups').textContent = s.duplicateGroups.toLocaleString();
  document.getElementById('geoLinkedRev').textContent = geoFmtMoneyFull(s.totalRevenue - s.unknownClientRevenue - s.noZipRevenue);

  const activePct = (s.activeClients / s.totalClients * 100).toFixed(1);
  document.getElementById('geoActiveDormant').textContent = `${{activePct}}% active`;
  document.getElementById('geoDupRecords').textContent = `${{s.duplicateRecords.toLocaleString()}} client records`;
  document.getElementById('geoMatchRate').textContent = `${{s.unparsedAddresses}} unparsed addresses`;
  document.getElementById('geoLinkedSub').textContent = `${{s.totalLineItems.toLocaleString()}} line items joined`;

  // State table
  const stateBody = document.getElementById('geoStateBody');
  const maxStateRev = Math.max(...GEO_DATA.states.map(r => r.revenue));
  stateBody.innerHTML = GEO_DATA.states.map(r => `
    <tr>
      <td><strong>${{r.state}}</strong></td>
      <td class="num">${{r.count.toLocaleString()}}</td>
      <td class="num">
        <span class="geo-bar-wrap"><span class="geo-bar" style="width:${{(r.revenue/maxStateRev*100).toFixed(1)}}%"></span></span>
        ${{geoFmtMoneyFull(r.revenue)}}
      </td>
    </tr>
  `).join('');

  // Zip table (full, scrollable)
  renderZipTable(GEO_DATA.zips);

  // City table
  const cityBody = document.getElementById('geoCityBody');
  cityBody.innerHTML = GEO_DATA.cities.slice(0, 60).map(r => `
    <tr>
      <td><strong>${{r.city}}</strong></td>
      <td class="muted">${{r.state || '?'}}</td>
      <td class="num">${{r.count.toLocaleString()}}</td>
      <td class="num">${{geoFmtMoneyFull(r.revenue)}}</td>
    </tr>
  `).join('');

  // Top 20 zips bar chart
  const top = GEO_DATA.zips.slice(0, 20);
  new Chart(document.getElementById('geoZipChart'), {{
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
              return [`Revenue: ${{geoFmtMoneyFull(r.revenue)}}`, `Procedures: ${{r.count.toLocaleString()}}`];
            }}
          }}
        }}
      }},
      scales: {{
        x: {{ ticks: {{ callback: v => geoFmtMoney(v) }}, grid: {{ color: 'rgba(255,255,255,0.04)' }} }},
        y: {{ grid: {{ display: false }} }}
      }}
    }}
  }});

  // Duplicate groups
  const dupBox = document.getElementById('geoDupBox');
  dupBox.innerHTML = GEO_DATA.duplicates.map(g => {{
    const rows = g.records.map(r =>
      `<div class="dup-row"><span class="cid">${{r.clientId}}</span> · ${{r.name}} · ${{r.zip || '----'}} ${{r.city || ''}} ${{r.state || ''}} ${{r.active ? '<span class="active-flag">● ACTIVE</span>' : ''}}</div>`
    ).join('');
    return `<div class="dup-card">
      <div class="dup-name">${{g.records[0].name}} <span style="font-weight:400;color:var(--muted);font-size:0.72rem;">(${{g.records.length}} records)</span></div>
      ${{rows}}
    </div>`;
  }}).join('');
  document.getElementById('geoDupBadge').textContent = `Showing ${{GEO_DATA.duplicates.length}} of ${{s.duplicateGroups}}`;

  // Search
  document.getElementById('geoZipSearch').addEventListener('input', (e) => {{
    const q = e.target.value.trim().toLowerCase();
    if (!q) {{ renderZipTable(GEO_DATA.zips); return; }}
    const filt = GEO_DATA.zips.filter(r =>
      r.zip.includes(q) ||
      (r.city || '').toLowerCase().includes(q)
    );
    renderZipTable(filt);
  }});
}}

function renderZipTable(rows) {{
  const body = document.getElementById('geoZipBody');
  body.innerHTML = rows.map(r => `
    <tr onclick="selectZip('${{r.zip}}', this)">
      <td class="zip-cell">${{r.zip}}</td>
      <td>${{r.city || '<span class="muted">?</span>'}}</td>
      <td class="muted">${{r.state || '?'}}</td>
      <td class="num">${{r.count.toLocaleString()}}</td>
      <td class="num">${{geoFmtMoneyFull(r.revenue)}}</td>
    </tr>
  `).join('');
}}

function selectZip(zip, el) {{
  document.querySelectorAll('#geoZipBody tr').forEach(t => t.classList.remove('selected'));
  el.classList.add('selected');
  const z = GEO_DATA.zips.find(r => r.zip === zip);
  if (!z) return;
  document.getElementById('geoDetailTitle').textContent = `${{z.zip}} · ${{z.city || ''}}, ${{z.state || ''}}`;
  document.getElementById('geoDetailSub').textContent = `${{z.count.toLocaleString()}} procedures · ${{geoFmtMoneyFull(z.revenue)}} revenue · top 5 services`;
  const box = document.getElementById('geoDetailBox');
  box.classList.remove('geo-detail-empty');
  if (!z.topServices.length) {{
    box.innerHTML = '<div class="geo-detail-empty">No services found.</div>';
    return;
  }}
  box.innerHTML = '<ul class="svc-list">' + z.topServices.map(s =>
    `<li>
      <span class="svc-name">${{s.name}}</span>
      <span class="svc-count">${{s.count}}×</span>
      <span class="svc-rev">${{geoFmtMoneyFull(s.revenue)}}</span>
    </li>`
  ).join('') + '</ul>';
}}

// Render once the DOM is ready (script is at end of body, so safe to call now).
renderGeographyTab();
{JS_END}"""

# ----------------------------------------------------------------------
# Apply edits
# ----------------------------------------------------------------------
html = HTML.read_text()

# Strip prior auto-injected blocks
html = re.sub(re.escape(CSS_START) + r".*?" + re.escape(CSS_END), "", html, flags=re.DOTALL)
html = re.sub(re.escape(START_MARK) + r".*?" + re.escape(END_MARK), "", html, flags=re.DOTALL)
html = re.sub(re.escape(JS_START) + r".*?" + re.escape(JS_END), "", html, flags=re.DOTALL)

# Insert CSS just before the closing </style>
html = html.replace("  </style>", GEO_CSS + "\n  </style>", 1)

# Insert tab page right before the FOOTER comment
html = html.replace("<!-- FOOTER -->", GEO_TAB + "\n\n<!-- FOOTER -->", 1)

# Insert JS right before closing </script>
html = html.replace("\n</script>\n</body>", "\n" + GEO_JS + "\n</script>\n</body>", 1)

HTML.write_text(html)
print(f"Updated {HTML} -> {len(html):,} bytes")
