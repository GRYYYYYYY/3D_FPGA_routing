#!/usr/bin/env python3
"""Timing after each fully automatic resource endpoint, not a selected prefix."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from run_native_scope_policy_v4 import run_dir

q=D/'completed_resource_timing_dev_01/queue';q.mkdir(parents=True,exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
prior=D/'low_resource_dual_timing_02/queue';owner=read(prior/'registration.json')
cases={}
for label,name in [('native','bnn_A0_native_only_K8'),('paired','bnn_A0_feedback_K8')]:
    phase=D/'fused_resource_development_01'/name;c=read(phase/'completion.json');assert c['passed']
    initial=Path(c['final_state']);root=Path(c['initial_state'])
    original=read(run_dir(root)/'independent_audit.json')['physical_metrics']
    limits=dict(wirelength=(original['planar_wirelength_excluding_sb_half_nodes']*1001+999)//1000,
        SB_pairs=c['final_resources']['SB_pairs'],CB_sources=c['final_resources']['CB_sources'])
    path=q.parent/(label+'_absolute_limits.json');write(path,limits)
    cases[label]=dict(resource_phase=str(phase),source_state=str(initial),pristine_state=str(root),limits=limits,
        fixed_limits_file=str(path),source_sha256={str(p):sha(p) for p in [phase/'completion.json',
            phase/'registration.json',phase/'evaluation_context/input_seal.json',initial/'completion.json',
            initial/'endpoint_vector.json',path]})
files=[Path(__file__).resolve(),D/'run_native_census_analysis_v2.py',D/'run_independent_critical_portfolio_v4.py',
    D/'native_problem_identity.py',D/'prepare_native_group_step_v2.py',D/'current_group_feedback_cached.py',
    D/'run_registered_independent_transactions.py',D/'explicit_envelope_timing_policy.py',prior/'registration.json']
bindings={str(p):sha(p) for p in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bindings,prerequisite_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),cases=cases,
    question='Do the completely automatically selected native82SB and paired43SB resource endpoints admit later own-current native CPD repair under their retained vertical envelopes, beyond the registered45SB prefix diagnostic?',
    controls='Same original pristine strongA0 input and K8/rank3/no-prefix-cap resource policies already completed; each native/domain endpoint receives the same current-STA selector/native full-device scope/proposal/strict acceptance opportunities. Post-resource SB/CB caps derive uniformly from each endpoint; wire stays fixed at original pristine root+0.1%, never rolls forward. Different resource slices remain explicit.',
    timing='Exact completed resource observations reused with zero new first-phase routing. One explicit full-graph analysis per new endpoint supplies current selection. Observation/repair/imported/whole research timings are separate; no old phase creation time is attached as complete configuration runtime.',
    limits=dict(native_VPR_this_chain=1,other_pool_parent_plus_child=2,combined_native_VPR_maximum=3,
        child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='New independent development batch, not current45SB input modification, per-circuit historical-best selection or frozen cold confirmation. This tests whole automatic resource-phase endpoints including strong native control. Local two-case completion cannot finish the research goal.'))
write(q/'status.json',dict(status='waiting_for_current_two_policy_timing_owner_terminal'))
while True:
    p=process_identity(owner['pid'])
    if not p or p['state']=='Z' or p['start_ticks']!=owner['start_ticks']:break
    time.sleep(15)
if not (prior/'completion.json').exists():
    write(q/'completion.json',dict(passed=False,status='timing_owner_missing_terminal_receipt_requires_reconciliation',
        source_sha256=bindings,native_calls=0));raise SystemExit(1)
started=time.monotonic();results={}
for label,case in cases.items():
    assert all(sha(path)==h for path,h in bindings.items())
    assert all(sha(path)==h for path,h in case['source_sha256'].items())
    source=Path(case['source_state']);observation=q.parent/(label+'_full_observation')
    commands=[('observe',[sys.executable,str(D/'run_native_census_analysis_v2.py'),
        '--source',str(run_dir(source)),'--batch',str(observation),'--native-census','--timing-graph-echo']),
        ('timing',[sys.executable,str(D/'run_independent_critical_portfolio_v4.py'),
        '--initial-state',str(observation),'--batch',str(q.parent/label),
        '--query-graph',str(D/'bnn_physical_query_graph_01'),'--audit-cache',str(D/'rr_audit_cache_bnn_01'),
        '--policy','timing_under_resources','--budget-mode','explicit_absolute','--fixed-limits',case['fixed_limits_file']])]
    phase_results=[]
    for phase,command in commands:
        if phase=='timing':
            a,b=read(source/'endpoint_vector.json'),read(observation/'endpoint_vector.json')
            assert all(a[k]==b[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
            for history in [D/'low_resource_dual_timing_02/strict',D/'low_resource_dual_timing_02/endpoint']:
                for path in history.glob('round_*/feedback/capacity/analysis.json'):
                    if read(path).get('passed'):command+=['--reuse-query-batch',str(path.parent)]
        t=time.monotonic()
        with (q/(label+'_'+phase+'.log')).open('w') as log:
            process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
            write(q/'status.json',dict(status='running',case=label,phase=phase,pid=process.pid,
                start_ticks=process_identity(process.pid)['start_ticks'],command=command))
            code=process.wait()
        result_path=observation/'completion.json' if phase=='observe' else q.parent/label/'completion.json'
        passed=code==0 and result_path.exists() and read(result_path)['passed']
        phase_results.append(dict(phase=phase,passed=passed,returncode=code,receipt=str(result_path),
                                  complete_current_phase_seconds=time.monotonic()-t))
        write(q/(label+'_phases.json'),phase_results)
        if not passed:break
    results[label]=dict(passed=len(phase_results)==2 and all(r['passed'] for r in phase_results),phases=phase_results)
    write(q/'results.json',results)
write(q/'completion.json',dict(passed=all(r['passed'] for r in results.values()),results=results,
    source_sha256=bindings,complete_followup_research_workflow_seconds=time.monotonic()-started,
    complete_single_configuration_algorithm_seconds=None,
    qualification='Development phase composition/control outcome only. All costs and failures preserved; cold full configuration and broader circuit-independent confirmation remain outstanding.'))
