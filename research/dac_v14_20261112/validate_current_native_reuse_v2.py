#!/usr/bin/env python3
"""Actual historical transaction reuse and invalidation checks, no native runs."""
import copy,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_native_reuse import match,failed_match
start=time.monotonic();b=D/'current_native_reuse_validation_02';b.mkdir(exist_ok=False)
history=D/'bnn_release_joint_dev_01';role=read(history/'registration.json')['roles']['R1_target_only_weighted_soft'];checks=[]
r=match(role,[history]);assert r and read(Path(r['evaluation'])/'completion.json')['passed'];checks.append(dict(case='exact_R1_request_state_objective',reused=True,evaluation=r['evaluation']))
for key,value in [('objective','weighted_capacity'),('state',str(D/'timing_cone_bnn_dev_01/Tf')),('pressure_start',10.)]:
 changed=copy.deepcopy(role);changed[key]=value;assert match(changed,[history]) is None;checks.append(dict(case='changed_'+key,reused=False))
request=b/'different_request.txt';request.write_text(Path(role['request']).read_text()+'\n');changed=copy.deepcopy(role);changed['request']=str(request);assert match(changed,[history]) is None;checks.append(dict(case='different_request_bytes',reused=False))
changed=copy.deepcopy(role);changed['original_budget']['wirelength']-=1
assert match(changed,[history])['evaluation']==r['evaluation'];checks.append(dict(case='acceptance_budget_not_native_search_input',native_reused=True,acceptance_must_be_recomputed=True))
failed_history=D/'spmv_adoption_factorial_01';failed_role=read(failed_history/'registration.json')['roles']['physical_soft']
f=failed_match(failed_role,[failed_history]);assert f and f['status']=='identical_completed_native_failure'
assert failed_match(role,[history]) is None
checks.append(dict(case='actual_completed_SPVM_capacity_failure',reused_failure=True))
checks.append(dict(case='legal_R1_not_marked_failed',passed=True))
write(b/'completion.json',dict(passed=True,checks=checks,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'current_native_reuse.py',history/'registration.json',request]},complete_process_seconds=time.monotonic()-start,new_native_calls=0,
 qualification='Exact native candidate reuse tested against actual full-legal R1 transaction and negative controls. No new policy commit, no sequential repair outcome claimed.'))
print('Passed',len(checks),'reuse cases',flush=True)
