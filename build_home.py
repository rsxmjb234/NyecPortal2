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
import build_smart  # noqa: E402,F401  (runs the build with the env above)

# ---- HEALTHeLINK / Fusion style ----
os.environ['CHART_OUT'] = 'marcus_fusion.html'
import build_chart  # noqa: E402,F401

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
    {'name': 'Bronx RHIO', 'region': 'The Bronx', 'color': '#b91c1c',
     'site': 'https://bronxrhio.org', 'href': '', 'live': False},
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
    padding:40px 24px 46px; text-align:center; }}
  .top .mark {{ width:46px; height:46px; border-radius:12px; background:rgba(255,255,255,.18);
    display:inline-flex; align-items:center; justify-content:center; margin-bottom:12px; }}
  .top h1 {{ margin:0; font-size:26px; letter-spacing:.2px; }}
  .top p {{ margin:8px 0 0; opacity:.9; font-size:14.5px; }}
  .conn {{ display:inline-flex; align-items:center; gap:7px; margin-top:14px; font-size:12px;
    background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.3);
    padding:5px 12px; border-radius:999px; }}
  .conn .live {{ width:7px; height:7px; border-radius:50%; background:#34d399;
    box-shadow:0 0 0 3px rgba(52,211,153,.3); }}

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
</style>
</head>
<body>
  <div class="top">
    <div class="mark"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h4l2 6 4-14 2 8h6"/></svg></div>
    <h1>SHIN-NY Community Health Record</h1>
    <p>One patient record, rendered in each Qualified Entity's own style &mdash; {live_n} live, more coming soon.</p>
    <div class="conn"><span class="live"></span> {n_people} synthetic patients &middot; C-CDA + genuine HL7 ORU</div>
  </div>

  <div class="wrap">
    <div class="sec-h">Choose a Qualified Entity (QE)</div>
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
  </div>

  <div class="foot">Synthetic demonstration data only. QE names and links belong to their
    respective organizations; styled wordmarks are shown in place of official logos.
    FHIR&reg; is an HL7 trademark.</div>
</body>
</html>"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(INDEX)

print('Wrote: index.html, marcus_fhir.html, marcus_fusion.html')
print(f'Patients: {n_people}')
