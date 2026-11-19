"""
Build the "Marcus cohort": 5 DIFFERENT synthetic people (5 different Synthea
CCDs, so the parsing engine sees real document variety), each belonging to ONE
SHIN-NY QE source (matching Julie's "each person appears in only one source"),
but sharing the SAME conditions, the SAME hospitalization dates, and an aligned
inpatient lab panel. Each person also gets a genuine HL7 v2.5.1 ORU^R01 lab
feed, time-aligned to the hospitalization and overlapping the CCD panel so the
portal has real de-duplication to do.

Names, DOBs and MRNs are all changed. Output -> ./marcus_bundle (for S3 upload).
"""
import os
import glob
import shutil
import random
import xml.etree.ElementTree as ET

V3 = 'urn:hl7-org:v3'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'
ns = {'v3': V3}
OUT = 'marcus_bundle'
random.seed(2026)

ET.register_namespace('', V3)
ET.register_namespace('sdtc', 'urn:hl7-org:sdtc')
ET.register_namespace('xsi', XSI)

# ---- shared clinical story (same for all 5) ----
CONDITIONS = [
    ('44054006', 'Diabetes mellitus type 2 (disorder)'),
    ('59621000', 'Essential hypertension (disorder)'),
    ('55822004', 'Hyperlipidemia (disorder)'),
]
ONSET = '20241101000000'
ONSET_N = '2024-11-01T00:00:00Z'
ADMIT, DISCHARGE = '20250210090000', '20250214140000'
ADMIT_N, DISCHARGE_N = '2025-02-10T09:00:00Z', '2025-02-14T14:00:00Z'
LAB_DT, LAB_N = '20250210090000', '2025-02-10T09:00:00Z'
BMP = [
    ('2339-0', 'Glucose [Mass/volume] in Blood', '81.78', 'mg/dL'),
    ('38483-4', 'Creatinine [Mass/volume] in Blood', '1.01', 'mg/dL'),
    ('2947-0', 'Sodium [Moles/volume] in Blood', '141.78', 'mmol/L'),
    ('6298-4', 'Potassium [Moles/volume] in Blood', '4.20', 'mmol/L'),
    ('49765-1', 'Calcium [Mass/volume] in Blood', '9.50', 'mg/dL'),
]

# ---- the 5 people (one per source) ----
BASE = sorted(glob.glob('ccds/*.xml'))
PEOPLE = [
    {'first': 'Marcus',  'last': 'Evans',      'dob': '19500601', 'sex': 'M',
     'qe': 'HEALTHIX',    'source': 'MSSM'},
    {'first': 'Darnell', 'last': 'Washington', 'dob': '19580314', 'sex': 'M',
     'qe': 'HEALTHELINK', 'source': 'KINGSB'},
    {'first': 'Rosa',    'last': 'Martinez',   'dob': '19620922', 'sex': 'F',
     'qe': 'HIXNY',       'source': 'SPLPCPRIME'},
    {'first': 'Alan',    'last': 'Whitfield',  'dob': '19551205', 'sex': 'M',
     'qe': 'GRRHIO',      'source': 'UR1244'},
    {'first': 'Priya',   'last': 'Nair',       'dob': '19670730', 'sex': 'F',
     'qe': 'BRONX',       'source': 'BXLEB'},
]
for i, p in enumerate(PEOPLE):
    p['base'] = BASE[i]
    p['mrn'] = str(random.randint(100000, 999999))
    p['eid'] = f"{p['qe'][:2].upper()}-EID-{random.randint(1000, 9999)}"
    p['mpid'] = f"COHORT-{i + 1:04d}"


def q(t):
    return f'{{{V3}}}{t}'


def el(tag, text=None, **attrs):
    e = ET.Element(q(tag))
    for k, v in attrs.items():
        e.set(k, v)
    if text is not None:
        e.text = text
    return e


def sub(parent, tag, text=None, **attrs):
    e = el(tag, text, **attrs)
    parent.append(e)
    return e


def narrative_table(rows):
    """Build a v3 narrative <text> with Start/Stop/Description/Code columns."""
    text = el('text')
    table = sub(text, 'table', border='1', width='100%')
    thead = sub(table, 'thead')
    tr = sub(thead, 'tr')
    for h in ('Start', 'Stop', 'Description', 'Code'):
        sub(tr, 'th', h)
    tbody = sub(table, 'tbody')
    for start, stop, desc, code in rows:
        r = sub(tbody, 'tr')
        sub(r, 'td', start)
        sub(r, 'td', stop)
        sub(r, 'td', desc)
        sub(r, 'td', code)
    return text


def replace_text(sec, text_el):
    old = sec.find('v3:text', ns)
    if old is not None:
        idx = list(sec).index(old)
        sec.remove(old)
    else:
        idx = 1
    sec.insert(idx, text_el)


def clear_entries(sec):
    for e in sec.findall('v3:entry', ns):
        sec.remove(e)


def problem_entry(code, name):
    entry = el('entry', typeCode='DRIV')
    act = sub(entry, 'act', classCode='ACT', moodCode='EVN')
    sub(act, 'templateId', root='2.16.840.1.113883.10.20.22.4.3')
    sub(act, 'id', root=f'urn:uuid:{random.getrandbits(122):032x}')
    sub(act, 'code', nullFlavor='NA')
    sub(act, 'statusCode', code='active')
    etv = sub(act, 'effectiveTime')
    sub(etv, 'low', value=ONSET)
    er = sub(act, 'entryRelationship', typeCode='SUBJ')
    obs = sub(er, 'observation', classCode='OBS', moodCode='EVN')
    sub(obs, 'templateId', root='2.16.840.1.113883.10.20.22.4.4')
    sub(obs, 'id', root=f'urn:uuid:{random.getrandbits(122):032x}')
    sub(obs, 'code', code='64572001', displayName='Condition',
        codeSystem='2.16.840.1.113883.6.96', codeSystemName='SNOMED-CT')
    sub(obs, 'statusCode', code='completed')
    eto = sub(obs, 'effectiveTime')
    sub(eto, 'low', value=ONSET)
    val = sub(obs, 'value', code=code, displayName=name,
              codeSystem='2.16.840.1.113883.6.96', codeSystemName='SNOMED-CT')
    val.set(f'{{{XSI}}}type', 'CD')
    return entry


def encounter_entry():
    entry = el('entry', typeCode='DRIV')
    enc = sub(entry, 'encounter', classCode='ENC', moodCode='EVN')
    sub(enc, 'templateId', root='2.16.840.1.113883.10.20.22.4.49')
    sub(enc, 'id', root=f'urn:uuid:{random.getrandbits(122):032x}')
    sub(enc, 'code', code='32485007', displayName='Hospital admission',
        codeSystem='2.16.840.1.113883.6.96', codeSystemName='SNOMED-CT')
    et = sub(enc, 'effectiveTime')
    sub(et, 'low', value=ADMIT)
    sub(et, 'high', value=DISCHARGE)
    return entry


def bmp_organizer():
    entry = el('entry', typeCode='DRIV')
    org = sub(entry, 'organizer', classCode='BATTERY', moodCode='EVN')
    sub(org, 'templateId', root='2.16.840.1.113883.10.20.22.4.1')
    sub(org, 'id', root=f'urn:uuid:{random.getrandbits(122):032x}')
    sub(org, 'code', code='51990-0', displayName='Basic metabolic panel - Blood',
        codeSystem='2.16.840.1.113883.6.1', codeSystemName='LOINC')
    sub(org, 'statusCode', code='completed')
    et = sub(org, 'effectiveTime')
    sub(et, 'low', value=LAB_DT)
    sub(et, 'high', value=LAB_DT)
    for code, name, value, unit in BMP:
        comp = sub(org, 'component')
        obs = sub(comp, 'observation', classCode='OBS', moodCode='EVN')
        sub(obs, 'templateId', root='2.16.840.1.113883.10.20.22.4.2')
        sub(obs, 'id', root=f'urn:uuid:{random.getrandbits(122):032x}')
        sub(obs, 'code', code=code, displayName=name,
            codeSystem='2.16.840.1.113883.6.1', codeSystemName='LOINC')
        sub(obs, 'statusCode', code='completed')
        sub(obs, 'effectiveTime', value=LAB_DT)
        v = sub(obs, 'value', value=value, unit=unit)
        v.set(f'{{{XSI}}}type', 'PQ')
    return entry


def append_narrative_row(sec, row):
    tbody = sec.find('v3:text//v3:tbody', ns)
    if tbody is None:
        return
    tr = sub(tbody, 'tr')
    for cell in row:
        sub(tr, 'td', cell)


def build_ccd(p):
    tree = ET.parse(p['base'])
    root = tree.getroot()

    de = root.find('v3:effectiveTime', ns)
    if de is not None:
        de.set('value', '20250215120000')

    # demographics + source identity
    pr = root.find('.//v3:recordTarget/v3:patientRole', ns)
    ids = pr.findall('v3:id', ns)
    if ids:
        ids[0].set('extension', p['mrn'])
        ids[0].set('assigningAuthorityName', f"{p['qe']}|{p['source']}")
    eid_el = el('id', root='2.16.840.1.113883.3.9999.eid', extension=p['eid'],
                assigningAuthorityName=p['qe'])
    mpid_el = el('id', root='2.16.840.1.113883.3.9999.mpid', extension=p['mpid'])
    pos = (list(pr).index(ids[-1]) + 1) if ids else 0
    pr.insert(pos, mpid_el)
    pr.insert(pos, eid_el)

    pat = pr.find('v3:patient', ns)
    nm = pat.find('v3:name', ns)
    for extra in nm.findall('v3:given', ns)[1:]:
        nm.remove(extra)
    for extra in nm.findall('v3:family', ns)[1:]:
        nm.remove(extra)
    gv = nm.find('v3:given', ns)
    if gv is None:
        gv = sub(nm, 'given')
    gv.text = p['first']
    fam = nm.find('v3:family', ns)
    if fam is None:
        fam = sub(nm, 'family')
    fam.text = p['last']
    gc = pat.find('v3:administrativeGenderCode', ns)
    if gc is not None:
        gc.set('code', p['sex'])
    bt = pat.find('v3:birthTime', ns)
    if bt is not None:
        bt.set('value', p['dob'])

    # sections: identical conditions + hospitalization + aligned BMP
    secs = {}
    for s in root.findall('.//v3:section', ns):
        t = s.find('v3:title', ns)
        if t is not None and t.text:
            secs[t.text.strip()] = s

    if 'Problems' in secs:
        s = secs['Problems']
        clear_entries(s)
        replace_text(s, narrative_table(
            [(ONSET_N, '', name, f'SNOMED-CT {code}') for code, name in CONDITIONS]))
        for code, name in CONDITIONS:
            s.append(problem_entry(code, name))

    if 'Encounters' in secs:
        s = secs['Encounters']
        clear_entries(s)
        replace_text(s, narrative_table(
            [(ADMIT_N, DISCHARGE_N, 'Hospital admission', 'SNOMED-CT 32485007')]))
        s.append(encounter_entry())

    if 'Diagnostic Results' in secs:
        s = secs['Diagnostic Results']
        s.append(bmp_organizer())
        append_narrative_row(s, (LAB_N, '', 'Basic metabolic panel - Blood', 'LOINC 51990-0'))

    return ET.tostring(root, encoding='unicode')


# ---------- HL7 v2.5.1 ORU^R01 ----------
def oru(p, msgid):
    qe, fac, mrn = p['qe'], p['source'], p['mrn']
    rows = [
        ('2339-0', 'Glucose', '81.78', 'mg/dL', '70-99', 'N'),        # dup of CCD BMP
        ('38483-4', 'Creatinine', '1.01', 'mg/dL', '0.70-1.30', 'N'),  # dup
        ('2947-0', 'Sodium', '141.78', 'mmol/L', '136-145', 'N'),      # dup
        ('4548-4', 'Hemoglobin A1c', '7.2', '%', '4.0-5.6', 'H'),      # ORU-only, abnormal
    ]
    addr = '179 Bednar Knoll^^New York^NY^11367'
    pid3 = f'{mrn}^^^{qe}&{fac}^MR~{p["eid"]}^^^{qe}^PI~{p["mpid"]}^^^NYEC^PI'
    seg = [
        '|'.join(['MSH', '^~\\&', f'LAB_{qe}', fac, 'SHINNY', 'NYS', LAB_DT, '',
                  'ORU^R01^ORU_R01', msgid, 'P', '2.5.1']),
        '|'.join(['PID', '1', '', pid3, '', f'{p["last"]}^{p["first"]}', '', p['dob'],
                  p['sex'], '', '', addr]),
        '|'.join(['PV1', '1', 'I', fac]),
        '|'.join(['ORC', 'RE', f'ORD{msgid}', f'FIL{msgid}', '', '', '', '', '', LAB_DT]),
        '|'.join(['OBR', '1', f'ORD{msgid}', f'FIL{msgid}',
                  '51990-0^Basic metabolic panel^LN', '', LAB_DT, LAB_DT,
                  '', '', '', '', '', '', '', '', '', '', '', '', '', 'F']),
    ]
    for i, (code, name, val, unit, rng, flag) in enumerate(rows, 1):
        seg.append('|'.join(['OBX', str(i), 'NM', f'{code}^{name}^LN', '', val, unit,
                             rng, flag, '', '', 'F', '', '', LAB_DT]))
    return '\r'.join(seg) + '\r'


# ---------- build bundle ----------
for d in ('ccda', 'oru-hl7', 'mpi'):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
# clear old files (avoid rmtree; OneDrive can lock the directory handles)
for old in glob.glob(os.path.join(OUT, '**', '*.*'), recursive=True):
    try:
        os.remove(old)
    except OSError:
        pass

for i, p in enumerate(PEOPLE, 1):
    xml = build_ccd(p)
    fn = f"{p['last'].upper()}_{p['first'].upper()}_{p['qe']}_{p['source']}_{p['mrn']}.xml"
    with open(os.path.join(OUT, 'ccda', fn), 'w', encoding='utf-8') as f:
        f.write("<?xml version='1.0' encoding='UTF-8'?>\n" + xml)
    with open(os.path.join(OUT, 'oru-hl7', fn.replace('.xml', '_ORU.hl7')),
              'w', encoding='utf-8', newline='') as f:
        f.write(oru(p, f'MSG{i:04d}'))
    p['ccd'] = fn

with open(os.path.join(OUT, 'mpi', 'cohort_mpi.csv'), 'w', encoding='utf-8', newline='') as f:
    f.write('qe,source,mrn,eid,mpid,first_name,last_name,dob,gender\n')
    for p in PEOPLE:
        f.write(f"{p['qe']},{p['source']},{p['mrn']},{p['eid']},{p['mpid']},"
                f"{p['first']},{p['last']},{p['dob']},{p['sex']}\n")

readme = f"""# Marcus cohort - cross-source synthetic test fixture

5 DIFFERENT synthetic people, each generated from a different Synthea CCD (so
the documents genuinely differ and exercise the parsing engine), each belonging
to ONE SHIN-NY QE source (per the MPI rule that a person appears in one source).

They deliberately SHARE:
  - the same 3 conditions: {', '.join(n for _, n in CONDITIONS)}
  - the same hospitalization: admit 2025-02-10, discharge 2025-02-14
  - the same aligned inpatient Basic Metabolic Panel drawn 2025-02-10

People (name - DOB - sex - QE|Source - MRN - EID - MPID)
""" + '\n'.join(
        f"  {p['first']} {p['last']} - {p['dob'][:4]}-{p['dob'][4:6]}-{p['dob'][6:]} - "
        f"{p['sex']} - {p['qe']}|{p['source']} - MRN {p['mrn']} - {p['eid']} - {p['mpid']}"
        for p in PEOPLE) + f"""

Files
  mpi/cohort_mpi.csv     one MPI anchor row per person (qe, source, mrn, eid, mpid, name, dob, sex)
  ccda/*.xml             5 C-CDA documents (one per person / source)
  oru-hl7/*_ORU.hl7      genuine HL7 v2.5.1 ORU^R01 lab feeds (NOT FHIR), one per person

Time alignment & de-duplication
  - Each person's CCD carries the 2025-02-10 inpatient BMP (Glucose, Creatinine,
    Sodium, Potassium, Calcium).
  - Each person's HL7 ORU reports the SAME Glucose/Creatinine/Sodium on 2025-02-10
    (so the portal can collapse the duplicate and prefer the ORU value, which
    carries units + reference range + abnormal flag), plus an ORU-only Hemoglobin
    A1c = 7.2 % flagged High.

All data is 100% synthetic. Demonstration only.
"""
with open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8') as f:
    f.write(readme)

print('Wrote bundle -> ./' + OUT)
for p in PEOPLE:
    print(f"  {p['first']:8} {p['last']:11} {p['qe']}|{p['source']:10} "
          f"MRN={p['mrn']} DOB={p['dob']} base={os.path.basename(p['base'])[:22]}")
