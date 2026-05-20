#!/usr/bin/env python3
"""Inject the Funding / Grants tab into naws-dashboard-2025.html.

Idempotent: replaces existing funding block if found, else inserts.
"""
import json
import re
from pathlib import Path

ROOT = Path("/Users/bryanengel/NAWS Data")
HTML = ROOT / "naws-dashboard-2025.html"
DATA = ROOT / "funding_data.json"

TAB_START = "<!-- ═══ FUNDING (auto) ═══ -->"
TAB_END = "<!-- ═══ /FUNDING (auto) ═══ -->"
JS_START = "/* ═══ FUNDING (auto) ═══ */"
JS_END = "/* ═══ /FUNDING (auto) ═══ */"
CSS_START = "/* ═══ FUNDING CSS (auto) ═══ */"
CSS_END = "/* ═══ /FUNDING CSS (auto) ═══ */"

fund_json = json.dumps(json.loads(DATA.read_text()), separators=(",", ":"))

CSS = f"""{CSS_START}
.fund-pill {{
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 0.65rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
}}
.fund-pill.grant {{ background: rgba(74,222,128,0.15); color: var(--green); }}
.fund-pill.donation {{ background: rgba(167,139,250,0.15); color: var(--purple); }}
.fund-pill.cc {{ background: rgba(76,154,255,0.15); color: var(--blue); }}
.fund-pill.cash {{ background: rgba(251,191,36,0.15); color: var(--amber); }}
.fund-pill.check {{ background: rgba(34,211,238,0.15); color: var(--cyan); }}
.fund-pill.other {{ background: rgba(139,148,158,0.15); color: var(--muted); }}
.fund-pill.canceled {{ background: rgba(248,113,113,0.15); color: var(--red); }}
.fund-pill.payment {{ background: rgba(74,222,128,0.15); color: var(--green); }}
.fund-pill.refund {{ background: rgba(251,146,60,0.15); color: var(--orange); }}

.fund-table {{ width: 100%; border-collapse: collapse; }}
.fund-table th {{
  font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--muted); padding: 8px 12px; text-align: left;
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; background: var(--surface);
}}
.fund-table th.num, .fund-table td.num {{ text-align: right; }}
.fund-table td {{
  font-size: 0.78rem; padding: 9px 12px;
  border-bottom: 1px solid var(--border);
}}
.fund-table tr:last-child td {{ border-bottom: none; }}
.fund-table tr:hover td {{ background: var(--surface2); }}
.fund-table .mono {{ font-family: 'Menlo','Monaco',monospace; font-size: 0.74rem; }}
.fund-table .muted {{ color: var(--muted); }}
.fund-table .canceled-row td {{ opacity: 0.55; }}
.fund-table .note {{ color: var(--muted); font-size: 0.72rem; font-style: italic; max-width: 320px; }}

.fund-scroll {{ max-height: 480px; overflow-y: auto; }}

.fund-pair {{
  background: var(--surface2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--orange);
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 10px;
  font-size: 0.78rem;
}}
.fund-pair-header {{ font-weight: 700; margin-bottom: 6px; }}
.fund-pair-detail {{ color: var(--muted); font-size: 0.74rem; }}

.fund-bar-wrap {{
  display: inline-block; width: 100px; height: 6px;
  background: var(--surface2); border-radius: 3px; overflow: hidden;
  vertical-align: middle; margin-right: 8px;
}}
.fund-bar {{ height: 100%; border-radius: 3px; background: var(--teal); }}
{CSS_END}"""

TAB_HTML = f"""{TAB_START}
<div id="tab-funding" class="tab-page">
<main>

  <div class="section-header">
    <div class="section-dot" style="background:var(--green);"></div>
    <div class="section-title">Funding &amp; Payment Mix</div>
    <div class="section-line"></div>
    <div class="section-badge" id="fundPeriod">Q1 2026</div>
  </div>

  <div class="geo-kpi-grid">
    <div class="geo-kpi" style="--accent-color: var(--teal);">
      <div class="geo-kpi-label">Total Collected (Net)</div>
      <div class="geo-kpi-value" id="fundTotalNet">$0</div>
      <div class="geo-kpi-sub" id="fundRowCount">0 transactions</div>
    </div>
    <div class="geo-kpi" style="--accent-color: var(--green);">
      <div class="geo-kpi-label">Grant Revenue</div>
      <div class="geo-kpi-value" id="fundGrantNet">$0</div>
      <div class="geo-kpi-sub">MO Dept Ag Grant 2026</div>
    </div>
    <div class="geo-kpi" style="--accent-color: var(--purple);">
      <div class="geo-kpi-label">Donation Revenue</div>
      <div class="geo-kpi-value" id="fundDonationNet">$0</div>
      <div class="geo-kpi-sub">Mr. Donation fund</div>
    </div>
    <div class="geo-kpi" style="--accent-color: var(--amber);">
      <div class="geo-kpi-label">Subsidized %</div>
      <div class="geo-kpi-value" id="fundSubsidPct">0%</div>
      <div class="geo-kpi-sub">Grant + Donation share of total</div>
    </div>
    <div class="geo-kpi" style="--accent-color: var(--blue);">
      <div class="geo-kpi-label">Credit Card</div>
      <div class="geo-kpi-value" id="fundCCNet">$0</div>
      <div class="geo-kpi-sub" id="fundCCSub">Visa + MC + Amex + Discover</div>
    </div>
    <div class="geo-kpi" style="--accent-color: var(--red);">
      <div class="geo-kpi-label">Cancel / Re-entry Pairs</div>
      <div class="geo-kpi-value" id="fundPairs">0</div>
      <div class="geo-kpi-sub">Adjustments handled (net excludes these)</div>
    </div>
  </div>

  <div class="section-header">
    <div class="section-dot" style="background:var(--teal);"></div>
    <div class="section-title">Net Revenue by Payment Type</div>
    <div class="section-line"></div>
    <div class="section-badge">Canceled rows excluded</div>
  </div>

  <div class="grid-1-2" style="margin-bottom:1rem;">
    <div class="chart-card">
      <div class="chart-title">Payment Type Mix</div>
      <div class="chart-subtitle">Share of net revenue</div>
      <div class="chart-container" style="height:300px;">
        <canvas id="fundMixChart"></canvas>
      </div>
    </div>
    <div class="chart-card">
      <div class="chart-title">All Payment Types</div>
      <div class="chart-subtitle">Sorted by net revenue. Gross = before any cancels/refunds.</div>
      <div class="fund-scroll">
        <table class="fund-table">
          <thead><tr>
            <th>Type</th><th>Category</th>
            <th class="num">Net $</th><th class="num">Net #</th>
            <th class="num">Canceled</th><th class="num">Refunds</th>
          </tr></thead>
          <tbody id="fundTypeBody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="section-header">
    <div class="section-dot" style="background:var(--green);"></div>
    <div class="section-title">MO Dept Ag Grant 2026 — Transactions</div>
    <div class="section-line"></div>
    <div class="section-badge" id="fundGrantBadge">0 transactions</div>
  </div>

  <div class="chart-card" style="margin-bottom:1rem;">
    <div class="chart-subtitle" style="margin-bottom:1rem;">
      Net Jan / Feb / Mar: <span id="fundGrantMonthly" style="font-weight:600;color:var(--text);">—</span>
    </div>
    <div class="fund-scroll">
      <table class="fund-table">
        <thead><tr>
          <th>Date</th><th>Client</th><th>Patients</th><th>Invoice</th>
          <th class="num">Amount</th><th>Status</th><th>Note</th><th>Staff</th>
        </tr></thead>
        <tbody id="fundGrantBody"></tbody>
      </table>
    </div>
  </div>

  <div class="section-header">
    <div class="section-dot" style="background:var(--purple);"></div>
    <div class="section-title">Mr. Donation Fund — Transactions</div>
    <div class="section-line"></div>
    <div class="section-badge" id="fundDonationBadge">0 transactions</div>
  </div>

  <div class="chart-card" style="margin-bottom:1rem;">
    <div class="chart-subtitle" style="margin-bottom:1rem;">
      Net Jan / Feb / Mar: <span id="fundDonationMonthly" style="font-weight:600;color:var(--text);">—</span>
    </div>
    <div class="fund-scroll">
      <table class="fund-table">
        <thead><tr>
          <th>Date</th><th>Client</th><th>Patients</th><th>Invoice</th>
          <th class="num">Amount</th><th>Status</th><th>Note</th><th>Staff</th>
        </tr></thead>
        <tbody id="fundDonationBody"></tbody>
      </table>
    </div>
  </div>

  <div class="section-header">
    <div class="section-dot" style="background:var(--orange);"></div>
    <div class="section-title">Cancel / Re-entry Pairs</div>
    <div class="section-line"></div>
    <div class="section-badge">Adjustments collapsed in net</div>
  </div>

  <div class="chart-card">
    <div class="chart-subtitle" style="margin-bottom:1rem;">
      Same invoice + same payment type with a Canceled row and one (or more) kept Payment rows.
      The "Net" KPIs and the totals above already exclude the canceled amounts — these are listed for audit trail.
    </div>
    <div id="fundPairBox"></div>
  </div>

</main>
</div>
{TAB_END}"""

JS = f"""{JS_START}
const FUND_DATA = {fund_json};

function fundMoney(n) {{
  return '$' + Math.round(n).toLocaleString();
}}

function fundShort(n) {{
  if (n >= 1000) return '$' + (n/1000).toFixed(1).replace(/\\.0$/,'') + 'K';
  return '$' + Math.round(n).toLocaleString();
}}

function renderFundingTab() {{
  const s = FUND_DATA.summary;
  document.getElementById('fundPeriod').textContent = FUND_DATA.period;
  document.getElementById('fundTotalNet').textContent = fundMoney(s.totalNet);
  document.getElementById('fundRowCount').textContent = s.totalRows.toLocaleString() + ' transactions';
  document.getElementById('fundGrantNet').textContent = fundMoney(s.grantNet);
  document.getElementById('fundDonationNet').textContent = fundMoney(s.donationNet);
  document.getElementById('fundSubsidPct').textContent = s.subsidizedPct.toFixed(2) + '%';
  document.getElementById('fundCCNet').textContent = fundMoney(s.creditCard.net_amount);
  document.getElementById('fundCCSub').textContent = `${{s.creditCard.net_count.toLocaleString()}} transactions`;
  document.getElementById('fundPairs').textContent = FUND_DATA.cancelPairs.length;

  // Payment type table
  const body = document.getElementById('fundTypeBody');
  const maxNet = Math.max(...FUND_DATA.paymentTypes.map(t => t.netAmount));
  body.innerHTML = FUND_DATA.paymentTypes.map(t => {{
    const cat = (t.category || 'other').toLowerCase().replace(' ', '');
    const pillClass = ({{grant:'grant', donation:'donation', creditcard:'cc', cash:'cash', check:'check'}})[cat] || 'other';
    return `<tr>
      <td><strong>${{t.name}}</strong></td>
      <td><span class="fund-pill ${{pillClass}}">${{t.category}}</span></td>
      <td class="num">
        <span class="fund-bar-wrap"><span class="fund-bar" style="width:${{Math.max(2, (t.netAmount/maxNet*100)).toFixed(1)}}%"></span></span>
        ${{fundMoney(t.netAmount)}}
      </td>
      <td class="num">${{t.netCount.toLocaleString()}}</td>
      <td class="num muted">${{t.canceledCount ? fundMoney(t.canceledAmount) + ' (' + t.canceledCount + ')' : '—'}}</td>
      <td class="num muted">${{t.refundCount ? fundMoney(t.refundAmount) + ' (' + t.refundCount + ')' : '—'}}</td>
    </tr>`;
  }}).join('');

  // Mix doughnut
  const COLORS = [
    'rgba(76,154,255,0.8)','rgba(251,191,36,0.8)','rgba(167,139,250,0.8)','rgba(34,211,238,0.8)',
    'rgba(74,222,128,0.8)','rgba(248,113,113,0.8)','rgba(251,146,60,0.8)','rgba(244,114,182,0.8)',
    'rgba(139,148,158,0.7)','rgba(26,188,156,0.8)',
  ];
  const mixData = FUND_DATA.paymentTypes.filter(t => t.netAmount > 0);
  new Chart(document.getElementById('fundMixChart'), {{
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
        legend: {{ position: 'right', labels: {{ font: {{ size: 10 }}, boxWidth: 10 }} }},
        tooltip: {{
          callbacks: {{
            label: ctx => `${{ctx.label}}: ${{fundMoney(ctx.parsed)}}`
          }}
        }}
      }}
    }}
  }});

  // Detail tables
  renderDetailTable('fundGrantBody', FUND_DATA.moGrant2026);
  renderDetailTable('fundDonationBody', FUND_DATA.mrDonation);
  document.getElementById('fundGrantBadge').textContent = `${{FUND_DATA.moGrant2026.length}} transactions`;
  document.getElementById('fundDonationBadge').textContent = `${{FUND_DATA.mrDonation.length}} transactions`;

  // Monthly lines
  const fmtMonthly = (arr) => arr.map((v, i) => `${{['Jan','Feb','Mar'][i]}} ${{fundMoney(v)}}`).join(' · ');
  document.getElementById('fundGrantMonthly').textContent = fmtMonthly(FUND_DATA.monthly['MO.DEPT AG GRANT 2026']);
  document.getElementById('fundDonationMonthly').textContent = fmtMonthly(FUND_DATA.monthly['Mr. Donation']);

  // Pairs
  const pairBox = document.getElementById('fundPairBox');
  if (!FUND_DATA.cancelPairs.length) {{
    pairBox.innerHTML = '<div class="muted" style="text-align:center;padding:20px;">No cancel/re-entry pairs detected.</div>';
  }} else {{
    pairBox.innerHTML = FUND_DATA.cancelPairs.map(p => {{
      const cancels = p.canceled.map(c => `${{c.date}} ${{fundMoney(c.amount)}}`).join(', ');
      const kept = p.kept.map(c => `${{c.date}} ${{fundMoney(c.amount)}}`).join(', ');
      return `<div class="fund-pair">
        <div class="fund-pair-header">${{p.client}} — Invoice ${{p.invoiceId}} <span class="muted" style="font-weight:400;">· ${{p.paymentType}}</span></div>
        <div class="fund-pair-detail">
          <span class="fund-pill canceled">Canceled</span> ${{cancels}} &nbsp;→&nbsp;
          <span class="fund-pill payment">Kept</span> ${{kept}}
        </div>
      </div>`;
    }}).join('');
  }}
}}

function renderDetailTable(elId, rows) {{
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
      <td class="num"><strong>${{fundMoney(r.amount)}}</strong></td>
      <td><span class="fund-pill ${{pillCls}}">${{r.type}}</span></td>
      <td class="note">${{r.note || ''}}</td>
      <td class="muted">${{r.user || ''}}</td>
    </tr>`;
  }}).join('');
}}

renderFundingTab();
{JS_END}"""

# ----------------------------------------------------------------------
# Apply edits
# ----------------------------------------------------------------------
html = HTML.read_text()

# Strip any prior auto-injected funding blocks
for s, e in [(CSS_START, CSS_END), (TAB_START, TAB_END), (JS_START, JS_END)]:
    html = re.sub(re.escape(s) + r".*?" + re.escape(e), "", html, flags=re.DOTALL)

# Add tab nav button (idempotent — only add if not already there)
if "switchTab('funding')" not in html:
    html = html.replace(
        '<button class="tab-btn" onclick="switchTab(\'geography\')">🗺️ Geography</button>',
        '<button class="tab-btn" onclick="switchTab(\'geography\')">🗺️ Geography</button>\n  '
        '<button class="tab-btn" onclick="switchTab(\'funding\')">💵 Funding</button>',
        1
    )

# Insert CSS before </style>
html = html.replace("  </style>", CSS + "\n  </style>", 1)

# Insert tab HTML before footer
html = html.replace("<!-- FOOTER -->", TAB_HTML + "\n\n<!-- FOOTER -->", 1)

# Insert JS before </script>
html = html.replace("\n</script>\n</body>", "\n" + JS + "\n</script>\n</body>", 1)

HTML.write_text(html)
print(f"Updated {HTML} -> {len(html):,} bytes")
