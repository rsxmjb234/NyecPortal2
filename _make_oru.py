"""Generate 5 synthetic ORU (FHIR Observation) labs for Marcus (BRONX-MPID-000003),
matching the schema used in s3://nyec-synthetic-data/synthetic-oru/.
3 are obvious duplicates of his 2025-03-15 CCD labs; 2 are new tests."""
import json

EID = "3"              # synthetic enterprise id -> MPID-000003
QE = "421099"          # synthetic HEALTHIX QE id
MPID = "BRONX-MPID-000003"
WHEN_DUP = "2025-03-15T10:05:00+00:00"   # same day as CCD panel
WHEN_NEW = "2025-03-15T10:07:00+00:00"


def obs(oid, loinc, display, text, value, unit, when):
    return {
        "resourceType": "Observation",
        "id": oid,
        "status": "final",
        "category": [{"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
            "code": "laboratory", "display": "Laboratory"}]}],
        "code": {"coding": [{"system": "http://loinc.org", "code": loinc,
                             "display": display}], "text": text},
        "subject": {"identifier": [
            {"system": "urn:nyec:synthetic:eid", "value": EID},
            {"system": "urn:nyec:synthetic:qe:HEALTHIX", "value": QE},
            {"system": "urn:nyec:synthetic:mpid", "value": MPID}]},
        "effectiveDateTime": when,
        "valueQuantity": {"value": value, "unit": unit,
                          "system": "http://unitsofmeasure.org", "code": unit},
    }


records = [
    # --- 3 obvious duplicates of the 2025-03-15 CCD basic metabolic panel ---
    obs("obs-3-HEALTHIX-20250315-0001", "2339-0", "Glucose [Mass/volume] in Blood",
        "Glucose", 81.78, "mg/dL", WHEN_DUP),
    obs("obs-3-HEALTHIX-20250315-0002", "38483-4", "Creatinine [Mass/volume] in Blood",
        "Creatinine", 1.01, "mg/dL", WHEN_DUP),
    obs("obs-3-HEALTHIX-20250315-0003", "2947-0", "Sodium [Moles/volume] in Blood",
        "Sodium", 141.78, "mmol/L", WHEN_DUP),
    # --- 2 new tests not present in the CCD ---
    obs("obs-3-HEALTHIX-20250315-0004", "4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood",
        "Hemoglobin A1c", 6.1, "%", WHEN_NEW),
    obs("obs-3-HEALTHIX-20250315-0005", "3016-3", "Thyrotropin [Units/volume] in Serum or Plasma",
        "TSH", 2.1, "mIU/L", WHEN_NEW),
]

with open("marcus_oru.ndjson", "w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r) + "\n")

print(f"Wrote marcus_oru.ndjson with {len(records)} Observations")
for r in records:
    print(f"  {r['code']['coding'][0]['code']:8} {r['code']['text']:16} "
          f"{r['valueQuantity']['value']} {r['valueQuantity']['unit']}  {r['effectiveDateTime'][:10]}")
