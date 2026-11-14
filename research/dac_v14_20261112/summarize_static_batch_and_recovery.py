#!/usr/bin/env python3
"""Separate engineering equivalence, implementation failures and actual QoR."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
batch=D/'native_batch_equivalence_dev_01';c=read(batch/'completion.json');assert c['passed'];rows=[];files=[Path(__file__).resolve(),batch/'completion.json']
for name in ['BNN_A0','SPMV_failure_success']:
 state=batch/name;r=read(state/'completion.json');assert r['passed'] and all(r['checks'].values());rows.append(dict(case=name,requests=r['native_transaction_calls'],native_processes=r['native_analysis_calls'],native_process_seconds=r['native_process_seconds'],complete_observed_component_workflow_seconds=r['complete_observed_workflow_seconds'],all_outputs_equal=True,post_batch_STA_fresh_and_identical=True));files.append(state/'completion.json')
b=D/'pending_reservation_dev_02';old=read(b/'completion.json');oldstatuses={k:v['status'] for k,v in old['roles'].items()};assert list(oldstatuses.values()).count('native_or_candidate_audit_failed')==4
failures=[]
for name,r in old['roles'].items():
 if r['status']=='legal_evaluated':continue
 state=b/name;run=Path(read(state/'completion.json')['run']);m=read(run/'manifest.json');assert m['status']=='failed' and m['returncode']==134;assert "Assertion '!trees.at(net)->find_by_isink(pin)' failed" in (run/'stdout.log').read_text();assert read(state/'completion.json')['checks']['inputs_unchanged'];failures.append(dict(role=name,class_='implementation_assertion_before_candidate',native_returncode=134,original_files_unchanged=True,native_graceful_rollback_completed=False));files += [state/'completion.json',run/'manifest.json',run/'stdout.log']
recovery=D/'reservation_prune_recovery_dev_01';new=read(recovery/'completion.json');assert new['passed'];recovery_rows=[]
for name,r in new['roles'].items():
 assert r['status']=='legal_evaluated';recovery_rows.append(dict(role=name,CPD_ns=r['cpd_s']*1e9,resources=r['resources'],accepted={k:v['accepted'] for k,v in r['policies'].items()},reused_FULLSTA=r['reused_FULL_STA']));files.append(recovery/(name+'_decisions.json'))
write(D/'static_batch_reservation_summary_01.json',dict(passed=True,static_batch=rows,component_speedup='unknown: no fresh same-version paired timing cohort',original_stage03_statuses=oldstatuses,stage03_failures=failures,stage04_recovery=recovery_rows,
 interpretation='Stage04 fixes the implementation failure and prevents the physical-cost starvation regression; on has the same CPD/wire/SB/CB as the earlier matched native-weighted target-only result. This supports robustness of that physical-cost branch, not superiority over the strongest weighted control. Static batching preserves results and failures but whole-algorithm speedup remains unknown.',source_sha256={str(p):sha(p) for p in files+[D/'native_reservation_stage_04/binding.json',D/'reservation_multisink_regression_01/completion.json',recovery/'completion.json']},new_native_calls=0))
print(dict(static_native_processes=2,static_transactions=10,old_implementation_failures=len(failures),recovery=recovery_rows))
