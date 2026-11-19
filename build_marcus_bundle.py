"""
Mint one self-consistent synthetic test person, "Marcus Evans", who exists
across 5 real SHIN-NY QE sources so he can be linked in the MPI, plus genuine
HL7 v2.5.1 ORU^R01 lab messages that overlap for de-duplication.

Outputs a self-contained bundle under ./marcus_bundle for upload to S3.

Identity model (matches the MPI-linkage notebook + Julie's note):
  - a source identity is (qe, source, mrn); assigning authority in the CCD is "QE|Source".
  - the cross-source keys are eid (per qe) and a shared mpid.
Clones the existing Synthea CCD (already named "Marcus Evans") 5 times, rewriting
name / DOB / gender and the source <id>, keeping the SAME conditions and labs so
the portal has real overlap to de-duplicate.
"""
import os
import copy
import xml.etree.ElementTree as ET

V3 = 'urn:hl7-org:v3'
ns = {'v3': V3}
BASE_CCD = 'ccds/BRONX-MPID-000003_Lessie363_Cartwright189_3d8cfae0-76e6-8b05-3421-f81320276a38.xml'
OUT = 'marcus_bundle'

# ---- Marcus golden identity ----
FIRST, LAST = 'Marcus', 'Evans'
DOB = '19500601'          # 1950-06-01
GENDER = 'M'
MPID = 'MARCUS-GOLDEN-0001'
ADDR = ('179 Bednar Knoll Suite 2', 'New York', 'NY', '11367')

# Each source: QE, Source(facility key), MRN at that source, EID in that QE.
# QE / source codes drawn from SHIN-NYOrgData.csv and test-patients.csv (real NY QEs).
SOURCES = [
    {'qe': 'HEALTHIX',    'source': 'MSSM',       'mrn': '700001', 'eid': 'HX-EID-0001'},
    {'qe': 'HEALTHELINK', 'source': 'KINGSB',     'mrn': '700002', 'eid': 'HL-EID-0001'},
    {'qe': 'HIXNY',       'source': 'SPLPCPRIME', 'mrn': '700003', 'eid': 'HN-EID-0001'},
    {'qe': 'GRRHIO',      'source': 'UR1244',     'mrn': '700004', 'eid': 'GR-EID-0001'},
    {'qe': 'BRONX',       'source': 'BXLEB',      'mrn': '700005', 'eid': 'BX-EID-0001'},
]

for pfx in ('', 'sdtc', 'xsi'):
    pass
ET.register_namespace('', V3)
ET.register_namespace('sdtc', 'urn:hl7-org:sdtc')
ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')


def q(t):
    return f'{{{V3}}}{t}'


def make_ccd(src):
    tree = ET.parse(BASE_CCD)
    root = tree.getroot()

    # document-level authored time -> common recent date (all "around the same time")
    de = root.find('v3:effectiveTime', ns)
    if de is not None:
        de.set('value', '20250315120000')

    pr = root.find('.//v3:recordTarget/v3:patientRole', ns)

    # rewrite the source <id>: QE|Source + MRN
    ids = pr.findall('v3:id', ns)
    if ids:
        ids[0].set('extension', src['mrn'])
        ids[0].set('assigningAuthorityName', f"{src['qe']}|{src['source']}")
    # add an EID id (per-QE enterprise id) and a shared MPID id
    eid_el = ET.SubElement(pr, q('id'))
    eid_el.set('root', '2.16.840.1.113883.3.9999.eid')
    eid_el.set('extension', src['eid'])
    eid_el.set('assigningAuthorityName', src['qe'])
    mpid_el = ET.SubElement(pr, q('id'))
    mpid_el.set('root', '2.16.840.1.113883.3.9999.mpid')
    mpid_el.set('extension', MPID)
    # keep SubElement order tidy: move the two new ids right after existing ids
    for e in (eid_el, mpid_el):
        pr.remove(e)
    insert_at = list(pr).index(ids[-1]) + 1 if ids else 0
    pr.insert(insert_at, mpid_el)
    pr.insert(insert_at, eid_el)

    # address
    addr = pr.find('v3:addr', ns)
    if addr is not None:
        for tag, val in zip(('streetAddressLine', 'city', 'state', 'postalCode'), ADDR):
            el = addr.find(f'v3:{tag}', ns)
            if el is None:
                el = ET.SubElement(addr, q(tag))
            el.text = val

    # name / gender / dob
    pat = pr.find('v3:patient', ns)
    nm = pat.find('v3:name', ns)
    givens = nm.findall('v3:given', ns)
    for extra in givens[1:]:
        nm.remove(extra)
    if givens:
        givens[0].text = FIRST
    else:
        ET.SubElement(nm, q('given')).text = FIRST
    fam = nm.find('v3:family', ns)
    if fam is None:
        fam = ET.SubElement(nm, q('family'))
    fam.text = LAST
    g = pat.find('v3:administrativeGenderCode', ns)
    if g is not None:
        g.set('code', GENDER)
    bt = pat.find('v3:birthTime', ns)
    if bt is not None:
        bt.set('value', DOB)

    return ET.tostring(root, encoding='unicode')


# ---------- HL7 v2.5.1 ORU^R01 ----------
def hl7(fields):
    return '|'.join(fields)


def oru_message(src, msgid, collected, obx_rows, order_dt=None):
    """Build a genuine HL7 v2.5.1 ORU^R01 message string (CR-separated segments)."""
    order_dt = order_dt or collected
    qe, fac, mrn = src['qe'], src['source'], src['mrn']
    seg = []
    seg.append(hl7(['MSH', '^~\\&', f'LAB_{qe}', fac, 'SHINNY', 'NYS',
                    collected, '', 'ORU^R01^ORU_R01', msgid, 'P', '2.5.1']))
    # PID-3: MRN^^^QE&Source^MR  (plus MPI/EID in a second rep)
    pid3 = f'{mrn}^^^{qe}&{fac}^MR~{src["eid"]}^^^{qe}^PI~{MPID}^^^NYEC^PI'
    addr = f'{ADDR[0]}^^{ADDR[1]}^{ADDR[2]}^{ADDR[3]}'
    seg.append(hl7(['PID', '1', '', pid3, '', f'{LAST}^{FIRST}', '', DOB, GENDER,
                    '', '', addr]))
    seg.append(hl7(['PV1', '1', 'O', f'{fac}']))
    seg.append(hl7(['ORC', 'RE', f'ORD{msgid}', f'FIL{msgid}', '', '', '', '', '',
                    order_dt]))
    # OBR: one panel (Basic metabolic panel)
    seg.append(hl7(['OBR', '1', f'ORD{msgid}', f'FIL{msgid}',
                    '51990-0^Basic metabolic panel^LN', '', order_dt, collected,
                    '', '', '', '', '', '', '', '', '', '', '', '', '', 'F']))
    for i, r in enumerate(obx_rows, 1):
        code, name, val, unit, rng, flag = r
        seg.append(hl7(['OBX', str(i), 'NM', f'{code}^{name}^LN', '', str(val),
                        unit, rng, flag, '', '', 'F', '', '', collected]))
    return '\r'.join(seg) + '\r'


# ---------- build ----------
os.makedirs(os.path.join(OUT, 'ccda'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'oru-hl7'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'mpi'), exist_ok=True)

ccd_files = []
for src in SOURCES:
    xml = make_ccd(src)
    fn = f"MARCUS_{src['qe']}_{src['source']}_{src['mrn']}.xml"
    path = os.path.join(OUT, 'ccda', fn)
    with open(path, 'w', encoding='utf-8') as f:
        f.write("<?xml version='1.0' encoding='UTF-8'?>\n" + xml)
    ccd_files.append(fn)

# ORU messages: overlap with the CCD 2025-03-15 basic metabolic panel so the
# portal can de-duplicate (Glucose appears in CCD + both ORU feeds).
#   (LOINC, name, value, unit, ref range, abnormal flag)
oru_a = oru_message(
    SOURCES[0], 'HX0001', '20250315103000',
    [('2339-0', 'Glucose', 81.78, 'mg/dL', '70-99', 'N'),       # dup of CCD
     ('38483-4', 'Creatinine', 1.01, 'mg/dL', '0.70-1.30', 'N'),  # dup of CCD
     ('2947-0', 'Sodium', 141.78, 'mmol/L', '136-145', 'N'),      # dup of CCD
     ('4548-4', 'Hemoglobin A1c', 6.1, '%', '4.0-5.6', 'H')])     # new, abnormal
oru_b = oru_message(
    SOURCES[3], 'GR0001', '20250315110000',
    [('2339-0', 'Glucose', 82.0, 'mg/dL', '70-99', 'N'),          # near-dup of CCD/ORU-A
     ('3016-3', 'TSH', 2.1, 'mIU/L', '0.40-4.50', 'N')])          # new

oru_files = []
for name, msg in [('MARCUS_HEALTHIX_MSSM_ORU.hl7', oru_a),
                  ('MARCUS_GRRHIO_UR1244_ORU.hl7', oru_b)]:
    path = os.path.join(OUT, 'oru-hl7', name)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(msg)
    oru_files.append(name)

# MPI rows (one per source) in the anchor schema the notebook/Athena uses.
mpi_path = os.path.join(OUT, 'mpi', 'marcus_mpi.csv')
with open(mpi_path, 'w', encoding='utf-8', newline='') as f:
    f.write('qe,source,mrn,eid,mpid,first_name,last_name,dob,gender\n')
    for s in SOURCES:
        f.write(f"{s['qe']},{s['source']},{s['mrn']},{s['eid']},{MPID},"
                f"{FIRST},{LAST},{DOB},{GENDER}\n")

# README / manifest
readme = f"""# Marcus Evans — golden cross-source test person (synthetic)

One synthetic person who intentionally spans 5 SHIN-NY QE sources so he can be
linked in the MPI and used to demo cross-source matching + de-duplication.

Identity
  name: {FIRST} {LAST}   DOB: {DOB[:4]}-{DOB[4:6]}-{DOB[6:]}   sex: {GENDER}
  shared MPID: {MPID}
  address: {', '.join(ADDR)}

Source identities (qe | source : mrn / eid)
""" + '\n'.join(f"  {s['qe']}|{s['source']} : mrn={s['mrn']} eid={s['eid']}" for s in SOURCES) + f"""

Files
  mpi/marcus_mpi.csv            MPI anchor rows (qe, source, mrn, eid, mpid, name, dob, gender)
  ccda/*.xml                    5 C-CDA documents, one per source. Same person, same
                                conditions + labs; only the demographics + source <id>
                                (QE|Source + MRN) differ, so the portal has real overlap
                                to de-duplicate.
  oru-hl7/*.hl7                 Genuine HL7 v2.5.1 ORU^R01 lab messages (NOT FHIR).

De-duplication built in
  - The 2025-03-15 Basic Metabolic Panel (Glucose, Creatinine, Sodium) appears in the
    CCDs AND in the HEALTHIX ORU feed AND (Glucose) in the GRRHIO ORU feed.
  - HbA1c and TSH are ORU-only "new" results. HbA1c is flagged High.
  - Expect the portal to collapse Glucose 2025-03-15 from 3 sources into one, prefer the
    ORU value (it carries units + reference range + abnormal flag), and keep HbA1c/TSH.

All data is 100% synthetic. Demonstration only.
"""
with open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8') as f:
    f.write(readme)

print('Bundle written to ./' + OUT)
print('CCDs:', ccd_files)
print('ORU :', oru_files)
print('MPI :', mpi_path)
