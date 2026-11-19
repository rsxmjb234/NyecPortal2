# 02 – Data Processing (requirements for ALL QEs)

Every QE view is a different presentation of the same processing pipeline. Nothing in this document is QE-specific. If a QE needs something different, it is in `qe/<name>.md`.

Reference implementation: `ccda_parse.py` (functions `parse_ccd`, `load_oru_hl7`, `_reconcile_oru`, `_dedup_person`, `merge_by_person`).

Pipeline:

```
 C-CDA XML  ─┐                                   ┌─> QE view (Hixny / HEALTHeLINK / Bronx / ...)
 HL7 ORU    ─┼─> parse ─> identify person ─> merge ─> de-duplicate ─> reconcile labs ─> display + drill-in
 MPI / IDs  ─┘
```

## 1. Inputs

| Input | Format | Demo location |
|-------|--------|---------------|
| Clinical documents | C-CDA (CCD) XML, one document per source per person | `demo-marcus/ccda/*.xml` |
| Lab results | HL7 v2.5.1 `ORU^R01`, one message file per source | `demo-marcus/oru-hl7/*_ORU.hl7` |
| Identity anchors | MPI CSV: `qe,source,mrn,eid,mpid,first_name,last_name,dob,gender` | `demo-marcus/mpi/marcus_mpi.csv` |

Requirements:
- Parsing **must** tolerate missing sections and missing optional fields. A missing section produces an empty section ("No X on file"), never an error page.
- A document that cannot be parsed **must not** block the other documents for that person. Record the failure (file, reason) for operations. **[Prod]**
- Unknown or unmapped codes **must** still display the best available text (display name, then original text, then the raw code).

## 2. Person identity and MRNs

### 2.1 Identifiers in a C-CDA (`recordTarget/patientRole/id`)

| Identifier | How to recognize it | Use |
|------------|--------------------|-----|
| Source MRN | `id` with `assigningAuthorityName="QE\|Source"`; `extension` = MRN | One entry in the MRN array |
| MPID | `id` whose `root` ends in `.mpid` | **Cross-source person key** |
| EID | `id` whose `root` ends in `.eid` | QE's own ID, kept for reference |

The first source MRN found is the document's primary MRN.

### 2.2 Identifiers in an HL7 ORU (`PID-3`, repeating, `~` separated)

```
340474^^^HEALTHIX&MSSM^MR ~ HX-EID-1234^^^HEALTHIX^PI ~ MARCUS-GOLDEN-0001^^^NYEC^PI
```

First repetition is the source MRN. Component 4 is `QE&Source`. Also read PID-5 (name), PID-7 (DOB), PID-8 (sex), PID-11 (address).

### 2.3 Matching rules

1. **Person key** = MPID when present. Fallback = `family|given|DOB`.
2. All documents with the same person key merge into **one virtual record**.
3. An ORU attaches to the document whose source MRN equals the ORU's PID-3 MRN.
   - The demo matches on MRN alone. **Production must match on the full triple (QE, Source, MRN)**, because two sources can issue the same MRN value.
4. **MRN array** = union of every `(QE, Source, MRN)` from CCDs and ORUs, de-duplicated on the triple. It drives the MRN Array button and is stamped on every Missing data ticket.

Requirements:
- **Must** show how many sources contributed and list them (MRN Array).
- **Should** surface a warning when two documents share an MPID but disagree on DOB or sex. Do not merge silently. **[Prod]**
- **[Prod]** Matching confidence and merge decisions **must** be auditable.

## 3. Merge and de-duplication by data type

After grouping by person, concatenate each data type across documents, then collapse duplicates using the key below. The first occurrence wins. **De-duplication hides duplicates in the merged view only. Never delete the source record.** Keep the raw documents and be able to show which sources contributed each item. **[Prod]**

| Data type | C-CDA section (title) | Fields extracted | De-dup key |
|-----------|----------------------|------------------|-----------|
| Conditions | `Problems` | name (SNOMED display), onset, resolved, status | (name, onset) |
| Medications | `Medications` | name (RxNorm), start, stop, status, dose, route, frequency, prescriber, refills, indication, RxNorm code | (name, start) |
| Lab results | `Diagnostic Results` | panel, test, value, unit, flag, reference range, date, LOINC, status | panel: (panel, date); result: (LOINC, date, value) |
| Lab results (ORU) | HL7 OBX | test, value, unit, range, flag, date, LOINC | (LOINC, date, value) |
| Immunizations | `Immunizations` | name, date | (name, date) |
| Vital signs | `Vital Signs` | test, value, unit, date | (test, value, date) |
| Procedures | `Surgeries`, else `Procedures` | name, date | (name, date) |
| Encounters / ADT | `Encounters` | type, facility, admit, discharge, attending, PCP, disposition, reason | (type, admit date) |
| Allergies | `Allergies` | substance | (substance) |

Known gaps to fix in the production build:
- **Encounter key** (type, admit date) can wrongly merge two same-day encounters at different facilities. **Should** add facility.
- **Medication key** (name, start) can merge the same drug started the same day at two doses. **Should** add dose.
- Sorting in the demo is done on the formatted `MM/DD/YYYY` string, which orders incorrectly across years. **Must** sort on real date values, newest first for encounters, immunizations and procedures.

## 4. Lab de-duplication (CCD vs ORU) – the core rule

The same lab can arrive twice: once inside a CCD and once as an ORU message. The viewer **must** reconcile them.

| Step | Rule |
|------|------|
| 1 | Build a set of CCD result keys `(LOINC, date)`. |
| 2 | For each ORU result, if `(LOINC, date)` is in the CCD set, mark the ORU result **duplicate = true** and display it as **preferred**. Otherwise display it as **new**. |
| 3 | For each CCD result whose `(LOINC, date)` exists in the ORU set, mark it **superseded**. Show it **crossed off (strikethrough) with a "superseded by ORU" tag. Never delete it.** |
| 4 | ORU results are shown in their own group at the top ("Laboratory Feed · ORU"), with a count. CCD results are grouped by panel and panel date below it. |
| 5 | Each lab row carries a source badge: **CCD** or **ORU**. A legend explains the badges and the strikethrough. |

Rule reasons: the ORU is the live lab-system message and is treated as authoritative. The CCD copy stays visible for audit.

Open item for product owner: the demo matches on LOINC + date only and does not compare values. **Should** flag a **conflict** when the key matches but the value or unit differs, instead of marking it a plain duplicate.

### Expected result for the demo patient (use as a test)

- CCD panel "Basic metabolic panel" dated 2025-03-15 on every document: Glucose 81.78 mg/dL, Creatinine 1.01 mg/dL, Sodium 141.78 mmol/L.
- Every ORU repeats those three plus **Hemoglobin A1c 6.1 %, flag High, ORU-only**.
- After merge: the three BMP results show as ORU **preferred** with the CCD copies **crossed off**. HbA1c shows as ORU **new**, abnormal.

## 5. Lab flags

| Source | Value | Display |
|--------|-------|---------|
| CCD `interpretationCode` | N, L, H, A, HH, LL | Normal, Low, High, Abnormal, Critical High, Critical Low |
| HL7 OBX-8 | same codes | same labels |

Low, High, Abnormal, Critical High and Critical Low are **abnormal**. Abnormal results **must** be visually distinct (red value; QE styles may add a left bar or tag).

## 6. Dates

- HL7/CDA timestamps arrive as `YYYYMMDD`, `YYYYMMDDHHMM` or `YYYYMMDDHHMMSS`. Accept all three.
- Demo displays `MM/DD/YYYY`. **[Prod]** Store ISO-8601 with timezone, display per the QE's convention, and sort on the stored value.
- An open-ended medication or problem (no stop/resolved date) is **Active**. A stop/resolved date makes it **Completed/Resolved**.

## 7. Terminology

| Domain | Code system |
|--------|-------------|
| Conditions, reasons, procedures | SNOMED CT (`2.16.840.1.113883.6.96`) |
| Medications | RxNorm (`2.16.840.1.113883.6.88`) |
| Labs, vitals | LOINC (`2.16.840.1.113883.6.1`) |
| Discharge disposition | HL7 Discharge Disposition (`2.16.840.1.113883.12.112`) via `sdtc:dischargeDispositionCode` |
| Provider type | NUCC taxonomy (`2.16.840.1.113883.6.101`) |
| Route | NCI Thesaurus (`2.16.840.1.113883.3.26.1.1`) |

Display text resolution order for any coded value: `displayName`, then `translation/displayName`, then the referenced narrative text (`originalText/reference`), then the raw code.

## 8. Encounters / ADT encoding

| Field | C-CDA location |
|-------|----------------|
| Type | `encounter/code` |
| Admit / discharge | `encounter/effectiveTime` low / high (no high = outpatient or open) |
| Facility | `encounter/participant[@typeCode='LOC']/participantRole/playingEntity/name` |
| Attending | `encounter/performer[1]/assignedEntity/assignedPerson/name` |
| PCP | `encounter/performer[2]/assignedEntity/assignedPerson/name` |
| Discharge disposition | `sdtc:dischargeDispositionCode/@displayName` |
| Reason for visit | `encounter/entryRelationship/observation/value/@displayName` |

The performer order (first attending, second PCP) is a demo convention. **[Prod]** Use `assignedEntity/code` (NUCC) to identify the role rather than position.

## 9. Drill-in detail (every QE)

Requirement from the product owner: **if more data exists than is shown in the row, the provider can click in and see it.**

- Clicking any data row **must** open a detail panel showing every field available for that record, not only the visible columns.
- Panel header shows the patient (name, DOB) and the QE|Source MRN the view represents.
- Fields with no value **must** be omitted, not shown blank.
- Group header rows and copy icons do not open the panel.
- Escape, the close button, or a click outside closes the panel.

Extra fields per type (beyond the visible columns), implemented in the demo:

| Type | Extra fields in detail |
|------|------------------------|
| Encounter / ADT | Facility, attending, PCP, discharge disposition, reason for visit, encounter type |
| Medication | Instructions (built sig), indication, dose, route, frequency, prescriber, refills, RxNorm code, record status |
| CCD lab | LOINC code, panel, result status, source document |
| ORU lab | LOINC code, source feed (HL7 v2 ORU^R01), duplicate-of-CCD yes/no |
| Others | Visible columns only (conditions, immunizations, procedures, vitals not yet enriched) |

## 10. Provenance and the Data ID

- Every displayed item **must** be traceable to its source (QE, Source, MRN, document or message ID, received date). **[Prod]** The demo tracks QE, Source and MRN only per view.
- The Missing data feature's "copy Data ID" produces `PDR|mrn=..|qe=..|src=..|<row text>`. In the demo this is built from the row text. **[Prod]** Replace it with a **stable record ID** (a persistent key per merged item), so a ticket still points at the right record after the data refreshes.

## 11. Empty and partial data

- Section with no data: the QE's own empty-state text (for example "No problems on file.").
- Navigation shows which sections have data (Fusion marks them in blue; others disable empty ones).
- A section **must** show a count when the QE style has one.

## 12. Security, privacy and audit [Prod]

The demo has none of these. All are required in the secure portal. Details come from the security team and from each QE's policy.

- Authentication and authorization, with per-user QE entitlements.
- Patient consent and consent-based visibility (HEALTHeLINK Fusion gates search results on consent).
- Break-the-glass access with a reason, and access audit logging of who viewed which patient and when.
- Encryption in transit and at rest. No PHI in logs or URLs.
- Missing data tickets stored in a dedicated secure bucket (see [03-missing-data-logging.md](03-missing-data-logging.md), section 12).

## 13. Acceptance test: Marcus Evans

Use the sample bundle. After processing, every QE view **must** show:

| Check | Expected |
|-------|----------|
| People | 1 (Marcus Evans, DOB 06/01/1950, M) |
| MRN array | 10 entries, one per source, no duplicates |
| Conditions | 5: type 2 diabetes, hypertension, hyperlipidemia, CKD stage 3, osteoarthritis |
| Medications | 10 after merge (each source holds a 7-10 subset) |
| Encounters / ADT | 5, newest first, each with facility, attending, PCP and reason; inpatient and ED stays also have a disposition |
| Labs | 840 CCD results after de-dup, plus the ORU group |
| BMP duplicates | Glucose, creatinine, sodium: ORU preferred, CCD crossed off |
| HbA1c 6.1 % | ORU only, flagged High |
| Drill-in | Opens for encounter, medication, CCD lab and ORU lab rows with the extra fields in section 9 |
