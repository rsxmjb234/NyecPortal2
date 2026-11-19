# SHIN-NY Community Health Record (PDR) – Developer Specification

Audience: the developer building this inside the secure portal.
Source of truth for behavior: the working demo (below) plus these documents.
All demo data is 100% synthetic.

## Reading order

| # | File | What it covers |
|---|------|----------------|
| 1 | [01-home-page.md](01-home-page.md) | Home page, one card per Qualified Entity (QE), and what each QE card must do |
| 2 | [02-data-processing.md](02-data-processing.md) | Requirements that apply to **every** QE: how each data type is ingested, normalized, merged, de-duplicated and displayed |
| 3 | [03-missing-data-logging.md](03-missing-data-logging.md) | "Missing data" ticket feature + MRN Array (full build spec with screenshots) |
| 4 | [qe/](qe/) | One file per QE with QE-specific needs |

QE files: [Hixny](qe/hixny.md) · [HEALTHeLINK](qe/healthelink.md) · [Bronx RHIO](qe/bronx-rhio.md) ·
[Healthix](qe/healthix.md) · [HealtheConnections](qe/healtheconnections.md) · [Rochester RHIO](qe/rochester-rhio.md)

## Terms

| Term | Meaning |
|------|---------|
| PDR | The portal being built (the record viewer that merges data for a person). |
| QE | Qualified Entity: a regional SHIN-NY health information exchange (Hixny, HEALTHeLINK, Bronx RHIO, ...). |
| Source | A contributing organization inside a QE (hospital, practice). Identified as `QE\|Source`. |
| MRN | Medical record number assigned by a source. One person has many MRNs. |
| MPID | Cross-QE person key shared by all of a person's records (demo: `MARCUS-GOLDEN-0001`). |
| EID | A QE's own enterprise ID for the person. |
| CCD / C-CDA | XML clinical document (problems, meds, labs, encounters, ...). |
| ORU | HL7 v2.5.1 `ORU^R01` lab result message. |
| ADT | Admit / Discharge / Transfer events (shown as Encounters). |
| Virtual record | The single merged view of one person built from every source. |

## Requirement language

"**Must**" = required. "**Should**" = expected unless there is a reason not to.
Each requirement is tagged where it matters:

- **[Demo]** behavior already implemented and visible in the demo.
- **[Prod]** requirement for the secure portal that the demo does not implement (for example authentication, consent, audit). These are listed so they are not missed. Confirm detail with the product owner and each QE.

## The demo (reference implementation)

- Live: https://main.d3pz3oj6iuj9t4.amplifyapp.com
- Code: https://github.com/rsxmjb234/NyecPortal2
- One synthetic patient, **Marcus Evans** (DOB 06/01/1950, M), appears in 10 sources across 5 QEs, rendered in three QE styles from the same merged data.

| File | Role |
|------|------|
| `make_person.py` | Generates the Marcus bundle (10 CCDs, 10 HL7 ORUs, MPI CSV) |
| `ccda_parse.py` | **Shared parser + merge + de-dup rules** (the logic in doc 02) |
| `build_smart.py` / `build_chart.py` / `build_bronx.py` | Hixny, HEALTHeLINK, Bronx RHIO renderers |
| `bug_widget.py` | Missing data, MRN Array and drill-in detail widget |
| `build_home.py` | Home page + orchestration |

The demo is static HTML generated at build time. The secure portal will be dynamic.
Treat the demo as the behavioral reference and these documents as the requirements. Do not copy the static-HTML approach.

## Sample data

`s3://nyec-synthetic-data/demo-marcus/` (ccda/, oru-hl7/, mpi/marcus_mpi.csv, README.md). Contains the 10 CCDs and 10 HL7 ORU files used for every example in these documents.
