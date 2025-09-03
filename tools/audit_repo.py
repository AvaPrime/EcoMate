#!/usr/bin/env python3
import os, re, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXPECT_FILES = [
  'services/proposal/bom_engine.py', 'services/proposal/cost_model.py',
  'services/catalog/sync.py', 'services/maintenance/scheduler.py',
  'services/compliance/engine.py', 'services/compliance/rules/',
  'services/telemetry/ingestor.py', 'services/api/main.py',
  '.github/workflows/'
]
STUB_PATTERNS = [r"\bTODO\b", r"\bFIXME\b", r"raise NotImplementedError", r"#\s*stub", r"pass\s*(#.*)?$"]
CI_EXPECT = ['.github/workflows/pr-polish.yml', '.github/workflows/compliance-gate.yml']
DOCS_EXPECT = [
  'eco_mate_master_index_roadmap_overview.md',
  'eco_mate_future_roadmap_living_document.md',
  'eco_mate_production_implementation_plan_drop_in_files_steps.md',
  'eco_mate_market_supply_chain_data_integration.md',
  'eco_mate_regulatory_compliance_data_integration.md',
  'eco_mate_environmental_geographic_data_integration_implementation_plan.md',
  'eco_mate_operational_predictive_data_integration.md'
]

def file_exists(p: Path):
    return (ROOT/p).exists() if str(p).endswith('/') else (ROOT/p).is_file()

def scan_stubs(p: Path):
    try: txt = p.read_text(encoding='utf-8', errors='ignore')
    except: return []
    hits = []
    for pat in STUB_PATTERNS:
        for m in re.finditer(pat, txt, re.M|re.I):
            line = txt.count('\n', 0, m.start()) + 1
            hits.append({'pattern': pat, 'line': line})
    return hits

def walk_py(root): return [p for p in (ROOT/root).rglob('*.py')]

def main():
    status = {"missing_files":[], "present_files":[], "stub_findings":{},
              "ci_present":[], "ci_missing":[], "docs_present":[], "docs_missing":[]}
    for f in EXPECT_FILES:
        (status['present_files'] if file_exists(Path(f)) else status['missing_files']).append(f)
    for py in walk_py('services'):
        hits = scan_stubs(py)
        if hits: status['stub_findings'][str(py)] = hits
    for ci in CI_EXPECT:
        (status['ci_present'] if file_exists(Path(ci)) else status['ci_missing']).append(ci)
    for d in DOCS_EXPECT:
        (status['docs_present'] if file_exists(Path(d)) else status['docs_missing']).append(d)
    print(json.dumps(status, indent=2))

if __name__ == '__main__': main()