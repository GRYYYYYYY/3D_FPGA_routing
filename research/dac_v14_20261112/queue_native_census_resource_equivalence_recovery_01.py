#!/usr/bin/env python3
"""One downstream engineering owner; actual fixed-seed source actors finish first."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time

from retained_prefix_workflow import D,read,sha,write,route_body
from seed_census_analysis_pool_v2 import process_identity
from run_native_scope_policy_v4 import run_dir

q=D/'native_census_resource_equivalence_recovery_01/queue'
q.mkdir(parents=True,exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
prior=D/'direct_scope_resource_equivalence_recovery_01/queue'
owner=read(prior/'registration.json')
names=['eltwise_A0_native','eltwise_A0_paired','bnn_A0_native','bnn_A0_paired']
cases={name:owner['cases'][name] for name in names}
files=[Path(__file__).resolve(),D/'run_native_census_resource_repair_v2.py',
       D/'direct_native_transaction_audit.py',D/'direct_native_transaction_validation_01/completion.json',
       D/'direct_scope_actor_preparation_01.json',D/'seed_census_analysis_pool_v2.py',
       D/'pool_state_evaluator_v8.py',D/'native_resources_from_receipt.py',
       D/'current_crossing_share_selector_v3.py',D/'current_resource_bundle_v2.py',
       D/'multiobjective_acceptance_v2.py',D/'state_resource_assurance.py',D/'native_resource_nonempty_selection_01/completion.json',D/'native_census_resource_actor_preparation_01.json',D/'native_census_state_evaluator_validation_01/completion.json',D/'resource_assurance_selector_validation_01/completion.json',prior/'registration.json']
bindings={str(p):sha(p) for p in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bindings,prerequisite_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),cases=cases,
    question='Can explicit actual native resource assurance per private candidate plus selected-final independent physical verification preserve the direct-scope whole trajectory and reduce total imported workflow cost?' ,
    modification='Same direct scope/edge/capacity/FULLSTA and same selection/search/acceptance. Counts are explicitly native, never fabricated independent audits. Every final selected state must pass independent physical validation; other private states retain their own publication gate.',
    controls='Four predetermined A0 native/paired cases on eltwise andBNN; same pristine roots and all global fixed-seed parameters from predecessor. Whole own-current menus, not historically chosen winning steps. R1/Tf seed-transfer branches remain in the independent scientific cohort; no four-case completion ends research.',
    limits=dict(combined_native_VPR_maximum=3,this_chain_parent_plus_child=2,child_seconds=1800,
        memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='New engineering cohort only after preceding pool owner terminates. No running input/version modified. Partial predecessor case success permits its matching engineering case; unmatched failures are retained/skipped. Imported workflow comparison is not formal cold route-plus-repair timing; no fabricated independent resource assurance.'))
write(q/'status.json',dict(status='waiting_for_registered_direct_scope_equivalence_terminal'))
while True:
    actual=process_identity(owner['pid'])
    if not actual or actual['state']=='Z' or actual['start_ticks']!=owner['start_ticks']:break
    time.sleep(15)
if not (prior/'completion.json').exists():
    write(q/'completion.json',dict(passed=False,status='predecessor_ended_without_receipt_requires_reconciliation',
                                  results={},source_sha256=bindings,native_calls=0))
    sys.exit(1)
assert read(D/'direct_native_transaction_validation_01/completion.json')['passed']
started=time.monotonic();results={}

def signature(path):
    attempts=read(path/'attempts.json')
    return [dict(round=r['round'],candidate_rank=r['candidate_rank'],net=r['net'],pins=r['pins'],
        bundle_removed_pins=r['bundle_removed_pins'],
        pair={name:{k:row[k] for k in ['status','accepted','CPD_s','resources'] if k in row}
              for name,row in r['pair'].items()},
        committed_role=next((name for name,row in r['pair'].items()
            if r.get('committed_evaluation') is not None and row.get('evaluation')==r['committed_evaluation']),None)) for r in attempts]

def compare_states(reference,actual):
    rc,ac=read(reference/'completion.json'),read(actual/'completion.json')
    checks={key:rc[key]==ac[key] for key in ['operator_stop','accepted_steps','attempted_scopes',
                                         'initial_CPD_s','final_CPD_s','final_resources','native_analysis_children']}
    checks['all_target_scopes_and_arm_acceptance']=signature(reference)==signature(actual)
    rs,ats=read(reference/'steps.json'),read(actual/'steps.json')
    vectors_equal=len(rs)==len(ats)
    ordered_equal=len(rs)==len(ats)
    for left,right in zip(rs,ats):
        ls,as_=Path(left['committed_evaluation']),Path(right['committed_evaluation'])
        lv,av=read(ls/'endpoint_vector.json'),read(as_/'endpoint_vector.json')
        vectors_equal &= all(lv[k]==av[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
        ordered_equal &= route_body(run_dir(ls)/'routed.route')==route_body(run_dir(as_)/'routed.route')
    checks['every_accepted_full_precision_vector']=bool(vectors_equal)
    checks['every_accepted_ordered_route_body']=bool(ordered_equal)
    rfinal,afinal=Path(rc['final_state']),Path(ac['final_state'])
    checks['final_independent_physical_metrics']=read(run_dir(rfinal)/'independent_audit.json')['physical_metrics']==read(run_dir(afinal)/'independent_audit.json')['physical_metrics']
    return dict(passed=all(checks.values()),checks=checks,
        reference_imported_workflow_seconds=rc['complete_imported_algorithm_workflow_seconds'],
        direct_imported_workflow_seconds=ac['complete_imported_algorithm_workflow_seconds'],
        complete_single_configuration_algorithm_seconds=None,
        qualification='Development full-trajectory equivalence from same input/global policy. Both costs cover their own imported workflow, failures, audits, STA and sealing. Not cold route-plus-repair time or repeated formal runtime confirmation.')

for name,case in cases.items():
    assert all(sha(p)==h for p,h in bindings.items())
    reference=prior.parent/name
    if not read(prior/'results.json').get(name,{}).get('passed') or not (reference/'completion.json').exists() or not read(reference/'completion.json')['passed']:
        results[name]=dict(passed=False,status='no_passed_matching_reference_no_actor_submitted')
        write(q/'results.json',results);continue
    assert all(sha(p)==h for p,h in case['source_sha256'].items())
    output=q.parent/name
    command=[sys.executable,str(D/'run_native_census_resource_repair_v2.py'),
        '--initial-state',case['initial_state'],'--batch',str(output),
        '--full-graph-cache',case['full_graph_cache'],'--bundle-size','8',
        '--domain-mode',case['domain_mode'],'--graph-echo','compact','--seed-order','delay_rr_id',
        '--accepted-steps','0','--rank-windows','3']
    if case['domain_feedback']:command.append('--domain-feedback')
    t=time.monotonic()
    with (q/(name+'.log')).open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',case=name,pid=process.pid,
            start_ticks=process_identity(process.pid)['start_ticks'],command=command))
        code=process.wait()
    passed=code==0 and (output/'completion.json').exists() and read(output/'completion.json')['passed']
    comparison=compare_states(reference,output) if passed else None
    if comparison is not None:write(output/'equivalence.json',comparison)
    results[name]=dict(passed=passed and comparison['passed'],returncode=code,
        complete_actor_seconds=time.monotonic()-t,completion=str(output/'completion.json'),comparison=comparison)
    write(q/'results.json',results)
write(q/'completion.json',dict(passed=all(r['passed'] for r in results.values()),results=results,
    source_sha256=bindings,complete_engineering_cohort_seconds=time.monotonic()-started,
    complete_single_configuration_algorithm_seconds=None,
    qualification='Engineering cohort terminal only; any mismatch requires mechanism diagnosis before claiming equivalence/speed, never terminates the research goal.'))
