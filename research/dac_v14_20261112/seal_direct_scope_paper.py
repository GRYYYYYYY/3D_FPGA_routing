#!/usr/bin/env python3
"""Seal only the new direct-scope manuscript delta and rendered artifact."""
import re
import shutil
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';delta_path=p/'data/direct_scope_delta_binding_02.json';delta=read(delta_path)
assert delta['passed'] and all(sha(path)==h for path,h in delta['source_sha256'].items())
assert sha(p/'current_repair_main.tex')==sha(delta['manuscript_version'])
proof=read(D/'direct_native_transaction_validation_01/completion.json')
assert proof['passed'] and proof['native_calls']==0 and proof['cases']==6 and len(proof['negative_controls'])==6
pdf=p/'build_direct_scope_01/current_repair_main.pdf';reader=PdfReader(pdf)
text=''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
checks={token:token in text for token in ['217183','2061.28','21.53','20.79','34.73','35.68','Archive52']}
assert all(checks.values()),checks
log=p/'build_direct_scope_01.log';assert not re.search('Overfull|Undefined|undefined|Fatal|Error',log.read_text())
assert '| C176 |' in (p/'claims_evidence.md').read_text()
validation=p/'direct_scope_delta_validation_01.json'
write(validation,dict(passed=True,numerical_text_checks=checks,pages=len(reader.pages),
    source_sha256=delta['source_sha256'],native_calls=0,qualification='New delta/claims/source/PDF validation only, not repeated historical or native audit.'))
snapshot=D/'paper_snapshots/current_direct_scope_repair_20261114';snapshot.mkdir(exist_ok=False)
files=[path for path in p.rglob('*') if path.is_file() and
       ((path.parent==p and path.suffix in ['.tex','.md','.cls','.sh']) or
        (path.is_relative_to(p/'data') and 'ledger_history_20261113' not in path.parts))]
payload={}
for path in files:
    relative=path.relative_to(p);target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target);payload[str(relative)]=sha(target)
for path,relative in [(pdf,Path('build/current_repair_main.pdf')),
    (p/'build_direct_scope_01/current_repair_main.log',Path('build/current_repair_main.log')),
    (log,Path(log.name)),(validation,Path(validation.name))]:
    target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target);payload[str(relative)]=sha(target)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=payload,
    public_snapshot='f7167bd',pushed=False,source_version=delta['manuscript_version'],focused_manuscript='current_repair_main.tex'))
old=read(D/'stable_seed_census_paper_binding_01.json')
binding=dict(passed=True,snapshot=str(snapshot),pdf=str(snapshot/'build/current_repair_main.pdf'),
    pages=len(reader.pages),evidence_pdf=old['evidence_pdf'],evidence_pages=old['evidence_pages'],
    claims=['C176'],archive=old['archive'],diagnostic_archive=old['diagnostic_archive'],
    native_overlay=old['native_overlay'],private45SB_prefix_in_final_figure=False,
    integrated_direct_scope_result_pending=True,new_work_pushed=False,complete_research=False,
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),snapshot/'snapshot_binding.json',validation,delta_path]},
    qualification='Six-page focused development manuscript with verified direct-audit component evidence and explicit integration/runtime uncertainty. Private paired prefixes excluded. No new route runs, cold speed claim or overall research completion.')
write(D/'direct_scope_paper_binding_01.json',binding)
for filename in ['CONTINUATION.json','live_handoff.json']:
    path=D/filename;value=read(path);value['latest_paper']=binding;write(path,value)
print(dict(passed=True,pages=len(reader.pages),pdf=binding['pdf']),flush=True)
