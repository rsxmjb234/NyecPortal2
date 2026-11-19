"""
Render the Marcus cohort (./marcus_bundle) in the SMART on FHIR portal, pulling
labs from the genuine HL7 ORU feeds and de-duplicating them against the CCDs.
Output: marcus_portal.html

This just points the configurable build_smart renderer at the cohort bundle.
"""
import os

os.environ['CHART_CCD_DIR'] = os.path.join('marcus_bundle', 'ccda')
os.environ['CHART_ORU_HL7'] = os.path.join('marcus_bundle', 'oru-hl7')
os.environ['CHART_OUT'] = 'marcus_portal.html'
os.environ['CHART_TITLE'] = 'SHIN-NY Community Health Record'

import build_smart  # noqa: F401,E402  (importing runs the configured build)
