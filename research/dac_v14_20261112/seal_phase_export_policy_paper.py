#!/usr/bin/env python3
"""Seal the focused paper after exact phase and export checks, without a repeated audit."""
import re
import shutil
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
delta_path = p / 'data/phase_export_policy_delta_binding_01.json'
delta = read(delta_path)
assert delta['passed'] and all(sha(path) == digest for path, digest in delta['source_sha256'].items())
assert sha(p / 'current_repair_main.tex') == sha(delta['manuscript_version'])
composition = read(D / 'resource_first_composition_01.json')
left = read(Path(composition['resource_first_state']) / 'endpoint_vector.json')
right = read(Path(composition['timing_first_reference']) / 'endpoint_vector.json')
vector_identity = {key: left[key] == right[key] for key in ['cpd_s', 'setup', 'hold', 'endpoint_ids', 'constraints_sha256']}
assert all(vector_identity.values())
pdf = p / 'build_phase_export_policy_01/current_repair_main.pdf'
reader = PdfReader(pdf)
text = ''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
checks = {value: value in text for value in ['13.413972', '1793.82', '894.94', '834.50', '49.76', '90.21', '70.66', '2.21']}
assert all(checks.values()), checks
log = p / 'build_phase_export_policy_01_tectonic.log'
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error', log.read_text())
claims = (p / 'claims_evidence.md').read_text()
assert all('| ' + key + ' |' in claims for key in delta['claims'])
validation = p / 'phase_export_policy_delta_validation_01.json'
write(validation, dict(passed=True, numerical_text_checks=checks, full_endpoint_vector_identity=vector_identity,
    pages=len(reader.pages), source_sha256=delta['source_sha256'],
    qualification='New source/numeric/PDF/delta validation only; exact setup and hold arrays/endpoint identities checked, not just nonregression counters. Underfull spacing warnings permitted; no overfull or unresolved references. No native work or full historical re-audit.'))
snapshot = D / 'paper_snapshots/current_phase_export_policy_20261114'
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
    (p / 'build_phase_export_policy_01/current_repair_main.log', Path('build/current_repair_main.log')),
    (log, Path(log.name)), (validation, Path(validation.name))]:
    target = snapshot / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    payload[str(relative)] = sha(path)
write(snapshot / 'snapshot_binding.json', dict(status='immutable_paper_snapshot', files=payload,
    public_snapshot='f7167bd', pushed=False, source_version=delta['manuscript_version'], focused_manuscript='current_repair_main.tex'))
old = read(D / 'streaming_timing_prefix_paper_binding_01.json')
write(D / 'phase_export_policy_paper_binding_01.json', dict(passed=True, snapshot=str(snapshot),
    pdf=str(snapshot / 'build/current_repair_main.pdf'), pages=len(reader.pages),
    evidence_pdf=old['evidence_pdf'], evidence_pages=old['evidence_pages'], claims=delta['claims'],
    archive='multiobjective_archive_50', new_work_pushed=False, complete_research=False,
    source_sha256={str(path): sha(path) for path in [Path(__file__).resolve(), snapshot / 'snapshot_binding.json', validation, delta_path]},
    qualification='Focused current5page repair manuscript with independently sealed historical evidence. Terminal resource-first local operator reaches known quality/vector; component I/O gain is not a new cold routing speedup. New automatic resource queue proceeds independently under registered controls; goal active.'))
print(dict(passed=True, pages=len(reader.pages), pdf=str(snapshot / 'build/current_repair_main.pdf')), flush=True)
