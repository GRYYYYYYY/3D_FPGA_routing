#!/usr/bin/env python3
"""Seal the focused paper after exact phase and export checks, without a repeated audit."""
import re
import shutil
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
delta_path = p / 'data/serialization_mechanism_delta_binding_01.json'
delta = read(delta_path)
assert delta['passed'] and all(sha(path) == digest for path, digest in delta['source_sha256'].items())
assert sha(p / 'current_repair_main.tex') == sha(delta['manuscript_version'])
composition = read(D / 'resource_first_composition_01.json')
left = read(Path(composition['resource_first_state']) / 'endpoint_vector.json')
right = read(Path(composition['timing_first_reference']) / 'endpoint_vector.json')
vector_identity = {key: left[key] == right[key] for key in ['cpd_s', 'setup', 'hold', 'endpoint_ids', 'constraints_sha256']}
assert all(vector_identity.values())
pdf = p / 'build_serialization_mechanism_01/current_repair_main.pdf'
reader = PdfReader(pdf)
text = ''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
checks = {value: value in text for value in ['217191', '141', '6719', '117.15', '118.13', '1793.82', '70.66']}
assert all(checks.values()), checks
log = p / 'build_serialization_mechanism_01.log'
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error', log.read_text())
claims = (p / 'claims_evidence.md').read_text()
assert all('| ' + key + ' |' in claims for key in delta['claims'])
validation = p / 'serialization_mechanism_delta_validation_01.json'
write(validation, dict(passed=True, numerical_text_checks=checks, full_endpoint_vector_identity=vector_identity,
    pages=len(reader.pages), source_sha256=delta['source_sha256'],
    qualification='New source/numeric/PDF/delta validation only; exact setup and hold arrays/endpoint identities checked, not just nonregression counters. Underfull spacing warnings permitted; no overfull or unresolved references. No native work or full historical re-audit.'))
snapshot = D / 'paper_snapshots/current_serialization_mechanism_20261114'
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
    (p / 'build_serialization_mechanism_01/current_repair_main.log', Path('build/current_repair_main.log')),
    (log, Path(log.name)), (validation, Path(validation.name))]:
    target = snapshot / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    payload[str(relative)] = sha(path)
write(snapshot / 'snapshot_binding.json', dict(status='immutable_paper_snapshot', files=payload,
    public_snapshot='f7167bd', pushed=False, source_version=delta['manuscript_version'], focused_manuscript='current_repair_main.tex'))
old = read(D / 'phase_export_policy_paper_binding_01.json')
write(D / 'serialization_mechanism_paper_binding_01.json', dict(passed=True, snapshot=str(snapshot),
    pdf=str(snapshot / 'build/current_repair_main.pdf'), pages=len(reader.pages),
    evidence_pdf=old['evidence_pdf'], evidence_pages=old['evidence_pages'], claims=delta['claims'],
    archive='multiobjective_archive_52', new_work_pushed=False, complete_research=False,
    source_sha256={str(path): sha(path) for path in [Path(__file__).resolve(), snapshot / 'snapshot_binding.json', validation, delta_path]},
    qualification='Focused current repair manuscript adds sealed eltwise native/paired automatic transfer and isolated source-order causality. New23wire gain is not attributed to guide scoring or graph I/O. BNN continuation and registered terminal archive queue remain active; imported workflows are not complete cold times. Goal active.'))
print(dict(passed=True, pages=len(reader.pages), pdf=str(snapshot / 'build/current_repair_main.pdf')), flush=True)
