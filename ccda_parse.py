"""Shared C-CDA + ORU parsing used by the chart renderers.

parse_ccd(path) -> dict of demographics + clinical section lists.
load_oru(patients) -> attaches ORU (FHIR Observation NDJSON) labs and flags
duplicates against CCD labs.
"""
import os
import glob
import json
import xml.etree.ElementTree as ET
from datetime import datetime, date

V3 = 'urn:hl7-org:v3'
ns = {'v3': V3}


def fmt_date(v):
    if not v:
        return ''
    v = v.strip()
    for n in (14, 12, 8):
        if len(v) >= n:
            try:
                fmt = {14: '%Y%m%d%H%M%S', 12: '%Y%m%d%H%M', 8: '%Y%m%d'}[n]
                return datetime.strptime(v[:n], fmt).strftime('%m/%d/%Y')
            except ValueError:
                continue
    return v


def parse_ccd(path):
    tree = ET.parse(path)
    root = tree.getroot()

    id_text = {}
    for el in root.iter():
        idv = el.get('ID')
        if idv:
            id_text[idv] = ' '.join(''.join(el.itertext()).split())

    def deref(el):
        if el is None:
            return ''
        ref = el.find('v3:reference', ns)
        if ref is not None:
            val = (ref.get('value') or '').lstrip('#')
            return id_text.get(val, '')
        return ' '.join(''.join(el.itertext()).split())

    def code_name(code_el):
        if code_el is None:
            return ''
        if code_el.get('displayName'):
            return code_el.get('displayName')
        tr = code_el.find('v3:translation', ns)
        if tr is not None and tr.get('displayName'):
            return tr.get('displayName')
        txt = deref(code_el.find('v3:originalText', ns))
        if txt:
            return txt
        return code_el.get('code', '') or ''

    def eff_low_high(parent):
        et_el = parent.find('v3:effectiveTime', ns)
        low = high = single = ''
        if et_el is not None:
            if et_el.get('value'):
                single = et_el.get('value')
            lo = et_el.find('v3:low', ns)
            hi = et_el.find('v3:high', ns)
            if lo is not None:
                low = lo.get('value', '')
            if hi is not None:
                high = hi.get('value', '')
        return low or single, high

    SEC = {}
    for s in root.findall('.//v3:section', ns):
        t = s.find('v3:title', ns)
        if t is not None and t.text:
            SEC[t.text.strip()] = s

    # ---- demographics ----
    pr = root.find('.//v3:recordTarget/v3:patientRole', ns)
    pat = pr.find('v3:patient', ns)
    nm = pat.find('v3:name', ns)
    given = ' '.join((g.text or '') for g in nm.findall('v3:given', ns)).strip()
    family = (nm.findtext('v3:family', default='', namespaces=ns) or '').strip()
    gender = pat.find('v3:administrativeGenderCode', ns).get('code', '')
    dob_raw = pat.find('v3:birthTime', ns).get('value', '')
    dob = fmt_date(dob_raw)
    age = ''
    if len(dob_raw) >= 8:
        b = datetime.strptime(dob_raw[:8], '%Y%m%d').date()
        t = date.today()
        age = t.year - b.year - ((t.month, t.day) < (b.month, b.day))

    addr_el = pr.find('v3:addr', ns)
    addr = ''
    if addr_el is not None:
        p = [addr_el.findtext('v3:streetAddressLine', default='', namespaces=ns),
             addr_el.findtext('v3:city', default='', namespaces=ns),
             addr_el.findtext('v3:state', default='', namespaces=ns),
             addr_el.findtext('v3:postalCode', default='', namespaces=ns)]
        p = [x for x in p if x]
        if len(p) >= 3:
            addr = f"{p[0]}, {p[1]}, {p[2]} {p[3] if len(p) > 3 else ''}".strip()
        else:
            addr = ', '.join(p)

    mrn = mrn_aa = mpiid = ''
    for idel in pr.findall('v3:id', ns):
        aa = idel.get('assigningAuthorityName', '')
        idroot = idel.get('root', '')
        if 'synthea' in aa.lower():
            mpiid = idel.get('extension', '')
            continue
        # skip the synthetic EID / MPID ids we stamp for cross-source linkage
        if idroot.endswith('.eid') or idroot.endswith('.mpid'):
            continue
        if aa and not mrn:          # first real source id (QE|Source) is the MRN
            mrn, mrn_aa = idel.get('extension', ''), aa
    if not mpiid:
        mpiid = pr.findall('v3:id', ns)[0].get('root', '')

    race = (pat.find('v3:raceCode', ns).get('displayName', '')
            if pat.find('v3:raceCode', ns) is not None else '')
    eth = (pat.find('v3:ethnicGroupCode', ns).get('displayName', '')
           if pat.find('v3:ethnicGroupCode', ns) is not None else '')
    lc = pat.find('.//v3:languageCommunication/v3:languageCode', ns)
    lang = lc.get('code', '') if lc is not None else ''

    doc_time = root.find('v3:effectiveTime', ns)
    doc_date = fmt_date(doc_time.get('value', '')) if doc_time is not None else ''

    base = os.path.basename(path)
    mpid_tag = base.split('_')[0] if '_' in base else base

    # ---- sections ----
    problems = []
    if 'Problems' in SEC:
        for act in SEC['Problems'].findall('.//v3:entry/v3:act', ns):
            obs = act.find('.//v3:observation', ns)
            if obs is None:
                continue
            name = code_name(obs.find('v3:value', ns)) or deref(obs.find('v3:text', ns))
            low, high = eff_low_high(obs)
            if not low:
                low, high = eff_low_high(act)
            problems.append({'name': name, 'onset': fmt_date(low),
                             'resolved': fmt_date(high),
                             'status': 'Resolved' if high else 'Active'})

    meds = []
    if 'Medications' in SEC:
        for sa in SEC['Medications'].findall('.//v3:entry/v3:substanceAdministration', ns):
            mat = sa.find('.//v3:manufacturedMaterial', ns)
            name = ''
            if mat is not None:
                name = code_name(mat.find('v3:code', ns)) or mat.findtext('v3:name', default='', namespaces=ns)
            low, high = eff_low_high(sa)
            meds.append({'name': name, 'start': fmt_date(low), 'stop': fmt_date(high)})

    labs = []
    if 'Diagnostic Results' in SEC:
        for org in SEC['Diagnostic Results'].findall('.//v3:entry/v3:organizer', ns):
            pname = code_name(org.find('v3:code', ns))
            plow, _ = eff_low_high(org)
            comps = []
            for obs in org.findall('v3:component/v3:observation', ns):
                vel = obs.find('v3:value', ns)
                value = unit = ''
                if vel is not None:
                    value = vel.get('value', '') or ''.join(vel.itertext()).strip()
                    unit = vel.get('unit', '')
                interp = obs.find('v3:interpretationCode', ns)
                flag = ''
                if interp is not None:
                    flag = {'N': 'Normal', 'L': 'Low', 'H': 'High', 'A': 'Abnormal',
                            'HH': 'Critical High', 'LL': 'Critical Low'}.get(
                        interp.get('code', ''), interp.get('code', ''))
                rr = ''
                rr_el = obs.find('.//v3:referenceRange//v3:text', ns)
                if rr_el is not None:
                    rr = ' '.join(''.join(rr_el.itertext()).split())
                olow, _ = eff_low_high(obs)
                ccode = obs.find('v3:code', ns)
                comps.append({'test': code_name(ccode), 'value': value,
                              'unit': unit, 'flag': flag, 'range': rr,
                              'date': fmt_date(olow or plow),
                              'loinc': ccode.get('code', '') if ccode is not None else '',
                              'source': 'CCD', 'superseded': False})
            labs.append({'panel': pname, 'date': fmt_date(plow), 'comps': comps})

    imms = []
    if 'Immunizations' in SEC:
        for sa in SEC['Immunizations'].findall('.//v3:entry/v3:substanceAdministration', ns):
            mat = sa.find('.//v3:manufacturedMaterial', ns)
            name = ''
            if mat is not None:
                name = code_name(mat.find('v3:code', ns)) or mat.findtext('v3:name', default='', namespaces=ns)
            low, _ = eff_low_high(sa)
            imms.append({'name': name, 'date': fmt_date(low)})
        imms.sort(key=lambda r: r['date'], reverse=True)

    vitals = []
    if 'Vital Signs' in SEC:
        for org in SEC['Vital Signs'].findall('.//v3:entry/v3:organizer', ns):
            olow, _ = eff_low_high(org)
            for obs in org.findall('v3:component/v3:observation', ns):
                vel = obs.find('v3:value', ns)
                value = unit = ''
                if vel is not None:
                    value = vel.get('value', '') or ''.join(vel.itertext()).strip()
                    unit = vel.get('unit', '')
                vlow, _ = eff_low_high(obs)
                vitals.append({'test': code_name(obs.find('v3:code', ns)), 'value': value,
                               'unit': unit, 'date': fmt_date(vlow or olow)})

    procs = []
    procsec = SEC.get('Surgeries')
    if procsec is None:
        procsec = SEC.get('Procedures')
    if procsec is not None:
        for proc in procsec.findall('.//v3:entry/v3:procedure', ns):
            name = code_name(proc.find('v3:code', ns)) or deref(proc.find('v3:text', ns))
            low, _ = eff_low_high(proc)
            procs.append({'name': name, 'date': fmt_date(low)})
        procs.sort(key=lambda r: r['date'], reverse=True)

    encs = []
    if 'Encounters' in SEC:
        for enc in SEC['Encounters'].findall('.//v3:entry/v3:encounter', ns):
            name = code_name(enc.find('v3:code', ns)) or deref(enc.find('v3:text', ns))
            low, high = eff_low_high(enc)
            encs.append({'name': name, 'start': fmt_date(low), 'stop': fmt_date(high)})
        encs.sort(key=lambda r: r['start'], reverse=True)

    allergies = []
    if 'Allergies' in SEC:
        for obs in SEC['Allergies'].findall('.//v3:entry//v3:observation', ns):
            name = code_name(obs.find('v3:value', ns))
            if name:
                allergies.append({'name': name})

    has = {
        'Conditions': len(problems), 'Allergies': len(allergies), 'Medications': len(meds),
        'Immunizations': len(imms), 'Vital Signs': len(vitals),
        'Lab Results': sum(len(p['comps']) for p in labs), 'Procedures': len(procs),
        'Encounters': len(encs),
    }

    return dict(given=given, family=family, gender=gender, dob=dob, age=age, addr=addr,
                mrn=mrn, mrn_aa=mrn_aa, mpiid=mpiid, race=race, eth=eth, lang=lang,
                doc_date=doc_date, mpid_tag=mpid_tag, problems=problems, meds=meds,
                labs=labs, imms=imms, vitals=vitals, procs=procs, encs=encs,
                allergies=allergies, has=has)


def load_oru(patients, pattern='*oru*.ndjson'):
    """Load ORU FHIR Observation NDJSON, attach to patients by MPID, flag dupes."""
    by_mpid = {}
    for fn in glob.glob(pattern):
        with open(fn, encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                o = json.loads(line)
                if o.get('resourceType') != 'Observation':
                    continue
                mpid = ''
                for idn in o.get('subject', {}).get('identifier', []):
                    if idn.get('system', '').endswith(':mpid'):
                        mpid = idn.get('value', '')
                if not mpid:
                    continue
                cod = o.get('code', {})
                coding = (cod.get('coding') or [{}])[0]
                loinc = coding.get('code', '')
                disp = coding.get('display', '') or cod.get('text', '')
                vq = o.get('valueQuantity', {})
                eff = o.get('effectiveDateTime', '')[:10]
                d = f'{eff[5:7]}/{eff[8:10]}/{eff[0:4]}' if len(eff) == 10 else ''
                by_mpid.setdefault(mpid, []).append({
                    'test': disp, 'loinc': loinc, 'value': vq.get('value', ''),
                    'unit': vq.get('unit', ''), 'date': d, 'dup': False})

    for P in patients:
        oru = by_mpid.get(P['mpid_tag'], [])
        P['oru'] = oru
        _reconcile_oru(P)


def _reconcile_oru(P):
    """Flag each ORU result as a duplicate of a CCD lab (same LOINC + date), and
    mark the matching CCD lab component as superseded (crossed off, not deleted)."""
    ccd_keys = set()
    for panel in P['labs']:
        for c in panel['comps']:
            ccd_keys.add((c['loinc'], c['date']))
    oru_keys = set((o['loinc'], o['date']) for o in P.get('oru', []))
    for o in P.get('oru', []):
        o['dup'] = (o['loinc'], o['date']) in ccd_keys
    for panel in P['labs']:
        for c in panel['comps']:
            if (c['loinc'], c['date']) in oru_keys:
                c['superseded'] = True


_HL7_FLAG = {'N': 'Normal', 'H': 'High', 'L': 'Low', 'A': 'Abnormal',
             'HH': 'Critical High', 'LL': 'Critical Low', '': ''}


def load_oru_hl7(patients, pattern):
    """Load genuine HL7 v2 ORU^R01 lab messages (NOT FHIR), match to patients by
    MRN from PID-3, and reconcile against CCD labs for de-duplication.

    Appends to any ORU already attached (e.g. from a FHIR feed)."""
    by_mrn = {}
    for fn in glob.glob(pattern):
        with open(fn, encoding='utf-8') as fh:
            raw = fh.read()
        segments = [s for s in raw.replace('\n', '\r').split('\r') if s.strip()]
        mrn = ''
        obs = []
        for s in segments:
            f = s.split('|')
            if f[0] == 'PID' and len(f) > 3:
                # PID-3: mrn^^^QE&Source^MR~eid^^^QE^PI~...
                mrn = f[3].split('~')[0].split('^')[0]
            elif f[0] == 'OBX' and len(f) > 5:
                code = f[3].split('^') if len(f) > 3 else ['']
                loinc = code[0]
                name = code[1] if len(code) > 1 else loinc
                value = f[5] if len(f) > 5 else ''
                unit = f[6] if len(f) > 6 else ''
                rng = f[7] if len(f) > 7 else ''
                flag = f[8] if len(f) > 8 else ''
                dt = f[14] if len(f) > 14 else ''
                obs.append({'test': name, 'loinc': loinc, 'value': value, 'unit': unit,
                            'date': fmt_date(dt), 'flag': _HL7_FLAG.get(flag, flag),
                            'range': rng, 'dup': False})
        if mrn:
            by_mrn.setdefault(mrn, []).extend(obs)

    for P in patients:
        extra = by_mrn.get(P.get('mrn', ''), [])
        if extra:
            P['oru'] = P.get('oru', []) + extra
            _reconcile_oru(P)
