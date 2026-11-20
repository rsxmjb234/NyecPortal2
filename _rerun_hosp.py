"""Re-run hospital query with DISTINCT, merge ADT, save. Delete when done."""
import json, re, sys
from collections import defaultdict, Counter
sys.path.insert(0, '.')
from athena_hello_world import athena_query

with open('SQLExamples/reportonhospitals.sql') as f:
    sql = re.sub(r'/\*[\s\S]*?\*/', '', f.read()).strip().rstrip(';').strip()

print('EXPLAIN...', flush=True)
athena_query('EXPLAIN ' + sql)
print('  OK')

print('Running...', flush=True)
rows, scanned = athena_query(sql)
gb = scanned / 1024**3
print(f'Scanned: {gb:.3f} GB  ({len(rows)} rows)')

# Merge ADT from lookup
QE_MAP = {
    'healthix': 'Healthix', 'healtheconnections': 'HealtheConnections',
    'hixny': 'Hixny', 'healthelink': 'HEALTHeLINK', 'bronx': 'Bronx RHIO',
    'rochester': 'Rochester RHIO',
}
with open('SQLExamples/reportonadt.json') as f:
    adt_raw = json.load(f)
adt_by_qe_aa = defaultdict(int)
adt_by_aa = defaultdict(int)
for r in adt_raw['rows']:
    qe_label = QE_MAP.get(r['qe'], r['qe'])
    aa = r['assigning_authority'].upper().strip()
    adt_by_qe_aa[(qe_label, aa)] += int(r['adt_count'])
    adt_by_aa[aa] += int(r['adt_count'])

for r in rows:
    qe = r['qe_name']
    aa = r['assigning_authority'].upper().strip()
    adt = adt_by_qe_aa.get((qe, aa), adt_by_aa.get(aa, 0))
    r['adt_count'] = str(adt)
    r['total_docs'] = str(int(r['ccd_count']) + int(r['trn_count']) + int(r['lab_count']) + adt)

# Check dedup worked
key_counts = Counter(
    (r['qe_name'], r['assigning_authority'], r['organization_name'], r['nys_facility_id'])
    for r in rows
)
dupes = {k: v for k, v in key_counts.items() if v > 1}
print(f'Duplicate (qe,aa,org,fid) remaining: {len(dupes)}')

# Count facility 207
rows_207 = [r for r in rows if r.get('nys_facility_id') == '207']
print(f'Facility #207 rows: {len(rows_207)}')

with open('SQLExamples/reportonhospitals.json', 'w') as f:
    json.dump({'scanned_bytes': scanned, 'scanned_gb': round(gb, 4),
               'row_count': len(rows), 'rows': rows}, f, indent=2)
print(f'Saved ({len(rows)} rows)')
