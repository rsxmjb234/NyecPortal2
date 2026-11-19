"""
make_person.py  -  build one realistic synthetic PERSON who appears across many
SHIN-NY QE sources. MVP target = Marcus Evans.

Realistic, NOT cloned:
  * Each of the N documents starts from a DIFFERENT Synthea patient, so every
    CCD has its own labs, medications, vitals, encounters and immunizations
    (genuine document variety for the parsing engine).
  * On every document we rewrite only the IDENTITY (name, DOB, sex, address) to
    the person, and the SOURCE identity (QE|Source assigning authority + a
    distinct MRN), plus a per-QE EID and one shared MPID.
  * We NORMALIZE the problem/condition list to the SAME set on every document,
    so the person presents consistently across sources.
  * Age is identical everywhere (DOB fixed). Region is set to the person's.
  * A shared recent basic metabolic panel is added to each document and mirrored
    by a genuine HL7 v2.5.1 ORU per source, so the portal has real cross-source
    de-duplication to perform.

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
N = 10
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

# Shared condition list (same on every document). (SNOMED, display, onset)
CONDITIONS = [
    ('44054006', 'Diabetes mellitus type 2 (disorder)', '20120301'),
    ('59621000', 'Essential hypertension (disorder)', '20100615'),
    ('55822004', 'Hyperlipidemia (disorder)', '20110920'),
    ('433144002', 'Chronic kidney disease stage 3 (disorder)', '20180110'),
    ('396275006', 'Osteoarthritis (disorder)', '20160505'),
]

# 10 (QE, Source) pairs; MRNs assigned below (random, distinct).
SOURCES = [
    ('HEALTHIX', 'MSSM'), ('HEALTHIX', 'NYP'),
    ('HEALTHELINK', 'KINGSB'), ('HEALTHELINK', 'ECMC'),
    ('HIXNY', 'SPLPCPRIME'), ('HIXNY', 'ALBMC'),
    ('GRRHIO', 'UR1244'), ('GRRHIO', 'RGH'),
    ('BRONX', 'BXLEB'), ('HEALTHECONN', 'UHS'),
][:N]

DOC_TIME = '20250315120000'
LAB_DT, LAB_N = '20250315103000', '2025-03-15T10:30:00Z'
BMP = [
    ('2339-0', 'Glucose [Mass/volume] in Blood', '81.78', 'mg/dL'),
    ('38483-4', 'Creatinine [Mass/volume] in Blood', '1.01', 'mg/dL'),
    ('2947-0', 'Sodium [Moles/volume] in Blood', '141.78', 'mmol/L'),
]
ORU_ROWS = [
    ('2339-0', 'Glucose', '81.78', 'mg/dL', '70-99', 'N'),
    ('38483-4', 'Creatinine', '1.01', 'mg/dL', '0.70-1.30', 'N'),
    ('2947-0', 'Sodium', '141.78', 'mmol/L', '136-145', 'N'),
    ('4548-4', 'Hemoglobin A1c', '6.1', '%', '4.0-5.6', 'H'),
]


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


def narrative_table(headers, rows):
    text = el('text')
    table = sub(text, 'table', border='1', width='100%')
    thead = sub(table, 'thead')
    tr = sub(thead, 'tr')
    for h in headers:
        sub(tr, 'th', h)
    tbody = sub(table, 'tbody')
    for row in rows:
        r = sub(tbody, 'tr')
        for cell in row:
            sub(r, 'td', cell)
    return text


def replace_text(sec, text_el):
    old = sec.find('v3:text', ns)
    idx = list(sec).index(old) if old is not None else 1
    if old is not None:
        sec.remove(old)
    sec.insert(idx, text_el)


def clear_entries(sec):
    for e in sec.findall('v3:entry', ns):
        sec.remove(e)


def problem_entry(code, name, onset):
    entry = el('entry', typeCode='DRIV')
    act = sub(entry, 'act', classCode='ACT', moodCode='EVN')
    sub(act, 'templateId', root='2.16.840.1.113883.10.20.22.4.3')
    sub(act, 'id', root=f'urn:uuid:{random.getrandbits(122):032x}')
    sub(act, 'code', nullFlavor='NA')
    sub(act, 'statusCode', code='active')
    etv = sub(act, 'effectiveTime')
    sub(etv, 'low', value=onset + '000000')
    er = sub(act, 'entryRelationship', typeCode='SUBJ')
    obs = sub(er, 'observation', classCode='OBS', moodCode='EVN')
    sub(obs, 'templateId', root='2.16.840.1.113883.10.20.22.4.4')
    sub(obs, 'id', root=f'urn:uuid:{random.getrandbits(122):032x}')
    sub(obs, 'code', code='64572001', displayName='Condition',
        codeSystem='2.16.840.1.113883.6.96', codeSystemName='SNOMED-CT')
    sub(obs, 'statusCode', code='completed')
    eto = sub(obs, 'effectiveTime')
    sub(eto, 'low', value=onset + '000000')
    val = sub(obs, 'value', code=code, displayName=name,
              codeSystem='2.16.840.1.113883.6.96', codeSystemName='SNOMED-CT')
    val.set(f'{{{XSI}}}type', 'CD')
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


def sections(root):
    out = {}
    for s in root.findall('.//v3:section', ns):
        t = s.find('v3:title', ns)
        if t is not None and t.text:
            out[t.text.strip()] = s
    return out


def build_ccd(base_path, qe, source, mrn, eid):
    root = ET.parse(base_path).getroot()

    de = root.find('v3:effectiveTime', ns)
    if de is not None:
        de.set('value', DOC_TIME)

    pr = root.find('.//v3:recordTarget/v3:patientRole', ns)
    ids = pr.findall('v3:id', ns)
    if ids:
        ids[0].set('extension', mrn)
        ids[0].set('assigningAuthorityName', f'{qe}|{source}')
    pos = (list(pr).index(ids[-1]) + 1) if ids else 0
    pr.insert(pos, el('id', root='2.16.840.1.113883.3.9999.mpid', extension=PERSON['mpid']))
    pr.insert(pos, el('id', root='2.16.840.1.113883.3.9999.eid', extension=eid,
                      assigningAuthorityName=qe))

    addr = pr.find('v3:addr', ns)
    if addr is not None:
        for tag, v in zip(('streetAddressLine', 'city', 'state', 'postalCode'), PERSON['addr']):
            e = addr.find(f'v3:{tag}', ns)
            if e is None:
                e = ET.SubElement(addr, q(tag))
            e.text = v

    pat = pr.find('v3:patient', ns)
    nm = pat.find('v3:name', ns)
    for extra in nm.findall('v3:given', ns)[1:]:
        nm.remove(extra)
    for extra in nm.findall('v3:family', ns)[1:]:
        nm.remove(extra)
    gv = nm.find('v3:given', ns)
    (gv if gv is not None else sub(nm, 'given')).text = PERSON['first']
    fam = nm.find('v3:family', ns)
    (fam if fam is not None else sub(nm, 'family')).text = PERSON['last']
    g = pat.find('v3:administrativeGenderCode', ns)
    if g is not None:
        g.set('code', PERSON['sex'])
    bt = pat.find('v3:birthTime', ns)
    if bt is not None:
        bt.set('value', PERSON['dob'])

    secs = sections(root)
    # normalize Problems to the shared condition list
    if 'Problems' in secs:
        s = secs['Problems']
        clear_entries(s)
        replace_text(s, narrative_table(
            ['Start', 'Stop', 'Description', 'Code'],
            [(c[2][:4] + '-' + c[2][4:6] + '-' + c[2][6:] + 'T00:00:00Z', '', c[1], f'SNOMED-CT {c[0]}')
             for c in CONDITIONS]))
        for code, name, onset in CONDITIONS:
            s.append(problem_entry(code, name, onset))
    # add the shared recent BMP (drives ORU dedup); keep all other base labs
    if 'Diagnostic Results' in secs:
        s = secs['Diagnostic Results']
        s.append(bmp_organizer())
        append_narrative_row(s, (LAB_N, '', 'Basic metabolic panel - Blood', 'LOINC 51990-0'))

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


# ---- build ----
BASES = sorted(glob.glob('ccds/*.xml'))
if len(BASES) < N:
    raise SystemExit(f'need {N} distinct base CCDs in ccds/, found {len(BASES)}')
BASES = BASES[:N]

for d in ('ccda', 'oru-hl7', 'mpi'):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
for old in glob.glob(os.path.join(OUT, '**', '*.*'), recursive=True):
    try:
        os.remove(old)
    except OSError:
        pass

rows = []
for i, ((qe, source), base) in enumerate(zip(SOURCES, BASES), 1):
    mrn = str(random.randint(100000, 999999))
    eid = f'{qe[:2].upper()}-EID-{random.randint(1000, 9999)}'
    stem = f'MARCUS_{qe}_{source}_{mrn}'
    with open(os.path.join(OUT, 'ccda', stem + '.xml'), 'w', encoding='utf-8') as f:
        f.write(build_ccd(base, qe, source, mrn, eid))
    with open(os.path.join(OUT, 'oru-hl7', stem + '_ORU.hl7'), 'w', encoding='utf-8', newline='') as f:
        f.write(make_oru(qe, source, mrn, eid, f'MSG{i:04d}'))
    rows.append((qe, source, mrn, eid, os.path.basename(base)))

with open(os.path.join(OUT, 'mpi', 'marcus_mpi.csv'), 'w', encoding='utf-8', newline='') as f:
    f.write('qe,source,mrn,eid,mpid,first_name,last_name,dob,gender\n')
    for qe, source, mrn, eid, _ in rows:
        f.write(f'{qe},{source},{mrn},{eid},{PERSON["mpid"]},'
                f'{PERSON["first"]},{PERSON["last"]},{PERSON["dob"]},{PERSON["sex"]}\n')

cond_list = '\n'.join(f'  - {c[1]}' for c in CONDITIONS)
readme = f"""# {PERSON['first']} {PERSON['last']} - one realistic person across {N} QE sources (synthetic)

A single synthetic PERSON present in {N} SHIN-NY QE sources. Each document is a
DIFFERENT Synthea patient (so labs, meds, vitals, encounters vary -> realistic
document variety), but all share one identity and one condition list.

Identity (identical on every document):
  name: {PERSON['first']} {PERSON['last']}   DOB: {PERSON['dob'][:4]}-{PERSON['dob'][4:6]}-{PERSON['dob'][6:]}   sex: {PERSON['sex']}
  shared MPID: {PERSON['mpid']}
  region: {', '.join(PERSON['addr'])}

Shared condition list (normalized onto every document):
{cond_list}

Source identities (QE|Source : MRN / EID  <- base Synthea record):
""" + '\n'.join(f'  {qe}|{source} : mrn={mrn} eid={eid}   (from {b})'
                for qe, source, mrn, eid, b in rows) + f"""

Each document also carries a shared 2025-03-15 basic metabolic panel, mirrored by
a genuine HL7 v2.5.1 ORU^R01 per source (Glucose/Creatinine/Sodium duplicate the
CCD panel to drive de-duplication; Hemoglobin A1c is ORU-only, flagged High).

Files
  mpi/marcus_mpi.csv   one MPI anchor row per source
  ccda/*.xml           {N} distinct C-CDAs (same person, same conditions, {N} sources)
  oru-hl7/*_ORU.hl7    {N} genuine HL7 ORU feeds

All data is 100% synthetic. Demonstration only.
"""
with open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8') as f:
    f.write(readme)

print(f'Wrote {OUT}: {N} DISTINCT CCDs + {N} ORUs for {PERSON["first"]} {PERSON["last"]}')
for qe, source, mrn, eid, b in rows:
    print(f'  {qe}|{source:11} MRN={mrn}  base={b[:26]}')
