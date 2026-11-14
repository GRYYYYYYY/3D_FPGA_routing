#!/usr/bin/env python3
"""Freeze focused manuscript and chronological evidence with only new-delta checks."""
import re
import shutil
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
delta = read(p / 'data/uniform_fused_delta_binding_01.json')
assert delta['passed'] and all(sha(D / n) == h for n, h in delta['sources_sha256'].items())
readers = {n: PdfReader(p / 'build' / n) for n in ['current_repair_main.pdf', 'main.pdf']}
checks = {}
for name, reader in readers.items():
    text = unicodedata.normalize('NFKC', ''.join(''.join(page.extract_text() or '' for page in reader.pages).split()))
    checks[name] = {number: number in text for number in ['2059563', '2059842', '217214', '372.048', '753.92']}
    assert all(checks[name].values()), checks[name]
for name in ['build_current_repair_03.log', 'build_uniform_fused_02.log']:
    assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error', (p / name).read_text()), name
claims = (p / 'claims_evidence.md').read_text()
assert all('| ' + key + ' |' in claims for key in delta['claims'])
links = []
for dest in re.findall(r'\]\(([^)]+)\)', claims[claims.index('| C164 |'):]):
    if '://' not in dest:
        assert (p / dest).exists()
        links.append(dest)
validation = p / 'uniform_fused_delta_validation_01.json'
write(validation, dict(passed=True, numerical_text_checks=checks, sources_sha256=delta['sources_sha256'],
      new_claims=delta['claims'], new_links_checked=links, pages={n: len(r.pages) for n, r in readers.items()},
      qualification='New source/numerical/build/link checks only. No repeated full historical ledger audit, route experiment or submission-readiness claim. Focused paper is a development manuscript; complete old evidence remains separate.'))
snapshot = D / 'paper_snapshots/current_uniform_fused_repair_20261114'
snapshot.mkdir(exist_ok=False)
files = [f for f in p.rglob('*') if f.is_file() and
         ((f.parent == p and f.suffix in ['.tex', '.md', '.cls', '.sh']) or
          (f.is_relative_to(p / 'data') and 'ledger_history_20261113' not in f.parts))]
files += [p / 'build/current_repair_main.pdf', p / 'build/current_repair_main.log', p / 'build/main.pdf', p / 'build/main.log',
          p / 'build_current_repair_03.log', p / 'build_uniform_fused_02.log', validation]
for f in files:
    target = snapshot / f.relative_to(p)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, target)
write(snapshot / 'snapshot_binding.json', dict(status='immutable_paper_snapshot', files={str(f.relative_to(p)): sha(f) for f in files},
      public_snapshot='f7167bd', pushed=False, focused_manuscript='current_repair_main.tex', chronological_evidence='main.tex'))
write(D / 'uniform_fused_paper_binding_01.json', dict(passed=True, snapshot=str(snapshot),
      pdf=str(snapshot / 'build/current_repair_main.pdf'), pages=len(readers['current_repair_main.pdf'].pages),
      evidence_pdf=str(snapshot / 'build/main.pdf'), evidence_pages=len(readers['main.pdf'].pages),
      claims=delta['claims'], archive='multiobjective_archive_47', new_work_pushed=False, complete_research=False,
      source_sha256={str(f): sha(f) for f in [Path(__file__).resolve(), snapshot / 'snapshot_binding.json', validation,
          p / 'data/uniform_fused_delta_binding_01.json', D / 'candidate_full_sta_native_binding_01.json',
          D / 'full_root_timing_potential_02/completion.json', D / 'multiobjective_archive_47/completion.json']},
      qualification='Focused problem/mechanism/results/Pareto/ablation/cost draft plus preserved chronological evidence. Actual candidate resource-case integration validated; CPD-changing/forced-path and full cold algorithm claims remain unproved. Resource-first timing active, streaming loader benchmark independent, no research date/call/matrix stop.'))
print(dict(snapshot=str(snapshot), focused_pages=len(readers['current_repair_main.pdf'].pages),
           evidence_pages=len(readers['main.pdf'].pages)), flush=True)
