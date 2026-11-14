#!/usr/bin/env python3
"""Seal only the new resource/timing/consumer delta and its current projection."""
from pathlib import Path
import re
import shutil
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

p=D/'paper';delta_path=p/'data/strict_terminal_vector_feedback_delta_binding_02.json';delta=read(delta_path)
assert delta['passed'] and all(sha(path)==h for path,h in delta['source_sha256'].items())
assert sha(p/'current_repair_main.tex')==sha(delta['manuscript_version'])
archive=read(D/'multiobjective_low_resource_timing_03/completion.json');assert archive['passed'] and archive['records']==333
projection=read(p/'data/joint_quality_projection_binding_07.json')
assert projection['passed'] and projection['observations']==220 and projection['unique_quality_tuples']==124
for n,h in projection['artifact_sha256'].items():assert sha(p/'data'/n)==h
assert read(D/'native_census_state_evaluator_validation_01/completion.json')['passed']
assert read(D/'native_resource_nonempty_selection_01/completion.json')['passed']
pdf=p/'build_strict_terminal_vector_feedback_01/current_repair_main.pdf';reader=PdfReader(pdf)
text=''.join(''.join(page.extract_text() or '' for page in reader.pages).split())
checks={token:token in text for token in ['Archive333','2061353','2061301','13.228145690','7293.64','3028.24','2747.93']}
assert all(checks.values()),checks
log=p/'build_strict_terminal_vector_feedback_01.log';assert not re.search('Overfull|Undefined|undefined|Fatal|Error',log.read_text())
assert all('| '+key+' |' in (p/'claims_evidence.md').read_text() for key in delta['claims'])
validation=p/'strict_terminal_vector_feedback_delta_validation_01.json'
write(validation,dict(passed=True,pages=len(reader.pages),numerical_text_checks=checks,
    source_sha256=delta['source_sha256'],native_calls=0,
    qualification='New sealed resource/timing/consumer/PDF/projection delta only. No repeated historical audit or new routing; current prefixes and final resource endpoint are separate.'))
snapshot=D/'paper_snapshots/current_strict_terminal_vector_feedback_20261114';snapshot.mkdir(exist_ok=False)
files=[path for path in p.rglob('*') if path.is_file() and
    ((path.parent==p and path.suffix in ['.tex','.md','.cls','.sh']) or
     (path.is_relative_to(p/'data') and 'ledger_history_20261113' not in path.parts))]
payload={}
for path in files:
    relative=path.relative_to(p);target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target);payload[str(relative)]=sha(target)
for path,relative in [(pdf,Path('build/current_repair_main.pdf')),
    (p/'build_strict_terminal_vector_feedback_01/current_repair_main.log',Path('build/current_repair_main.log')),
    (log,Path(log.name)),(validation,Path(validation.name))]:
    target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target);payload[str(relative)]=sha(target)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files=payload,
    public_snapshot='f7167bd',pushed=False,source_version=delta['manuscript_version'],focused_manuscript='current_repair_main.tex'))
old=read(D/'low_resource_headroom_paper_binding_01.json')
binding=dict(passed=True,snapshot=str(snapshot),pdf=str(snapshot/'build/current_repair_main.pdf'),
    pages=len(reader.pages),evidence_pdf=old['evidence_pdf'],evidence_pages=old['evidence_pages'],claims=delta['claims'],
    archive='multiobjective_low_resource_timing_03',records=333,projection_observations=220,projection_quality_tuples=124,
    resource_actor_final_SB=43,registered_timing_root_SB=45,timing_prefix_accepts=3,
    timing_trajectory_complete=True,dual_policy_comparison_complete=True,feedback_subset_native_pending=True,live_native_census_equivalence_pending=True,new_work_pushed=False,complete_research=False,
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),snapshot/'snapshot_binding.json',validation,delta_path]},
    qualification='Six-page focused development paper: completed9accept43SB resource trajectory, distinct registered45SB three-accept timing phase at13.228146ns, completed full-vector six-proposal zero-accept control and pending feedback subset, all external strong baselines and actual native-census consumer component proof. No cross-input phase splicing, full cold speedup or overall research completion.')
write(D/'strict_terminal_vector_feedback_paper_binding_01.json',binding)
for name in ['CONTINUATION.json','live_handoff.json']:
    path=D/name;value=read(path);value['latest_paper']=binding;write(path,value)
print(dict(passed=True,pages=len(reader.pages),pdf=binding['pdf']),flush=True)
