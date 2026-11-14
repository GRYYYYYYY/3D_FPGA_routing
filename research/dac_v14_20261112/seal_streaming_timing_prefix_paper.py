#!/usr/bin/env python3
"""Freeze the updated focused paper; retain the previous full evidence PDF unchanged."""
import re
import shutil
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D, read, write, sha

p = D / 'paper'
delta = read(p / 'data/streaming_timing_prefix_delta_binding_01.json')
assert delta['passed'] and all(sha(D / n) == h for n, h in delta['sources_sha256'].items())
assert sha(p / 'current_repair_main.tex') == sha(D / delta['editable_manuscript_version'])
reader = PdfReader(p / 'build/current_repair_main.pdf')
text = ''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
checks = {v: v in text for v in ['13.421610', '2061627', '11.48', '5.10', '52,495']}
assert all(checks.values()), checks
log = p / 'build_streaming_timing_prefix_01.log'
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error', log.read_text())
claims = (p / 'claims_evidence.md').read_text()
assert all('| ' + c + ' |' in claims for c in delta['claims'])
validation = p / 'streaming_timing_prefix_delta_validation_01.json'
write(validation, dict(passed=True, checks=checks, sources_sha256=delta['sources_sha256'], pages=len(reader.pages),
      qualification='New focused-draft source/numerical/build validation only. Immutable version copy supports later edits; old full evidence PDF remains separately sealed. No route/STA or historical complete audit repeated.'))
snapshot = D / 'paper_snapshots/current_streaming_timing_prefix_20261114'
snapshot.mkdir(exist_ok=False)
files = [f for f in p.rglob('*') if f.is_file() and ((f.parent == p and f.suffix in ['.tex', '.md', '.cls', '.sh']) or
         (f.is_relative_to(p / 'data') and 'ledger_history_20261113' not in f.parts))]
files += [p / 'build/current_repair_main.pdf', p / 'build/current_repair_main.log', log, validation]
for f in files:
    target = snapshot / f.relative_to(p)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, target)
write(snapshot / 'snapshot_binding.json', dict(status='immutable_paper_snapshot', files={str(f.relative_to(p)): sha(f) for f in files},
      public_snapshot='f7167bd', pushed=False, focused_manuscript='current_repair_main.tex', source_version=delta['editable_manuscript_version']))
previous = read(D / 'uniform_fused_paper_binding_01.json')
write(D / 'streaming_timing_prefix_paper_binding_01.json', dict(passed=True, snapshot=str(snapshot),
      pdf=str(snapshot / 'build/current_repair_main.pdf'), pages=len(reader.pages),
      evidence_pdf=previous['evidence_pdf'], evidence_pages=previous['evidence_pages'],
      claims=delta['claims'], archive='multiobjective_archive_47', new_work_pushed=False, complete_research=False,
      source_sha256={str(f): sha(f) for f in [Path(__file__).resolve(), snapshot / 'snapshot_binding.json',
          validation, p / 'data/streaming_timing_prefix_delta_binding_01.json', D / 'uniform_fused_paper_binding_01.json']},
      qualification='Focused current repair manuscript plus independently sealed historical evidence. Streaming results are component measurements and an accepted timing prefix is not a finished trajectory or new joint frontier claim. Full cold algorithm confirmation remains incomplete; goal active.'))
print(dict(pdf=str(snapshot / 'build/current_repair_main.pdf'), pages=len(reader.pages)), flush=True)
