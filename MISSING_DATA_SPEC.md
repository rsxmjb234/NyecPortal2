# Missing Data — Feature Build Spec

A build-ready specification for the **Missing data** feature of the SHIN-NY
record portal. Written so a fresh agent/engineer can implement it from scratch.

PDR = the Patient Data Repository (what this portal shows).
QE  = a Qualified Entity / source feed (e.g. HEALTHIX, HEALTHELINK, HIXNY, GRRHIO, BRONX).

The portal renders a patient record from **C-CDA documents** plus **genuine HL7
v2 ORU** lab feeds, and reconciles duplicate labs. The **Missing data** feature
lets a user report a discrepancy between what PDR shows and what a QE has, so a
reconciliation team can chase it down. The feature is identical across both
front-end styles the portal ships (the "HIXNY"/SMART-on-FHIR view and the
"HEALTHeLINK"/Fusion view).

---

## 1. Trigger

- A prominent button in the top app bar of **every** patient view, labelled
  **"⚠ Missing data"** (warning glyph + text).
- Clicking it opens a modal, pre-populated from the **currently viewed patient**
  and the **current screen/section**.

## 2. Step 1 — choose the direction of the discrepancy

The modal first asks: **"Where is the data missing?"** with two choices:

1. **QE has it — PDR does not** — it's in a QE/source feed but not in PDR.
2. **PDR has it — QE does not** — it's on this PDR screen but a QE is missing it.

The direction is recorded on the ticket and drives which fields show next.

## 3. Direction A — "QE has it — PDR does not"

The data is somewhere in a QE but not in front of us, so **do not pre-fill**
QE / Source / MRN — the record on screen is almost certainly *not* the source
that has it.

Fields:
| Field | Source | Editable? |
|-------|--------|-----------|
| First, Last, DOB | from the viewed patient | read-only |
| Screen | current section, shown as `"<First> - <Section>"` e.g. `Marcus - Lab Results` | read-only |
| QE, Source, MRN | **blank**, placeholder "if known" | editable |
| `<DataType>` (label adapts to screen — see §6) | user | editable |
| Date | user | editable |
| Result (label adapts — see §6) | user | editable |
| Notes | user; prompt adapts: *"Describe what `<datatype>` you see in the QE we don't show here"* | editable |

## 4. Direction B — "PDR has it — QE does not"

The element is on the current PDR screen; the patient's **own QE** is the one
missing it, so **pre-fill** QE / Source / MRN (read-only). Section heading reads
**"Which PDR element is the QE (`<QE>`) missing?"**

Fields:
| Field | Source | Editable? |
|-------|--------|-----------|
| First, Last, DOB, Screen | viewed patient / current section | read-only |
| QE, Source, MRN | pre-filled from the patient's assigning authority (`QE\|Source`) + MRN | read-only |
| Data ID | user pastes an ID copied from a row on the screen (see §7); plus a "Use last copied Data ID" button | editable |
| Notes | user | editable |

## 5. Auto-captured metadata — on EVERY ticket, both directions

Shown read-only at the end of the form and always included in the payload:
- **Date** — today's report date.
- **MRN array** — every MRN that makes up this patient *as of when we looked*,
  each as `MRN (QE|Source)`. Built from all real source identifiers on the
  record (exclude internal EID/MPID ids). In a single-source record this has one
  entry; the structure must support many for multi-source MPI identities.

## 6. Screen-adaptive field mapping (Direction A)

The item/result labels, placeholders, and the notes prompt change with the
active screen. Default (unknown screen) = `Item` / `Value`.

| Screen | Item label | Result label | Item example | Result example |
|--------|-----------|--------------|--------------|----------------|
| Lab Results | Lab | Result | Hemoglobin A1c | 7.2 % |
| Medications | Medication | Dose / Status | Metformin 500 mg | Active |
| Conditions | Condition | Status | Type 2 diabetes | Active |
| Vitals / Vital Signs | Vital | Value | Blood pressure | 128/82 |
| Immunizations | Immunization | Status | Influenza | Completed |
| Allergies | Allergy | Reaction | Penicillin | Hives |
| Procedures | Procedure | Outcome | Appendectomy | — |
| Encounters | Encounter | Type | Hospital admission | — |
| Demographics | Demographic | Value | Phone number | — |

Always capture QE / Source / MRN regardless of screen (per §3/§4).

## 7. Copy-a-Data-ID from a row (Direction B helper)

- Every data row on screen gets a subtle copy affordance (shown on row hover).
- Clicking it composes a **Data ID** and copies it to the clipboard, e.g.
  `PDR|mrn=224906|qe=HEALTHIX|src=MSSM|Glucose [Mass/volume] in Blood | 96.74 | mg/dL | 03/12/2016`
  and keeps it as "last copied" in memory.
- The user pastes it into Direction B's **Data ID** field (or clicks "Use last
  copied Data ID").
- Clipboard uses the browser Clipboard API (needs HTTPS). The in-memory
  "last copied" fallback must work even when the OS clipboard is unavailable
  (e.g. opened via `file://`).

## 8. Dismissal

The modal must be dismissable without submitting, from any step:
- an **×** button in the header,
- the **Escape** key,
- a click on the backdrop/overlay.

## 9. Ticket JSON schema

One ticket per submission. Keys are stable and flat (nested only for
`patient` and `mrnArray`) so downstream SQL is simple.

Common keys (all tickets):
- `ticket` (string) — short id, e.g. `BUG-696916`
- `direction` (enum) — `QE_HAS__PDR_MISSING` | `PDR_HAS__QE_MISSING`
- `patient` — `{ first, last, dob }`
- `screen` (string) — `"<First> - <Section>"`
- `reportDate` (string) — local date the report was made
- `mrnArray` — `[ { qe, source, mrn }, ... ]`
- `notes` (string)
- `createdAt` (string, ISO-8601 UTC)

Direction A (`QE_HAS__PDR_MISSING`) adds:
- `qeThatHasIt` (string, may be empty), `source` (string), `mrn` (string)
- `dataType` (string — the adaptive label, e.g. `Lab`)
- `item` (string), `date` (string), `result` (string)

Direction B (`PDR_HAS__QE_MISSING`) adds:
- `qeMissingIt` (string), `source` (string), `mrn` (string) — pre-filled
- `dataId` (string — pasted from the row)

## 10. Storage requirement — S3 (secure) + Athena

The current demo only *shows* the JSON. The real build **must persist each
ticket to S3** so Athena can report on them.

**Format — single-line JSON, NO indentation.**
- Serialize with no pretty-printing / no indent (`json.dumps(obj)` /
  `JSON.stringify(obj)` with no spacing args). One ticket = one JSON object on a
  single line. This is mandatory: Athena's JSON SerDe reads **one JSON record
  per line**; indented/multi-line JSON will not parse.
- Write one compact object per S3 object (a single-line file), or append
  one-object-per-line into NDJSON roll-ups — either is Athena-readable.

**Layout — partitioned for Athena.**
```
s3://<secure-tickets-bucket>/tickets/dt=YYYY-MM-DD/<ticket>.json
```
Partitioning by `dt` keeps scans cheap. (`reportDate`/`createdAt` also live
inside the record.)

**Secure bucket — requirements.**
- A dedicated bucket, **separate from any public/synthetic-data bucket**.
- **Block Public Access = ON** (all four settings).
- **Default encryption at rest** (SSE-S3 minimum; SSE-KMS preferred).
- Bucket policy **denying non-TLS** access (`aws:SecureTransport = false`).
- **Versioning on**; lifecycle to expire/transition as policy dictates.
- Least-privilege IAM: the writer may only `s3:PutObject` to
  `tickets/*`; the Athena/Glue reader only `s3:GetObject`/`ListBucket`.

**Do NOT write from the browser.** A static site cannot hold AWS credentials
safely. Add a thin backend:
- `POST /tickets` → **API Gateway** → **Lambda** (role scoped to `PutObject` on
  the tickets bucket only).
- The browser `fetch`es the finished ticket object to that endpoint; the Lambda
  validates and writes the compact JSON to the partitioned key.
- Keep the in-page confirmation ("ticket captured") but have it reflect the real
  PUT result/key.

**Athena.**
- External table over `s3://<bucket>/tickets/` using a JSON SerDe
  (`org.openx.data.jsonserde.JsonSerDe`), partitioned by `dt`.
- Suggested columns: `ticket string, direction string,
  patient struct<first:string,last:string,dob:string>, screen string,
  qethathasit string, qemissingit string, source string, mrn string,
  datatype string, item string, date string, result string, dataid string,
  mrnarray array<struct<qe:string,source:string,mrn:string>>, notes string,
  reportdate string, createdat string`.
- Add partitions via `MSCK REPAIR TABLE` or partition projection on `dt`.
- Enables reports like: tickets by direction, by QE, by screen/dataType, by day;
  most-reported missing elements; QE-vs-PDR gap counts.

## 11. Acceptance criteria

- [ ] "⚠ Missing data" button on every patient view (both styles).
- [ ] Step 1 offers the two directions; `direction` recorded.
- [ ] Direction A does **not** pre-fill QE/Source/MRN (editable, "if known").
- [ ] Direction B **pre-fills** QE/Source/MRN read-only and names the QE in the heading.
- [ ] Item/Result labels, placeholders, and notes prompt adapt to the screen (§6).
- [ ] Each row exposes a copy-able Data ID; Direction B can paste it / reuse last.
- [ ] Every ticket includes `reportDate` and `mrnArray` (read-only), both directions.
- [ ] Modal closes via ×, Escape, and backdrop click without submitting.
- [ ] On submit, the ticket is written to the secure S3 bucket as **single-line,
      no-indent JSON** under a `dt=`-partitioned key via the backend Lambda.
- [ ] An Athena table can query the tickets and produce reports.

## 12. Reference implementation (current demo)

In this repo the feature is a self-contained, injectable widget:
- `bug_widget.py` — builds the button, modal (all steps), per-row copy icons,
  and the client JS; `inject(html)` splices it into a finished page via string
  replacement (so page f-string brace escaping is irrelevant).
- The renderers (`build_smart.py`, `build_chart.py`) stamp each patient block
  with `data-first/last/dob/qe/source/mrn/mrns`, which the widget reads.
- The demo currently renders the compact ticket JSON on screen instead of
  PUTting it to S3 — §10 is the remaining work to productionize.
