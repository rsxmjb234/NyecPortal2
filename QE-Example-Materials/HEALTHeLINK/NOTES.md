# HEALTHeLINK (Western New York)

- Official site: https://wnyhealthelink.com
- Portal/product: **HEALTHeLINK Fusion** (the "HealthShare" clinical viewer),
  reached through the HEALTHeCOMMUNITY Portal.
- Region: Western New York (Buffalo area). SHIN-NY Qualified Entity.

## Materials in this folder
- `HEALTHeLINK-Fusion-User-Training-Guide.pdf` — the official Fusion user
  training guide (v2.5, dated Nov 2025).
- `fusion-training-guide-text.txt` — extracted text of the guide.
- `fusion-training-guide-screenshots/` — 48 images extracted from the guide
  (login, patient search, consent, clinical viewer, chartbook, lab results,
  reports, etc.).

## UI / workflow concepts worth mirroring (from the guide)
- **Access path:** HEALTHeCOMMUNITY Portal badges -> HEALTHeLINK badge ->
  Confidentiality Acknowledgement -> Duo two-factor -> Fusion Gateway ->
  HealthShare.
- **Patient Search:** left "Search Criteria" panel (Last name, First name, DOB
  required); results table with Name, Age, Gender, DOB, Address, Master Patient
  Identifier; a caret expands per-source rows showing **Medical Record Number,
  Assigning Authority, and Info Types** (icons). Consent gates visibility.
- **Clinical viewer / Clinical Summary:** patient banner with **chart flags**
  (hover/click icons), a left-hand **Chartbook** navigation (sections with data
  marked in blue), one section at a time.
- **Lab Results:** table with Lab Test, Result, Units, Flag, Reference Range,
  Status, Trend, Order, Facility, Collection Date; **abnormal results flagged in
  red** on the left; search + sort/filter (three-bar filter icon).
- **Reports:** per-section reports (default last 30 days) with view / download /
  print; "New Report" builder by data type + date range; save named reports.
- **Audit:** same-name access, break-the-glass, patient-data-access audits.

These directly informed the "HEALTHeLINK style" (Fusion) view in the demo:
patient banner + chart flags, Chartbook left-nav, dense clinical tables, red
abnormal flags.

Source: HEALTHeLINK Fusion User Training Guide (public training material);
https://wnyhealthelink.com. Content paraphrased for compliance.
