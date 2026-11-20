# NyecPortal2

Tools for building patient chart views from synthetic **C-CDA** documents and
**ORU** (FHIR R4 Observation) lab feeds held in the `nyec-synthetic-data` S3 bucket.

## Live site

**https://main.d3pz3oj6iuj9t4.amplifyapp.com**

Deploy: run `deploy_amplify.ps1` (requires the `304507007699_AWSPowerUserAccess` sandbox profile).

## Contents

| File | Purpose |
|------|---------|
| `ccda_parse.py` | Shared parser: reads a C-CDA XML into demographics + clinical sections; loads ORU NDJSON labs and flags CCD/ORU duplicates. |
| `build_chart.py` | Renders a multi-patient chart styled after the **HEALTHeLINK Fusion** clinical viewer (`patient_chart.html`). |
| `build_smart.py` | Renders the same data as a **SMART on FHIR**-style dashboard (`patient_chart_smart.html`). |
| `s3_hello_read.py` | Minimal "hello world" read of one object from S3. |
| `_make_oru.py` | Generates the synthetic ORU lab feed used for the dedup demo. |
| `_extract_pdf.py` | Pulls text/images from the Fusion training-guide PDF (design reference). |

## Build

```bash
# Put C-CDA XML files in ./ccds and any *oru*.ndjson feeds in the root, then:
python build_chart.py      # -> patient_chart.html  (Fusion look)
python build_smart.py      # -> patient_chart_smart.html  (SMART on FHIR look)
```

## Not tracked in git (see `.gitignore`)

- **Synthetic data**: `*.xml`, `*.csv`, `*.ndjson`, `ccds/` — regenerable / pulled from S3.
- **Credentials / secrets**: keys, `.env`, and credential helper `*.bat` scripts.
- **Generated output**: the built HTML, screenshots (`*.png`), the reference PDF.
- **Sub-projects** `PublicHealthPortal/` and `PublicHealthPortalDemo20/` — they have their own git repos.

Data is 100% synthetic; it exists only for demonstration.
