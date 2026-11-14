#!/usr/bin/env python3
"""Seal the focused paper after exact phase and export checks, without a repeated audit."""
import re
import shutil
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
delta_path = p / 'data/stable_seed_census_delta_binding_02.json'
delta = read(delta_path)
assert delta['passed'] and all(sha(path) == digest for path, digest in delta['source_sha256'].items())
assert sha(p / 'current_repair_main.tex') == sha(delta['manuscript_version'])
composition = read(D / 'resource_first_composition_01.json')
left = read(Path(composition['resource_first_state']) / 'endpoint_vector.json')
right = read(Path(composition['timing_first_reference']) / 'endpoint_vector.json')
vector_identity = {key: left[key] == right[key] for key in ['cpd_s', 'setup', 'hold', 'endpoint_ids', 'constraints_sha256']}
assert all(vector_identity.values())
pdf = p / 'build_stable_seed_census_02/current_repair_main.pdf'
reader = PdfReader(pdf)
text = ''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
checks = {value: value in text for value in ['217183','82','2061.28','572.64','543.80','330.43','136.65','Archive52']}
assert all(checks.values()), checks
log = p / 'build_stable_seed_census_02.log'
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error', log.read_text())
claims = (p / 'claims_evidence.md').read_text()
assert all('| ' + key + ' |' in claims for key in delta['claims'])
validation = p / 'stable_seed_census_delta_validation_01.json'
write(validation, dict(passed=True, numerical_text_checks=checks, full_endpoint_vector_identity=vector_identity,
    pages=len(reader.pages), source_sha256=delta['source_sha256'],
    qualification='New source/numeric/PDF/delta validation only; exact setup and hold arrays/endpoint identities checked, not just nonregression counters. Underfull spacing warnings permitted; no overfull or unresolved references. No native work or full historical re-audit.'))
snapshot = D / 'paper_snapshots/current_stable_seed_census_20261114'
snapshot.mkdir(exist_ok=False)
files = [path for path in p.rglob('*') if path.is_file() and
    ((path.parent == p and path.suffix in ['.tex', '.md', '.cls', '.sh']) or
     (path.is_relative_to(p / 'data') and 'ledger_history_20261113' not in path.parts))]
payload = {}
for path in files:
    relative = path.relative_to(p)
    target = snapshot / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    payload[str(relative)] = sha(path)
for path, relative in [(pdf, Path('build/current_repair_main.pdf')),
    (p / 'build_stable_seed_census_02/current_repair_main.log', Path('build/current_repair_main.log')),
    (log, Path(log.name)), (validation, Path(validation.name))]:
    target = snapshot / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    payload[str(relative)] = sha(path)
write(snapshot / 'snapshot_binding.json', dict(status='immutable_paper_snapshot', files=payload,
    public_snapshot='f7167bd', pushed=False, source_version=delta['manuscript_version'], focused_manuscript='current_repair_main.tex'))
old = read(D / 'serialization_mechanism_paper_binding_01.json')
write(D / 'stable_seed_census_paper_binding_01.json', dict(passed=True, snapshot=str(snapshot),
    pdf=str(snapshot / 'build/current_repair_main.pdf'), pages=len(reader.pages),
    evidence_pdf=old['evidence_pdf'], evidence_pages=old['evidence_pages'], claims=delta['claims'],
    archive='multiobjective_archive_52',diagnostic_archive='multiobjective_seed_order_diag_01',native_overlay='BNN_extended_native_menu_01.json',merged_archive_pending=True,new_work_pushed=False, complete_research=False,
    source_sha256={str(path): sha(path) for path in [Path(__file__).resolve(), snapshot / 'snapshot_binding.json', validation, delta_path]},
    qualification='Focused development manuscript adds sealed stronger82SB native control, real source-by-seed invariance/cost/physical gates and native count validation. Figure includes the stronger native control and explicit snapshot population. Actual client/global pristine-root transfer and fast count consumer remain outstanding, not inferred from component proofs. Goal active and no cold speedup claimed.'))
print(dict(passed=True, pages=len(reader.pages), pdf=str(snapshot / 'build/current_repair_main.pdf')), flush=True)
