#!/usr/bin/env python3
"""Two own-current timing policies on one frozen legal low-resource diagnostic root."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from run_native_scope_policy_v4 import run_dir

q=D/'low_resource_dual_timing_02/queue';q.mkdir(parents=True,exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
prior=D/'low_resource_timing_headroom_04';owner=read(prior/'registration.json')
origin=Path(owner['source_state']);paired=D/'fused_resource_development_01/bnn_A0_feedback_K8'
anchor=read(paired/'registration.json')['anchor'];metrics=read(run_dir(origin)/'independent_audit.json')['physical_metrics']
limits=dict(wirelength=anchor['resource_limits']['wirelength'],SB_pairs=metrics['sb_pairs_used'],CB_sources=metrics['cb_crossing_output_sources_used'])
write(q.parent/'absolute_limits.json',limits)
files=[Path(__file__).resolve(),D/'run_independent_critical_portfolio_v4.py',
    D/'explicit_envelope_timing_policy.py',D/'explicit_envelope_timing_policy_validation_01.json',
    D/'explicit_endpoint_portfolio_preparation_01.json',D/'current_group_feedback_cached.py',
    D/'prepare_native_group_step_v2.py',D/'native_problem_identity.py',D/'current_native_reuse_resource.py',
    D/'run_registered_independent_transactions.py',D/'current_sta_arrival_cone_compact.py',
    prior/'registration.json',origin/'completion.json',origin/'endpoint_vector.json',
    run_dir(origin)/'routed.route',paired/'registration.json',q.parent/'absolute_limits.json']
bindings={str(p):sha(p) for p in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bindings,prerequisite_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),
    original_resource_prefix=str(origin),timing_initial_state=owner['observation_state'],fixed_absolute_limits=limits,
    policies=['timing_under_resources','endpoint_under_resources'],
    question='Can freshly selected native whole-connection repairs lower CPD after automatic slack-based release to45SB/5060CB without giving resources back, and do exact flat-CPD endpoint-vector accepts enable later progress that strict CPD accepts miss?',
    controls='Both branches start from the exact same immutable legal observation, use the same current-STA selector, proposal order, full-device native search, modifiable trees, capacity/physical/FULLSTA checks and fixed absolute caps. Each reselects on its own state after acceptance. Strict branch keeps the existing strict-CPD-under-resources rule; secondary additionally requires componentwise fixed setup-vector progress at nonworse CPD. Same-source/request native results may be reused only before/where trajectories still match.',
    constraints='Inherited exact SDC digest and endpoint/launch/capture sets are verified from native full-precision vectors. No epsilon or rounded CPD comparison, no rolling resource budgets. Hold-violation components must not worsen.',
    limits=dict(this_chain_native_VPR=1,other_registered_pool_parent_plus_child=2,combined_native_VPR_maximum=3,
        child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='Composition diagnostic on a registered accepted resource prefix, not final resource-actor endpoint or frozen pristine-root algorithm confirmation. All repairs here use native search; no custom capacity mechanism superiority over equal-scope native search is implied. Exact reused physical observation and private source provenance retained. Diagnostic setup, per-strategy imported/reuse workflow and full cold algorithm time remain distinct.'))
write(q/'status.json',dict(status='waiting_for_low_resource_current_cone_and_headroom_diagnostic'))
while True:
    actual=process_identity(owner['pid'])
    if not actual or actual['state']=='Z' or actual['start_ticks']!=owner['start_ticks']:break
    time.sleep(15)
if not (prior/'completion.json').exists() or not read(prior/'completion.json')['passed']:
    write(q/'completion.json',dict(passed=False,status='diagnostic_prerequisite_failed_no_repairs_submitted',
        source_sha256=bindings,results={},native_calls=0,qualification='Requires main-model diagnosis; does not terminate research.'))
    sys.exit(1)
assert all(sha(p)==h for p,h in bindings.items())
initial=Path(owner['observation_state']);assert read(initial/'completion.json')['passed']
assert sha(run_dir(initial)/'routed.route')==sha(run_dir(origin)/'routed.route')
root_vector=read(initial/'endpoint_vector.json');original_vector=read(origin/'endpoint_vector.json')
assert all(root_vector[k]==original_vector[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
assert all(read(D/n)['passed'] for n in ['explicit_envelope_timing_policy_validation_01.json','explicit_endpoint_portfolio_preparation_01.json'])
write(q/'exact_initial_state_binding.json',dict(passed=True,initial_state=str(initial),original_state=str(origin),
    full_precision_CPD_s=root_vector['cpd_s'],constraints_sha256=root_vector['constraints_sha256'],
    endpoint_components=len(root_vector['setup']),limits=limits,
    qualification='Same exact vector/route/constraints root for both policies; no static initial target list.'))
started=time.monotonic();results={};transaction_history=[];query_history=[]
for label,policy in [('strict','timing_under_resources'),('endpoint','endpoint_under_resources')]:
    assert all(sha(p)==h for p,h in bindings.items())
    output=q.parent/label
    command=[sys.executable,str(D/'run_independent_critical_portfolio_v4.py'),'--initial-state',str(initial),
        '--batch',str(output),'--query-graph',str(D/'bnn_physical_query_graph_01'),
        '--audit-cache',str(D/'rr_audit_cache_bnn_01'),'--policy',policy,
        '--budget-mode','explicit_absolute','--fixed-limits',str(q.parent/'absolute_limits.json')]
    for tx in transaction_history:command+=['--reuse-native-batch',str(tx)]
    for query in query_history:command+=['--reuse-query-batch',str(query)]
    t=time.monotonic()
    with (q/(label+'.log')).open('w') as log:
        proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',policy=label,pid=proc.pid,
            start_ticks=process_identity(proc.pid)['start_ticks'],command=command))
        code=proc.wait()
    passed=code==0 and (output/'completion.json').exists() and read(output/'completion.json')['passed']
    secondary_only=[]
    for path in output.glob('round_*/proposal_*/policy_decisions.json'):
        ds=read(path)
        if not ds['timing_under_resources']['accepted'] and ds.get('endpoint_under_resources',{}).get('accepted'):
            secondary_only.append(dict(decisions=str(path),strict_reason=ds['timing_under_resources']['reason'],
                secondary_reason=ds['endpoint_under_resources']['reason']))
    write(output/'strict_rejected_secondary_admissible.json',dict(records=secondary_only,
        qualification='Policy-admissible proposals on this branch; actual commits are recorded separately in steps.json. Subsequent CPD reduction is an observed sequence, not causal proof from a single accept.'))
    results[label]=dict(passed=passed,returncode=code,completion=str(output/'completion.json'),
        complete_imported_strategy_workflow_seconds=time.monotonic()-t,secondary_only_proposals=len(secondary_only),
        complete_single_configuration_algorithm_seconds=None)
    write(q/'results.json',results)
    transaction_history.extend(p.parent for p in output.glob('round_*/proposal_*/transaction/progress.json'))
    query_history.extend(p.parent for p in output.glob('round_*/feedback/capacity/analysis.json') if read(p).get('passed'))
write(q/'completion.json',dict(passed=all(r['passed'] for r in results.values()),results=results,
    complete_two_strategy_research_workflow_seconds=time.monotonic()-started,
    complete_single_configuration_algorithm_seconds=None,source_sha256=bindings,
    qualification='Composition diagnostic branches terminal, not overall research completion or cold full-algorithm time. Read exact steps/current states; record timing migration, near endpoints, resources, failures and all costs before frontier claims.'))
