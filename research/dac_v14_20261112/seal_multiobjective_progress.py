#!/usr/bin/env python3
"""Seal completed multiobjective evidence while next graph preparation runs."""
import re,shutil,time,unicodedata
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha
paper=D/'paper';pdf=paper/'build/main.pdf';reader=PdfReader(str(pdf))
text=unicodedata.normalize('NFKC',' '.join(' '.join(p.extract_text() or '' for p in reader.pages).split()))
checks={s:s in text for s in ['148431','283.605','549.419','6720']}
checks['section_heading']='multiobjectivedevelopmentevaluation' in ''.join(text.casefold().split())
assert all(checks.values()),checks
log=paper/'build_multiobjective_progress_01.log';assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log.read_text())
v=read(paper/'data/evidence_v14_ledger_validation.json');assert v['status']=='passed' and v['ledger_sha256']==sha(paper/'data/evidence_v14_ledger.json')
write(paper/'multiobjective_pdf_validation_01.json',dict(passed=True,pages=len(reader.pages),checks=checks,pdf_sha256=sha(pdf),
 scope='Build and extracted-text validation; not DAC page-limit readiness.',
 prior_checker_failure='Case-sensitive heading search failed on PDF small-caps extraction M ULTIOBJECTIVE; use casefold/whitespace normalization for heading only. PDF/build unchanged; no repeated experiment.'))
snapshot=D/'paper_snapshots/current_multiobjective_archive_20261113';snapshot.mkdir(exist_ok=False)
files=[p for p in paper.rglob('*') if p.is_file() and ((p.parent==paper and p.suffix in ['.tex','.md','.cls','.sh']) or (p.is_relative_to(paper/'data') and 'ledger_history_20261113' not in str(p)))]
files+=[pdf,paper/'multiobjective_pdf_validation_01.json',log,paper/'verify_v14_ledger.py']
for p in files:
 q=snapshot/p.relative_to(paper);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
write(snapshot/'snapshot_binding.json',dict(status='immutable_paper_snapshot',files={str(p.relative_to(paper)):sha(p) for p in files},public_snapshot='f7167bd',pushed=False))
paths=[Path(__file__).resolve(),D/'multiobjective_archive_01/completion.json',D/'multiobjective_archive_01/validation.json',D/'multiobjective_policy_replay_01/completion.json',D/'multiobjective_acceptance_validation_02.json',D/'timing_cone_bnn_dev_02/completion.json',snapshot/'snapshot_binding.json',snapshot/'multiobjective_pdf_validation_01.json',snapshot/'data/evidence_v14_ledger.json']
write(D/'multiobjective_progress_binding_01.json',dict(passed=True,source_sha256={str(p):sha(p) for p in paths},new_work_pushed=False,research_complete=False,current_batch_rules_unchanged=True,archive_records=85,claims=['C108','C109'],next_registered='bnn_slack_release_screen_01/registration.json'))
for name in ['CONTINUATION.json','live_handoff.json']:
 h=read(D/name);h['latest_paper']=dict(snapshot=str(snapshot),pages=len(reader.pages),claims=['C108','C109'],new_work_pushed=False)
 h['latest_multiobjective']=dict(binding='multiobjective_progress_binding_01.json',archive='multiobjective_archive_01',points=85,non_dominated_records=43,uncertain_records=10,dominated_records=32,policy_replay='multiobjective_policy_replay_01',replay_checks=6720,replay_eligible_states=7,new_native_repairs=0,full_standalone_repair_time='unknown')
 h['latest_bnn_observations']=dict(batch='timing_cone_bnn_dev_02',passed=True,reused_Tf=True,new_native_calls=2,original_Tf_calls=1,route_search_calls=0);h['previous_goal_turn_classification']='progress';write(D/name,h)
with (D/'RESEARCH_LOG.md').open('a') as f:
 f.write('\nMultiobjective update sealed: original BNN Tf observation reused after coordinator interruption; A0/R1 observations completed with original rules, no reroutes. Archive85 actual run/state records:43 nondominated,10CPD precision-uncertain,32quality-dominated; unequal opportunities/time cohorts explicit. Historical SPMV weighted joint rejected on timing has148431wire/1SB vsacceptedplateau148445/1SB atsameCPD/CB; endpoint-vector benefit remains another dimension. BNN U/R1 formal medians283.605/549.419s withsameprintedCPD andresource tradeoffs; nohistorical timeattached torepair. Fixed-budget replay6720conditions/7eligiblehistoricalstates,0newroute/0commit;20core receipts distinct fromunknownstandalonealgorithm time. Protocol/continuations updated; C108-C10944pagepaper built/sealedlocal,542sources319links. BNN independent cache/export preparation supports upcoming slack-budgeted release+repair withmatchednativecontrols. Goalactivewithoutoverallstops.\n')
print(dict(pages=len(reader.pages),sources=v['source_count'],links=v['local_link_count'],sealed=True))
