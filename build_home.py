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

# ---- home screen ----
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

  .wrap {{ max-width:900px; margin:-26px auto 0; padding:0 20px 30px; width:100%; }}
  .cards {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  @media (max-width:680px) {{ .cards {{ grid-template-columns:1fr; }} }}
  .card {{ display:flex; flex-direction:column; background:#fff; border:1px solid var(--line);
    border-radius:16px; box-shadow:0 6px 20px rgba(16,24,40,.08); padding:22px; text-decoration:none;
    color:inherit; transition:transform .12s ease, box-shadow .12s ease; }}
  .card:hover {{ transform:translateY(-3px); box-shadow:0 12px 28px rgba(16,24,40,.14); }}
  .badge {{ align-self:flex-start; font-size:11px; font-weight:700; letter-spacing:.5px;
    text-transform:uppercase; padding:4px 10px; border-radius:999px; margin-bottom:14px; }}
  .fhir .badge {{ background:#e3f2fd; color:#1565c0; }}
  .fusion .badge {{ background:#e0f2f1; color:#0b7c7b; }}
  .card h2 {{ margin:0 0 6px; font-size:19px; }}
  .card .sub {{ color:var(--muted); font-size:13.5px; line-height:1.5; flex:1; }}
  .open {{ margin-top:16px; font-weight:700; color:var(--brand-2); }}
  .fhir .open {{ color:#1565c0; }}

  .note {{ max-width:900px; margin:22px auto 40px; padding:16px 20px; background:#fff;
    border:1px solid var(--line); border-radius:12px; color:var(--muted); font-size:13px; line-height:1.6; }}
  .note b {{ color:var(--ink); }}
  .foot {{ text-align:center; color:var(--muted); font-size:11.5px; padding:0 0 26px; }}
  svg {{ width:26px; height:26px; }}
</style>
</head>
<body>
  <div class="top">
    <div class="mark"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h4l2 6 4-14 2 8h6"/></svg></div>
    <h1>SHIN-NY Community Health Record</h1>
    <p>One patient record, viewed two ways &mdash; same data, same de-duplication rules.</p>
    <div class="conn"><span class="live"></span> {n_people} synthetic patients &middot; C-CDA + genuine HL7 ORU</div>
  </div>

  <div class="wrap">
    <div class="cards">
      <a class="card fhir" href="marcus_fhir.html">
        <span class="badge">FHIR style</span>
        <h2>SMART on FHIR view</h2>
        <div class="sub">A modern app-style dashboard: patient banner, resource cards
          (Condition, MedicationRequest, Observation&hellip;), and tabbed sections. Feels like
          an app launched from an EHR.</div>
        <div class="open">Open the FHIR view &rarr;</div>
      </a>
      <a class="card fusion" href="marcus_fusion.html">
        <span class="badge">HEALTHeLINK style</span>
        <h2>Fusion clinical viewer</h2>
        <div class="sub">The HEALTHeLINK Fusion look: patient banner with chart flags, the
          Chartbook left-nav, and one clinical section at a time in dense clinical tables.</div>
        <div class="open">Open the HEALTHeLINK view &rarr;</div>
      </a>
    </div>

    <div class="note">
      Both views are generated from the <b>same bundle</b> (<code>marcus_bundle</code>): the same
      5 C-CDA documents and the same genuine <b>HL7 v2.5.1 ORU</b> lab feeds, parsed by the same
      code. The <b>de-duplication is identical</b> in both: an ORU result that matches a CCD lab on
      LOINC&nbsp;+&nbsp;date is shown as <b>preferred</b>, and the duplicate CCD value is
      <b>crossed off, never deleted</b>. Open the Lab Results of any patient to see it.
    </div>
  </div>

  <div class="foot">Synthetic demonstration data only. Not affiliated with CRISP or Hixny. FHIR&reg; is an HL7 trademark.</div>
</body>
</html>"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(INDEX)

print('Wrote: index.html, marcus_fhir.html, marcus_fusion.html')
print(f'Patients: {n_people}')
