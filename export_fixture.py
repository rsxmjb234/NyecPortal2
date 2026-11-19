"""Export the merged Marcus record as a canonical JSON fixture for the developer spec.

Writes developer-spec/fixtures/marcus_evans.json (full) and
marcus_evans.sample.json (3 items per type, for embedding in docs).
Derived fields (dup, superseded) are removed: the viewer computes them.
"""
import glob
import json
import os

import ccda_parse as c

CCD = sorted(glob.glob('marcus_bundle/ccda/*.xml'))
ORU = os.path.join('marcus_bundle', 'oru-hl7', '*.hl7')

pts = [c.parse_ccd(f) for f in CCD]
c.load_oru_hl7(pts, ORU)
P = c.merge_by_person(pts)[0]

KEEP = ['given', 'family', 'gender', 'dob', 'age', 'addr', 'race', 'eth', 'lang',
        'person_key', 'mrn_list', 'problems', 'meds', 'labs', 'imms', 'vitals',
        'procs', 'encs', 'allergies', 'oru']
out = {k: P.get(k) for k in KEEP}
out['person_key'] = P['person_key']
out['mpid'] = P['person_key']
del out['person_key']
for lab in out['labs']:
    for comp in lab['comps']:
        comp.pop('superseded', None)
        comp.pop('source', None)
for o in out['oru']:
    o.pop('dup', None)
for e in out['encs']:
    e.pop('details', None)

os.makedirs('developer-spec/fixtures', exist_ok=True)
with open('developer-spec/fixtures/marcus_evans.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

# sample: 3 items per list, 2 lab panels x 3 components, plus the BMP + A1c
sample = dict(out)
for k in ('problems', 'meds', 'imms', 'vitals', 'procs', 'encs', 'allergies'):
    sample[k] = out[k][:3]
bmp = [p for p in out['labs'] if p['panel'].startswith('Basic metabolic panel')
       and p['date'] == '03/15/2025'][:1]
other = [p for p in out['labs'] if p not in bmp][:1]
sample['labs'] = [dict(p, comps=p['comps'][:3]) for p in other] + bmp
sample['oru'] = [o for o in out['oru'] if o['date'] == '03/15/2025'][:4]
sample['mrn_list'] = out['mrn_list'][:3]
with open('developer-spec/fixtures/marcus_evans.sample.json', 'w', encoding='utf-8') as f:
    json.dump(sample, f, indent=1, ensure_ascii=False)

print('counts:', {k: (len(v) if isinstance(v, list) else v) for k, v in out.items()
                  if isinstance(v, list)})
print('bytes full:', os.path.getsize('developer-spec/fixtures/marcus_evans.json'))
