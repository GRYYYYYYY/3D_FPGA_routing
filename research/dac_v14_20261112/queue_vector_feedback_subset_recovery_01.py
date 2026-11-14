#!/usr/bin/env python3
"""One capacity/STA test of a new failure-derived subset, on the same original state."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from run_native_scope_policy_v4 import run_dir
from explicit_envelope_timing_policy import decide

q=D/'vector_feedback_subset_native_recovery_01/queue';q.mkdir(parents=True,exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
prior=D/'completed_resource_timing_recovery_01/queue';owner=read(prior/'registration.json')
plan=D/'vector_feedback_subset_01/plan.json';value=read(plan);source=Path(value['source_state'])
assert read(D/'vector_feedback_subset_01/completion.json')['passed']
assert value['selection']['profile']['all_current_paths_covered']
caps=read(D/'low_resource_dual_timing_02/absolute_limits.json')
files=[Path(__file__).resolve(),plan,D/'vector_feedback_subset_01/completion.json',
    D/'prepare_native_group_step_v2.py',D/'native_problem_identity.py',
    D/'run_registered_independent_transactions.py',D/'explicit_envelope_timing_policy.py',
    source/'completion.json',source/'endpoint_vector.json',prior/'registration.json']
bindings={str(p):sha(p) for p in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bindings,prerequisite_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),
    source_state=str(source),plan=str(plan),fixed_resource_limits=caps,
    question='Can a same-source subset derived from rejected aggregate feedback improve the fixed full endpoint vector, when the old menu either worsened donors or left a tied endpoint flat?',
    controls='Same original45SB input, full-vector/strict rules, native weighted objective/full-device search and exact absolute caps. The acceptance rule is not relaxed. The new subset excludes actions with donors whose actual route delay increased in the rejected same-source aggregate; it is not a history-best circuit configuration.',
    limits=dict(native_VPR_this_chain=1,other_pool_parent_plus_child=2,combined_native_VPR_maximum=3,
        child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='Independent targeted mechanism intervention, not a replacement of already completed batches or a new whole-configuration score. Old failed proposals and all costs preserved. It waits for the other serial native chain to end; no concurrent slot overbooking. A one-probe outcome never ends the research.'))
write(q/'status.json',dict(status='waiting_for_completed_resource_timing_owner_terminal'))
while True:
    p=process_identity(owner['pid'])
    if not p or p['state']=='Z' or p['start_ticks']!=owner['start_ticks']:break
    time.sleep(15)
if not (prior/'completion.json').exists():
    write(q/'completion.json',dict(passed=False,status='prior_owner_missing_receipt_requires_reconciliation',native_calls=0,source_sha256=bindings));raise SystemExit(1)
started=time.monotonic();costs=[];tx=q.parent/'transaction'
commands=[('prepare',[sys.executable,str(D/'prepare_native_group_step_v2.py'),'--plan',str(plan),
    '--anchor-state',str(source),'--output',str(tx),'--objective','weighted_soft']),
    ('native',[sys.executable,str(D/'run_registered_independent_transactions.py'),'--batch',str(tx),'--selector','compact'])]
passed=True
for phase,command in commands:
    assert all(sha(p)==h for p,h in bindings.items())
    t=time.monotonic()
    with (q/(phase+'.log')).open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',phase=phase,pid=process.pid,
            start_ticks=process_identity(process.pid)['start_ticks'],command=command))
        code=process.wait()
    costs.append(dict(phase=phase,returncode=code,complete_process_seconds=time.monotonic()-t))
    write(q/'process_costs.json',costs)
    if code:passed=False;break
result=None
if passed:
    row=read(tx/'progress.json')['current_group'];passed=row['status']=='legal_evaluated'
    if passed:
        state=Path(row['evaluation']);assert read(state/'completion.json')['passed'] and read(state/'input_seal.json')['passed']
        physical=read(run_dir(state)/'independent_audit.json');assert physical['audit']['passed']
        axes=physical['physical_metrics'];resources=dict(wirelength=axes['planar_wirelength_excluding_sb_half_nodes'],
            SB_pairs=axes['sb_pairs_used'],CB_sources=axes['cb_crossing_output_sources_used'])
        before,after=read(source/'endpoint_vector.json'),read(state/'endpoint_vector.json')
        decisions={policy:decide(policy,before,after,resources,cpd_limit_s=before['cpd_s'],
            resource_limits=caps,native_valid=True,transaction_complete=True) for policy in ['strict','endpoint_vector']}
        result=dict(state=str(state),CPD_s=after['cpd_s'],resources=resources,decisions=decisions,
            accepted=decisions['endpoint_vector']['accepted'],
            accepted_state=str(state if decisions['endpoint_vector']['accepted'] else source))
        write(q.parent/'decisions.json',result)
write(q/'completion.json',dict(passed=passed,result=result,process_costs=costs,
    complete_intervention_workflow_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None,
    source_sha256=bindings,
    qualification='Fresh actual native capacity/FULL/STA test of an omitted failure-derived scope, with unchanged exact policy. Acceptance recorded separately from process/legal success. Interpret vector gains/plateaus/regressions and donor changes before integrating the general controller; not full-algorithm time or research completion.'))
