# Implementation Plan — Marcus Multi-QE Data Overhaul

- [ ] 1. **Copy Synthea base CCDs into the worktree.** The 10 base CCDs live in the main repo's `ccds/` (gitignored). Copy them into the worktree's `ccds/` so `build_marcus_bundle.py` can read them.
      Files: `ccds/` (copy from main repo)
      Verify: `ls ccds/*.xml` shows 10 files.

- [ ] 2. **Rewrite `build_marcus_bundle.py` for 15 sources in per-QE folders.** Replace the single-base-CCD approach with per-source base CCD assignments. Add `make_trn()` for TRN generation. Output to `marcus_bundle/{qe_lower}/ccda/`, `/oru-hl7/`, `/trn/` instead of flat dirs. Remove Rochester/GRRHIO. Generate varied ORU lab values per source. Generate MPI CSV with 15 rows. Update README.
      Files: `build_marcus_bundle.py`, generated: `marcus_bundle/` (5 QE subfolders × 3 file types × 3 files each = 45 data files)
      Verify: `python.exe build_marcus_bundle.py` succeeds. 15 CCDs, 15 ORUs, 15 TRNs in correct folders. No GRRHIO files.

- [ ] 3. **Add TRN directory support to the 3 build renderers.** In `build_smart.py`, `build_chart.py`, and `build_bronx.py`, add `CHART_TRN_DIR` env var support. After the CCD file glob, also glob TRN files if the env var is set.
      Files: `build_smart.py`, `build_chart.py`, `build_bronx.py`
      Verify: Each file has the `TRN_DIR` logic. Build still works with empty TRN_DIR (no regression).

- [ ] 4. **Parameterize hardcoded "HIXNY" in `build_smart.py`.** Replace the two hardcoded `HIXNY` strings in the HTML template (subtitle and title tag) with `VIEW_QE` which is already read from the `CHART_QE` env var.
      Files: `build_smart.py`
      Verify: Read the file and confirm no hardcoded HIXNY in the HTML template.

- [ ] 5. **Rewrite `build_home.py` for 5 QE views.** Use `importlib.reload(build_smart)` for Healthix and HealtheConnections. Set per-QE env vars (CCD_DIR, ORU_HL7, TRN_DIR, OUT, QE). Build 5 views: HIXNY→marcus_fhir.html (build_smart), HEALTHELINK→marcus_fusion.html (build_chart), HEALTHIX→marcus_healthix.html (reload build_smart), HEALTHECONN→marcus_healtheconn.html (reload build_smart), BRONX→marcus_bronx.html (build_bronx). Update QES list: all 5 live, no Rochester. Update the descriptive note text.
      Files: `build_home.py`
      Verify: `python.exe build_home.py` produces 6 HTML files (5 QE views + index.html). Each QE view has exactly 3 MRNs.

- [ ] 6. **Update `deploy_amplify.ps1`.** Add `marcus_healthix.html` and `marcus_healtheconn.html` to the Copy-Item line.
      Files: `deploy_amplify.ps1`
      Verify: Read the file and confirm all 5 QE HTML files are in the Copy-Item list.

## Digest

### build_marcus_bundle.py (rewrite)
- Currently: single `BASE_CCD`, 5 SOURCES, flat output to `marcus_bundle/ccda/` and `marcus_bundle/oru-hl7/`
- Change: 15 SOURCES with per-source `base` CCD, per-QE subfolder output, new `make_trn()` function
- No tests exist. Verify: run `python.exe build_marcus_bundle.py`, check file counts.

### build_smart.py (modify module-level build section, ~line 276+)
- Block: `files = sorted(glob.glob(os.path.join(CCD_DIR, '*.xml')))` — add TRN_DIR glob
- Block: `<title>{E(TITLE)} &mdash; HIXNY</title>` and `<div class="sub">HIXNY &middot; demonstration</div>` — replace HIXNY with VIEW_QE
- No tests. Verify: `python.exe build_home.py` succeeds.

### build_chart.py (modify module-level build section, near bottom after ccda_parse import)
- Block: `files = sorted(glob.glob(os.path.join(CCD_DIR, '*.xml')))` — add TRN_DIR glob
- No tests. Verify: `python.exe build_home.py` succeeds.

### build_bronx.py (modify module-level build section, ~line 193+)
- Block: `files = sorted(glob.glob(os.path.join(CCD_DIR, '*.xml')))` — add TRN_DIR glob
- No tests. Verify: `python.exe build_home.py` succeeds.

### build_home.py (rewrite)
- Currently: sets env vars, imports build_smart/build_chart/build_bronx for 3 QEs + builds index.html
- Change: 5 QEs with per-QE folder paths, importlib.reload for repeated build_smart, updated QES list (all live, no Rochester)
- No tests. Verify: `python.exe build_home.py` produces 6 HTML files with correct per-QE MRN counts.

### deploy_amplify.ps1 (one-line change)
- Block: `Copy-Item index.html, marcus_fhir.html, marcus_fusion.html, marcus_bronx.html, hosp_data.js, nonhosp_data.js _site\`
- Change: add `marcus_healthix.html, marcus_healtheconn.html` to the list
- No tests. Verify: read the file.

### ccda_parse.py — NO CHANGES. TRN support is in the build scripts' file-globbing logic, not the parser.

### Verified build command: `python.exe build_home.py` (must run from worktree root after build_marcus_bundle.py has generated data)
