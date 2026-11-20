"""
Build the demo home screen plus both renderings of the SAME Marcus cohort:
  - marcus_fhir.html    SMART on FHIR style (build_smart)
  - marcus_fusion.html  HEALTHeLINK / Fusion style (build_chart)
  - index.html          landing page that links to both
Same bundle (marcus_bundle), same parser, same HL7 ORU + de-duplication rules.
"""
import os
import html

CCD = os.path.join('marcus_bundle', 'ccda')
ORU = os.path.join('marcus_bundle', 'oru-hl7')
E = html.escape

# ---- FHIR / SMART on FHIR style ----
os.environ['CHART_CCD_DIR'] = CCD
os.environ['CHART_ORU_HL7'] = ORU
os.environ['CHART_OUT'] = 'marcus_fhir.html'
os.environ['CHART_TITLE'] = 'SHIN-NY Community Health Record'
os.environ['CHART_QE'] = 'HIXNY'          # this view represents the Hixny portal
import build_smart  # noqa: E402,F401  (runs the build with the env above)

# ---- HEALTHeLINK / Fusion style ----
os.environ['CHART_OUT'] = 'marcus_fusion.html'
os.environ['CHART_QE'] = 'HEALTHELINK'     # this view represents the HEALTHeLINK portal
import build_chart  # noqa: E402,F401

# ---- Bronx RHIO / IMAT Solutions style ----
os.environ['CHART_OUT'] = 'marcus_bronx.html'
os.environ['CHART_QE'] = 'BRONX'           # this view represents the Bronx RHIO (IMAT) portal
import build_bronx  # noqa: E402,F401

n_people = len(build_smart.patients)

# ---- home screen: one view per NY Qualified Entity (QE); some live, rest coming soon ----
QES = [
    {'name': 'Hixny', 'region': 'Capital Region', 'color': '#0e7490',
     'site': 'https://hixny.org', 'href': 'marcus_fhir.html', 'live': True},
    {'name': 'HEALTHeLINK', 'region': 'Western New York', 'color': '#1d4ed8',
     'site': 'https://wnyhealthelink.com', 'href': 'marcus_fusion.html', 'live': True},
    {'name': 'Healthix', 'region': 'NYC & Long Island', 'color': '#059669',
     'site': 'https://healthix.org', 'href': '', 'live': False},
    {'name': 'HealtheConnections', 'region': 'Central NY, North Country & more', 'color': '#ea580c',
     'site': 'https://www.healtheconnections.org', 'href': '', 'live': False},
    {'name': 'Rochester RHIO', 'region': 'Finger Lakes & Southern Tier', 'color': '#7c3aed',
     'site': 'https://rochesterrhio.org', 'href': '', 'live': False},
    {'name': 'Bronx RHIO', 'region': 'The Bronx (IMAT Solutions)', 'color': '#b91c1c',
     'site': 'https://bronxrhio.org', 'href': 'marcus_bronx.html', 'live': True},
]


def _qe_card(q):
    dom = q['site'].replace('https://', '').replace('http://', '').rstrip('/')
    logo = f'<div class="qe-logo">{E(q["name"])}</div>'
    region = f'<div class="qe-region">{E(q["region"])}</div>'
    site = f'<a class="qe-site" href="{q["site"]}" target="_blank" rel="noopener">{E(dom)}</a>'
    if q['live']:
        action = f'<a class="qe-open" href="{q["href"]}">Open the {E(q["name"])} view &rarr;</a>'
        cls = 'qe-card live'
    else:
        action = '<span class="qe-badge">Coming soon</span>'
        cls = 'qe-card soon'
    return f'<div class="{cls}" style="--c:{q["color"]}">{logo}{region}{action}{site}</div>'


cards_html = '\n      '.join(_qe_card(q) for q in QES)
live_n = sum(1 for q in QES if q['live'])

# ============================================================
# Extra CSS â€” plain string so CSS braces need no escaping
# ============================================================
EXTRA_CSS = """
  /* â”€â”€ Understand Volume section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  .report-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:18px; }
  .report-card { background:#fff; border:1px solid var(--line); border-radius:14px;
    padding:20px 22px; box-shadow:0 6px 20px rgba(16,24,40,.08); }
  .report-card.full { grid-column:1/-1; }
  .report-card.soon { opacity:.72; }
  .report-title { font-weight:700; font-size:15.5px; color:var(--ink); }
  .report-sub { font-size:12px; color:var(--muted); }
  .vol-row { display:flex; align-items:center; gap:10px; margin-bottom:9px; }
  .vol-name { width:155px; flex-shrink:0; font-size:12.5px; font-weight:600; color:var(--ink); }
  .vol-bar-wrap { flex:1; height:18px; background:#f1f5f9; border-radius:4px; overflow:hidden; display:flex; }
  .vol-bar-seg { height:100%; transition:width .4s; }
  .vol-total { width:76px; text-align:right; font-size:11.5px; color:var(--muted); flex-shrink:0;
    font-variant-numeric:tabular-nums; }
  .vol-legend { display:flex; gap:16px; margin-top:14px; padding-top:12px;
    border-top:1px solid var(--line); flex-wrap:wrap; }
  .vol-legend-item { display:flex; align-items:center; gap:5px; font-size:11.5px; color:var(--muted); }
  .vol-legend-dot { width:10px; height:10px; border-radius:2px; flex-shrink:0; }
  .report-meta { margin-top:12px; font-size:11px; color:#98a2b3; line-height:1.5; }
  .report-soon-title { font-size:14px; font-weight:600; color:var(--muted); }
  .report-badge { display:inline-block; margin-top:10px; background:#f2f4f7; color:#667085;
    font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.5px;
    padding:4px 10px; border-radius:999px; }

  /* â”€â”€ Hospital report (Report 2) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  .qe-tabs { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; }
  .qe-tab { border:1px solid var(--line); background:#fff; color:var(--muted); font-size:12px;
    font-weight:600; padding:5px 14px; border-radius:999px; cursor:pointer;
    transition:background .12s,color .12s,border-color .12s; }
  .qe-tab:hover { border-color:var(--brand); color:var(--brand); }
  .qe-tab.active { color:#fff; }
  .hosp-badge { display:inline-block; background:#ecfdf5; color:#059669; font-size:12px;
    font-weight:700; padding:3px 10px; border-radius:999px; margin-bottom:12px; }
  .hosp-wrap { overflow-x:auto; max-height:460px; overflow-y:auto;
    border:1px solid var(--line); border-radius:8px; }
  .hosp-tbl { width:100%; border-collapse:collapse; font-size:12.5px; }
  .hosp-tbl th { position:sticky; top:0; background:#f8fafc; text-align:left;
    color:var(--muted); font-size:11px; font-weight:700; text-transform:uppercase;
    letter-spacing:.5px; padding:8px 12px 6px; border-bottom:2px solid var(--line); }
  .hosp-tbl th.r { text-align:right; }
  .hosp-tbl td { padding:7px 12px; border-bottom:1px solid var(--line); }
  .hosp-tbl td.r { text-align:right; font-variant-numeric:tabular-nums; }
  .hosp-tbl td.code { font-family:ui-monospace,monospace; font-size:11px; color:var(--muted); }
  .hosp-tbl td.tot { font-weight:700; }
  .hosp-tbl tbody tr:hover td { background:#f8fafc; }
  /* AA group header (multiple hospitals share one AA) */
  .hosp-tbl tr.aa-grp td { background:#f1f5f9; border-top:2px solid var(--line); }
  .hosp-tbl tr.aa-grp .aa-label { font-family:ui-monospace,monospace; font-size:11.5px;
    font-weight:700; color:var(--brand-2); }
  .hosp-tbl tr.aa-grp .aa-count { font-size:11px; color:var(--muted); margin-left:8px; font-weight:400; }
  /* Sub-rows under a grouped AA */
  .hosp-tbl tr.aa-sub td { border-bottom:1px solid #f3f4f6; }
  .hosp-tbl td.sub-name { padding-left:26px; color:var(--muted); font-size:12px; }"""

# ============================================================
# "Understand Volume" section HTML â€” plain string
# ============================================================
VOLUME_SECTION = """
    <div class="sec-h" id="volume-reports" style="margin-top:36px">Understand Volume</div>
    <div class="report-grid">

      <!-- Report 1: Volume by QE \u2013 Highest Level (hardcoded from Athena run) -->
      <div class="report-card full">
        <div class="report-title">Volume by QE &mdash; Highest Level</div>
        <div class="report-sub" style="margin:3px 0 16px">
          28-day total &middot; Oct&nbsp;18&nbsp;&ndash;&nbsp;Nov&nbsp;14,&nbsp;2026 &middot; Verato-matched sources only
        </div>
        <div id="vol-chart"></div>
        <div class="vol-legend">
          <div class="vol-legend-item"><div class="vol-legend-dot" style="background:#0ea5a4"></div>CCD</div>
          <div class="vol-legend-item"><div class="vol-legend-dot" style="background:#3b82f6"></div>TRN</div>
          <div class="vol-legend-item"><div class="vol-legend-dot" style="background:#94a3b8"></div>LAB</div>
        </div>
        <div class="report-meta">
          Source: <code>DailyVolumeByQE-28Day-SingleSnapshot-ExcludeOrphans.sql</code>
          &middot; 47.24&nbsp;GB scanned &middot; excludes backload &amp; orphan sources
        </div>
      </div>

      <!-- Report 2: Hospital Volume \u2013 Last 10 Days -->
      <div class="report-card full" id="hosp-report">
        <div class="report-title">Hospital Volume &mdash; Last 10 Days</div>
        <div class="report-sub" style="margin:3px 0 16px">
          Nov&nbsp;4&nbsp;&ndash;&nbsp;Nov&nbsp;13,&nbsp;2026 &middot; Article&nbsp;28 hospitals &middot; CCD&nbsp;+&nbsp;TRN &middot; filter by QE
        </div>
        <div class="qe-tabs" id="hosp-tabs"></div>
        <div id="hosp-badge"></div>
        <div class="hosp-wrap">
          <table class="hosp-tbl">
            <thead><tr>
              <th>Hospital</th><th>AA&nbsp;Code</th>
              <th class="r">CCD</th><th class="r">TRN</th><th class="r">Total</th>
            </tr></thead>
            <tbody id="hosp-tbody"></tbody>
          </table>
        </div>
        <div class="report-meta" style="margin-top:14px">
          Source: <code>reportonhospitals.sql</code>
          &middot; 47.23&nbsp;GB scanned &middot; SFDC registry (Article&nbsp;28 only)
          &middot; hospitals with no recent activity shown at bottom
        </div>
      </div>

      <!-- Placeholder 3 -->
      <div class="report-card soon">
        <div class="report-soon-title">Doc-Type Mix by QE</div>
        <div style="color:var(--muted);font-size:13px;margin-top:6px;line-height:1.5">
          CCD vs TRN vs LAB share per QE with week-over-week change &mdash; surfaces shifts in submission patterns.
        </div>
        <span class="report-badge">Coming soon</span>
      </div>

    </div><!-- /report-grid -->"""

# ============================================================
# Report 1 render script â€” plain string (JS braces safe here)
# ============================================================
REPORT1_SCRIPT = """
  <script>
  (function () {
    var rows = [
      { qe: "Healthix",           ccd: 6856187, trn: 3691902, lab: 5822179 },
      { qe: "HealtheConnections", ccd: 4064234, trn: 2946189, lab: 4940467 },
      { qe: "TechBD",             ccd: 1001590, trn:  989702, lab: 1857966 },
      { qe: "Hixny",              ccd: 2497901, trn:   86968, lab: 1177507 },
      { qe: "Bronx RHIO",         ccd:  832486, trn: 1191999, lab: 1209660 },
      { qe: "Rochester RHIO",     ccd: 1159667, trn:  656012, lab:       0 }
    ];
    rows.sort(function(a, b) {
      return (b.ccd + b.trn + b.lab) - (a.ccd + a.trn + a.lab);
    });
    var maxTotal = Math.max.apply(null, rows.map(function(r) { return r.ccd + r.trn + r.lab; }));
    function fmt(n) { return n.toLocaleString(); }
    function pct(v) { return (v / maxTotal * 100).toFixed(2) + '%'; }
    var container = document.getElementById('vol-chart');
    rows.forEach(function(r) {
      var total = r.ccd + r.trn + r.lab;
      var div = document.createElement('div');
      div.className = 'vol-row';
      div.innerHTML =
        '<div class="vol-name">' + r.qe + '</div>' +
        '<div class="vol-bar-wrap">' +
          '<div class="vol-bar-seg" style="width:' + pct(r.ccd) + ';background:#0ea5a4" title="CCD: ' + fmt(r.ccd) + '"></div>' +
          '<div class="vol-bar-seg" style="width:' + pct(r.trn) + ';background:#3b82f6" title="TRN: ' + fmt(r.trn) + '"></div>' +
          '<div class="vol-bar-seg" style="width:' + pct(r.lab) + ';background:#94a3b8" title="LAB: ' + fmt(r.lab) + '"></div>' +
        '</div>' +
        '<div class="vol-total">' + fmt(total) + '</div>';
      container.appendChild(div);
    });
  })();
  </script>"""

# ============================================================
# Report 2 render script â€” plain string
# ============================================================
REPORT2_SCRIPT = """
  <script src="./hosp_data.js"></script>
  <script>
  /* Report 2: Hospital Volume render */
  (function () {
    if (!window.HOSP) return;
    var HOSP = window.HOSP;
    var QE_COLORS = {
      'HealtheConnections':'#ea580c', 'Healthix':'#059669', 'Bronx RHIO':'#b91c1c',
      'HEALTHeLINK':'#1d4ed8', 'Rochester RHIO':'#7c3aed', 'Hixny':'#0e7490'
    };
    var current = HOSP.qes[0];

    function fmt(n) { return n > 0 ? n.toLocaleString() : '\u2014'; }

    function render(qe) {
      var rows = HOSP.rows.filter(function(r) { return r[0] === qe; });

      // Group by AA code, preserving SQL order (total DESC, aa ASC, org ASC)
      var seen = {}, groups = [];
      rows.forEach(function(r) {
        var aa = r[2];
        if (!seen[aa]) {
          seen[aa] = { aa: aa, ccd: r[3], trn: r[4], names: [] };
          groups.push(seen[aa]);
        }
        seen[aa].names.push(r[1]);
      });

      // Sort groups: AA total DESC, then AA name ASC
      groups.sort(function(a, b) {
        var ta = a.ccd + a.trn, tb = b.ccd + b.trn;
        return tb !== ta ? tb - ta : a.aa.localeCompare(b.aa);
      });

      var active = groups.filter(function(g) { return g.ccd + g.trn > 0; }).length;
      document.getElementById('hosp-badge').innerHTML =
        '<span class="hosp-badge">' + active + ' of ' + groups.length +
        ' assigning authorities submitting</span>';

      var html = '';
      groups.forEach(function(g) {
        var tot = g.ccd + g.trn;
        var zero = tot === 0;
        var zc = zero ? ' zero' : '';

        if (g.names.length === 1) {
          // Single hospital â€” clean flat row
          html += '<tr' + (zero ? ' class="zero"' : '') + '>'
            + '<td>' + g.names[0] + '</td>'
            + '<td class="code">' + g.aa + '</td>'
            + '<td class="r">' + fmt(g.ccd) + '</td>'
            + '<td class="r">' + fmt(g.trn) + '</td>'
            + '<td class="r tot">' + fmt(tot) + '</td>'
            + '</tr>';
        } else {
          // Multiple hospitals share this AA â€” group header + sub-rows
          html += '<tr class="aa-grp' + zc + '">'
            + '<td colspan="2"><span class="aa-label">' + g.aa + '</span>'
            + '<span class="aa-count">' + g.names.length + ' hospitals</span></td>'
            + '<td class="r">' + fmt(g.ccd) + '</td>'
            + '<td class="r">' + fmt(g.trn) + '</td>'
            + '<td class="r tot">' + fmt(tot) + '</td>'
            + '</tr>';
          g.names.forEach(function(name) {
            html += '<tr class="aa-sub' + zc + '">'
              + '<td class="sub-name">' + name + '</td>'
              + '<td colspan="4"></td>'
              + '</tr>';
          });
        }
      });
      document.getElementById('hosp-tbody').innerHTML = html;

      var color = QE_COLORS[qe] || 'var(--brand)';
      document.querySelectorAll('#hosp-tabs .qe-tab').forEach(function(btn) {
        var on = btn.dataset.qe === qe;
        btn.classList.toggle('active', on);
        btn.style.background  = on ? color : '';
        btn.style.borderColor = on ? color : '';
      });
    }

    var tabs = document.getElementById('hosp-tabs');
    HOSP.qes.forEach(function(qe) {
      var btn = document.createElement('button');
      btn.className = 'qe-tab';
      btn.dataset.qe = qe;
      btn.textContent = qe;
      btn.addEventListener('click', function() { current = qe; render(qe); });
      tabs.appendChild(btn);
    });

    render(current);
  })();
  </script>"""

# ============================================================
# Assemble index.html
# ============================================================
INDEX = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SHIN-NY Record Viewer &mdash; Demo Home</title>
<style>
  :root {{ --brand:#0ea5a4; --brand-2:#0e7490; --ink:#1f2a37; --muted:#5b6774; --line:#e5e9ee; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; min-height:100vh; color:var(--ink); background:#eef2f6;
    font-family:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
    display:flex; flex-direction:column; }}
  .top {{ background:linear-gradient(90deg,var(--brand-2),var(--brand)); color:#fff;
    padding:28px 24px 32px; text-align:center; }}
  .top h1 {{ margin:0; font-size:24px; letter-spacing:.2px; font-weight:700; }}

  .wrap {{ max-width:1000px; margin:24px auto 0; padding:0 20px 30px; width:100%; }}
  .sec-h {{ font-size:12.5px; font-weight:700; text-transform:uppercase; letter-spacing:.6px;
    color:var(--muted); margin:4px 2px 14px; }}
  .qe-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:18px; }}
  .qe-card {{ background:#fff; border:1px solid var(--line); border-top:4px solid var(--c);
    border-radius:14px; padding:18px; box-shadow:0 6px 20px rgba(16,24,40,.08);
    display:flex; flex-direction:column; min-height:154px; transition:transform .12s, box-shadow .12s; }}
  .qe-card.live:hover {{ transform:translateY(-3px); box-shadow:0 12px 28px rgba(16,24,40,.14); }}
  .qe-card.soon {{ opacity:.72; }}
  .qe-logo {{ font-weight:800; font-size:21px; letter-spacing:-.4px; color:var(--c); }}
  .qe-region {{ color:var(--muted); font-size:12.5px; margin-top:4px; }}
  .qe-open {{ margin-top:14px; font-weight:700; color:var(--c); text-decoration:none; }}
  .qe-open:hover {{ text-decoration:underline; }}
  .qe-badge {{ margin-top:14px; align-self:flex-start; background:#f2f4f7; color:#667085;
    font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.5px;
    padding:4px 10px; border-radius:999px; }}
  .qe-site {{ margin-top:auto; padding-top:12px; font-size:11.5px; color:#98a2b3; text-decoration:none; }}
  .qe-site:hover {{ color:var(--c); text-decoration:underline; }}

  .note {{ margin:22px 0 40px; padding:16px 20px; background:#fff;
    border:1px solid var(--line); border-radius:12px; color:var(--muted); font-size:13px; line-height:1.6; }}
  .note b {{ color:var(--ink); }}
  .foot {{ text-align:center; color:var(--muted); font-size:11.5px; padding:0 0 26px; }}
  .mark svg {{ width:26px; height:26px; }}

  /* â”€â”€ Page nav â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
  .page-nav {{ display:flex; justify-content:center; gap:8px; padding:0 20px 16px;
    background:linear-gradient(90deg,var(--brand-2),var(--brand)); flex-wrap:wrap; }}
  .page-nav a {{ color:rgba(255,255,255,.75); text-decoration:none; font-size:12.5px;
    font-weight:600; padding:6px 18px; border-radius:999px;
    border:1px solid rgba(255,255,255,.3);
    transition:color .12s, background .12s, border-color .12s; }}
  .page-nav a:hover {{ color:#fff; background:rgba(255,255,255,.18); border-color:rgba(255,255,255,.5); }}
  .page-nav a.on {{ color:#fff; background:rgba(255,255,255,.22); border-color:rgba(255,255,255,.5); }}
{EXTRA_CSS}
</style>
</head>
<body>
  <div class="top">
    <h1>QE PDR Viewer</h1>
  </div>
  <nav class="page-nav">
    <a class="on" href="#qe-portals">QE Portals</a>
    <a href="#volume-reports">Volume Reports</a>
  </nav>

  <div class="wrap">
    <div class="sec-h" id="qe-portals">Choose a Qualified Entity (QE)</div>
    <div class="qe-grid">
      {cards_html}
    </div>

    <div class="note">
      Each QE will render the <b>same underlying record</b> in its own look &amp; feel. The two live
      views (Hixny, HEALTHeLINK) are built from one bundle &mdash; the same 5 C-CDA documents and the
      same genuine <b>HL7 v2.5.1 ORU</b> lab feeds, parsed by the same code &mdash; and apply the same
      de-duplication: an ORU result matching a CCD lab on LOINC&nbsp;+&nbsp;date is shown as
      <b>preferred</b> and the duplicate CCD value is <b>crossed off, never deleted</b>.
    </div>
{VOLUME_SECTION}
  </div>

  <div class="foot">Synthetic demonstration data only. QE names and links belong to their
    respective organizations; styled wordmarks are shown in place of official logos.
    FHIR&reg; is an HL7 trademark.</div>
{REPORT1_SCRIPT}
{REPORT2_SCRIPT}
</body>
</html>"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(INDEX)

print('Wrote: index.html, marcus_fhir.html, marcus_fusion.html')
print(f'Patients: {n_people}')
