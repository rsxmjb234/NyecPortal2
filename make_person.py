"""
make_person.py  -  build one synthetic PERSON who exists across many SHIN-NY QE
sources. MVP target = Marcus Evans.

Approach (demo-pragmatic):
  * Start from a Synthea-generated C-CDA (all "Synthea parameters" identical,
    because every output derives from the SAME base record -> same conditions,
    same clinical dates, same everything).
  * Clone it N times; on each copy rewrite only the IDENTITY (name, DOB, sex,
    address) to the person, and the SOURCE identity (QE|Source assigning
    authority + a distinct MRN), plus a per-QE EID and one shared MPID.
  * Age is identical on every copy because the DOB is fixed.
  * Region + conditions are identical because the clinical body is untouched.
  * Emit a matching genuine HL7 v2.5.1 ORU^R01 per source, time-aligned to the
    CCD's 2025-03-15 basic metabolic panel so the portal can de-duplicate.

Output -> ./marcus_bundle  (ccda/, oru-hl7/, mpi/, README.md) for upload to S3.
"""
import os
import glob
import random
import xml.etree.ElementTree as ET

V3 = 'urn:hl7-org:v3'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'
ns = {'v3': V3}
OUT = 'marcus_bundle'
N_CCDS = 10
random.seed(777)

ET.register_namespace('', V3)
ET.register_namespace('sdtc', 'urn:hl7-org:sdtc')
ET.register_namespace('xsi', XSI)

# ---- the PERSON (MVP: Marcus) ----
PERSON = {
    'first': 'Marcus', 'last': 'Evans', 'dob': '19500601', 'sex': 'M',
    'addr': ('179 Bednar Knoll Suite 2', 'Bronx', 'NY', '10467'),
    'mpid': 'MARCUS-GOLDEN-0001',
}

# A Synthea-generated C-CDA to use as the identical clinical base for every copy.
BASE_CCD = 'ccds/BRONX-MPID-000003_Lessie363_Cartwright189_3d8cfae0-76e6-8b05-3421-f81320276a38.xml'

# 10 real-ish SHIN-NY (QE, Source) pairs; MRNs assigned below (random, distinct).
SOURCES = [
    ('HEALTHIX', 'MSSM'), ('HEALTHIX', 'NYP'),
    ('HEALTHELINK', 'KINGSB'), ('HEALTHELINK', 'ECMC'),
    ('HIXNY', 'SPLPCPRIME'), ('HIXNY', 'ALBMC'),
    ('GRRHIO', 'UR1244'), ('GRRHIO', 'RGH'),
    ('BRONX', 'BXLEB'), ('HEALTHECONN', 'UHS'),
][:N_CCDS]

DOC_TIME = '20250315120000'   # all authored around the same time

# ORU basic metabolic panel aligned to the base CCD's 2025-03-15 panel (drives dedup)
LAB_DT = '20250315103000'
ORU_ROWS = [
    ('2339-0', 'Glucose', '81.78', 'mg/dL', '70-99', 'N'),         # dup of CCD
    ('38483-4', 'Creatinine', '1.01', 'mg/dL', '0.70-1.30', 'N'),  # dup of CCD
    ('2947-0', 'Sodium', '141.78', 'mmol/L', '136-145', 'N'),      # dup of CCD
    ('4548-4', 'Hemoglobin A1c', '6.1', '%', '4.0-5.6', 'H'),      # ORU-only, abnormal
]


def q(t):
    return f'{{{V3}}}{t}'


def make_ccd(qe, source, mrn, eid):
    tree = ET.parse(BASE_CCD)
    root = tree.getroot()

    de = root.find('v3:effectiveTime', ns)
    if de is not None:
        de.set('value', DOC_TIME)

    pr = root.find('.//v3:recordTarget/v3:patientRole', ns)
    ids = pr.findall('v3:id', ns)
    if ids:
        ids[0].set('extension', mrn)
        ids[0].set('assigningAuthorityName', f'{qe}|{source}')
    eid_el = ET.Element(q('id'), {'root': '2.16.840.1.113883.3.9999.eid',
                                  'extension': eid, 'assigningAuthorityName': qe})
    mpid_el = ET.Element(q('id'), {'root': '2.16.840.1.113883.3.9999.mpid',
                                   'extension': PERSON['mpid']})
    pos = (list(pr).index(ids[-1]) + 1) if ids else 0
    pr.insert(pos, mpid_el)
    pr.insert(pos, eid_el)

    addr = pr.find('v3:addr', ns)
    if addr is not None:
        for tag, val in zip(('streetAddressLine', 'city', 'state', 'postalCode'), PERSON['addr']):
            el = addr.find(f'v3:{tag}', ns)
            if el is None:
                el = ET.SubElement(addr, q(tag))
            el.text = val

    pat = pr.find('v3:patient', ns)
    nm = pat.find('v3:name', ns)
    for extra in nm.findall('v3:given', ns)[1:]:
        nm.remove(extra)
    for extra in nm.findall('v3:family', ns)[1:]:
        nm.remove(extra)
    gv = nm.find('v3:given', ns) if nm.find('v3:given', ns) is not None else ET.SubElement(nm, q('given'))
    gv.text = PERSON['first']
    fam = nm.find('v3:family', ns) if nm.find('v3:family', ns) is not None else ET.SubElement(nm, q('family'))
    fam.text = PERSON['last']
    g = pat.find('v3:administrativeGenderCode', ns)
    if g is not None:
        g.set('code', PERSON['sex'])
    bt = pat.find('v3:birthTime', ns)
    if bt is not None:
        bt.set('value', PERSON['dob'])

    return "<?xml version='1.0' encoding='UTF-8'?>\n" + ET.tostring(root, encoding='unicode')


def make_oru(qe, source, mrn, eid, msgid):
    addr = f"{PERSON['addr'][0]}^^{PERSON['addr'][1]}^{PERSON['addr'][2]}^{PERSON['addr'][3]}"
    pid3 = f'{mrn}^^^{qe}&{source}^MR~{eid}^^^{qe}^PI~{PERSON["mpid"]}^^^NYEC^PI'
    seg = [
        '|'.join(['MSH', '^~\\&', f'LAB_{qe}', source, 'SHINNY', 'NYS', LAB_DT, '',
                  'ORU^R01^ORU_R01', msgid, 'P', '2.5.1']),
        '|'.join(['PID', '1', '', pid3, '', f'{PERSON["last"]}^{PERSON["first"]}', '',
                  PERSON['dob'], PERSON['sex'], '', '', addr]),
        '|'.join(['PV1', '1', 'O', source]),
        '|'.join(['ORC', 'RE', f'ORD{msgid}', f'FIL{msgid}', '', '', '', '', '', LAB_DT]),
        '|'.join(['OBR', '1', f'ORD{msgid}', f'FIL{msgid}',
                  '51990-0^Basic metabolic panel^LN', '', LAB_DT, LAB_DT,
                  '', '', '', '', '', '', '', '', '', '', '', '', '', 'F']),
    ]
    for i, (code, name, val, unit, rng, flag) in enumerate(ORU_ROWS, 1):
        seg.append('|'.join(['OBX', str(i), 'NM', f'{code}^{name}^LN', '', val, unit,
                             rng, flag, '', '', 'F', '', '', LAB_DT]))
    return '\r'.join(seg) + '\r'


# ---- build bundle ----
for d in ('ccda', 'oru-hl7', 'mpi'):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
for old in glob.glob(os.path.join(OUT, '**', '*.*'), recursive=True):
    try:
        os.remove(old)
    except OSError:
        pass

rows = []
for i, (qe, source) in enumerate(SOURCES, 1):
    mrn = str(random.randint(100000, 999999))
    eid = f'{qe[:2].upper()}-EID-{random.randint(1000, 9999)}'
    stem = f'MARCUS_{qe}_{source}_{mrn}'
    with open(os.path.join(OUT, 'ccda', stem + '.xml'), 'w', encoding='utf-8') as f:
        f.write(make_ccd(qe, source, mrn, eid))
    with open(os.path.join(OUT, 'oru-hl7', stem + '_ORU.hl7'), 'w', encoding='utf-8', newline='') as f:
        f.write(make_oru(qe, source, mrn, eid, f'MSG{i:04d}'))
    rows.append((qe, source, mrn, eid))

with open(os.path.join(OUT, 'mpi', 'marcus_mpi.csv'), 'w', encoding='utf-8', newline='') as f:
    f.write('qe,source,mrn,eid,mpid,first_name,last_name,dob,gender\n')
    for qe, source, mrn, eid in rows:
        f.write(f'{qe},{source},{mrn},{eid},{PERSON["mpid"]},'
                f'{PERSON["first"]},{PERSON["last"]},{PERSON["dob"]},{PERSON["sex"]}\n')

readme = f"""# {PERSON['first']} {PERSON['last']} - one person across {N_CCDS} QE sources (synthetic)

A single synthetic PERSON present in {N_CCDS} SHIN-NY QE sources, so the portal
can match and de-duplicate across sources and show the full source|MRN set that
defines the person.

Identity (identical on every document):
  name: {PERSON['first']} {PERSON['last']}   DOB: {PERSON['dob'][:4]}-{PERSON['dob'][4:6]}-{PERSON['dob'][6:]}   sex: {PERSON['sex']}
  shared MPID: {PERSON['mpid']}
  address/region: {', '.join(PERSON['addr'])}

Source identities (QE|Source : MRN / EID) - all the SAME person:
""" + '\n'.join(f'  {qe}|{source} : mrn={mrn} eid={eid}' for qe, source, mrn, eid in rows) + f"""

How it was made
  * {N_CCDS} C-CDAs cloned from one Synthea-generated base record, so every copy
    has identical Synthea parameters: same conditions, same clinical dates,
    same age (DOB fixed), same region. Only the identity + source <id> differ.
  * {N_CCDS} genuine HL7 v2.5.1 ORU^R01 lab feeds, one per source, time-aligned
    to the 2025-03-15 basic metabolic panel. Each repeats Glucose/Creatinine/
    Sodium (duplicates of the CCD panel -> de-duplication) plus an ORU-only
    Hemoglobin A1c flagged High.

Files
  mpi/marcus_mpi.csv   one MPI anchor row per source (qe, source, mrn, eid, mpid, name, dob, sex)
  ccda/*.xml           {N_CCDS} C-CDAs (same person, {N_CCDS} sources)
  oru-hl7/*_ORU.hl7    {N_CCDS} genuine HL7 ORU feeds

All data is 100% synthetic. Demonstration only.
"""
with open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8') as f:
    f.write(readme)

print(f'Wrote {OUT}: {N_CCDS} CCDs + {N_CCDS} ORUs for {PERSON["first"]} {PERSON["last"]}')
for qe, source, mrn, eid in rows:
    print(f'  {qe}|{source}  MRN={mrn}  EID={eid}')
