#!/usr/bin/env python3
"""Seal current-cone diagnostic and bounded-vector implementation evidence."""
from pathlib import Path
import re
import shutil
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';delta_path=p/'data/low_resource_headroom_delta_binding_01.json';delta=read(delta_path)
assert delta['passed'] and all(sha(path)==h for path,h in delta['source_sha256'].items())
assert sha(p/'current_repair_main.tex')==sha(delta['manuscript_version'])
diag=read(D/'low_resource_timing_headroom_04/completion.json');assert diag['passed']
assert sum(r['potential_ns']>0 for r in diag['rows'])==5 and diag['reused_queries']==7 and diag['new_queries']==3
proof=read(D/'explicit_envelope_timing_policy_validation_01.json');assert proof['passed'] and len(proof['negative_controls'])==9
pdf=p/'build_low_resource_headroom_01/current_repair_main.pdf';reader=PdfReader(pdf)
text=''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
checks={token:token in text for token in ['217183','2061.28','0.185825799','0.007639001','45-SB/5060-CB','Archive52']}
assert all(checks.values()),checks
log=p/'build_low_resource_headroom_01.log';assert not re.search('Overfull|Undefined|undefined|Fatal|Error',log.read_text())
assert all('| '+c+' |' in (p/'claims_evidence.md').read_text() for c in delta['claims'])
validation=p/'low_resource_headroom_delta_validation_01.json'
write(validation,dict(passed=True,pages=len(reader.pages),numerical_text_checks=checks,
    source_sha256=delta['source_sha256'],native_calls=0,
    qualification='New diagnostic/policy/source/PDF delta only; running repair outcomes are not inferred.'))
snapshot=D/'paper_snapshots/current_low_resource_headroom_20261114';snapshot.mkdir(exist_ok=False)
files=[path for path in p.rglob('*') if path.is_file() and
    ((path.parent==p and path.suffix in ['.tex','.md','.cls','.sh']) or
     (path.is_relative_to(p/'data') and 'ledger_history_20261113' not in path.parts))]
payload={}
for path in files:
    relative=path.relative_to(p);target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target);payload[str(relative)]=sha(target)
for path,relative in [(pdf,Path('build/current_repair_main.pdf')),
    (p/'build_low_resource_headroom_01/current_repair_main.log',Path('build/current_repair_main.log')),
    (log,Path(log.name)),(validation,Path(validation.name))]:
    target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target);payload[str(relative)]=sha(target)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=payload,
    public_snapshot='f7167bd',pushed=False,source_version=delta['manuscript_version'],focused_manuscript='current_repair_main.tex'))
old=read(D/'direct_scope_paper_binding_01.json')
binding=dict(passed=True,snapshot=str(snapshot),pdf=str(snapshot/'build/current_repair_main.pdf'),
    pages=len(reader.pages),evidence_pdf=old['evidence_pdf'],evidence_pages=old['evidence_pages'],claims=delta['claims'],
    archive=old['archive'],diagnostic_archive=old['diagnostic_archive'],native_overlay=old['native_overlay'],
    low_resource_prefix_in_final_figure=False,dual_policy_result_pending=True,new_work_pushed=False,complete_research=False,
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),snapshot/'snapshot_binding.json',validation,delta_path]},
    qualification='Focused six-page development manuscript with current private-prefix potential, exact resource-bounded vector rule, explicit default BNN constraints and pending composition results. Optimistic gaps are not a feasible CPD improvement or native global bound. No final private-resource or complete-time point promoted.')
write(D/'low_resource_headroom_paper_binding_01.json',binding)
for name in ['CONTINUATION.json','live_handoff.json']:
    path=D/name;value=read(path);value['latest_paper']=binding;write(path,value)
print(dict(passed=True,pages=len(reader.pages),pdf=binding['pdf']),flush=True)
