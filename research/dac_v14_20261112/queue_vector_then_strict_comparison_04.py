"""Registered direct-strict versus completed-vector-then-strict development pair."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from resolve_transaction_history_v1 import resolve
from run_native_scope_policy_v4 import run_dir
from native_problem_identity import problem_identity

root=D/'vector_then_strict_comparison_04';q=root/'queue';q.mkdir(parents=True,exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
names=['stable_seed_transfer_recovery_02','direct_scope_resource_equivalence_recovery_02',
       'native_census_resource_equivalence_recovery_02','native_checkpoint_recovery_03',
       'rejection_feedback_controller_dev_01','complete_route_resource_measurements_03','vector_then_strict_comparison_02']
dependencies={n:read(D/n/'queue/registration.json') for n in names}
vector=D/'rejection_feedback_controller_dev_01/endpoint'
original=Path(read(vector/'registration.json')['initial_state'])
caps=D/'low_resource_dual_timing_02/absolute_limits.json'
assert read(caps)==read(vector/'registration.json')['fixed_absolute_limits']
source_files=[Path(__file__).resolve(),D/'run_independent_critical_portfolio_v5.py',
    D/'resolve_transaction_history_v1.py',D/'current_native_reuse_resource.py',caps,
    vector/'registration.json',original/'completion.json',original/'endpoint_vector.json',
    D/'feedback_successor_candidates_validation_01/completion.json']
# Bind local implementation dependencies before waiting; completed evidence is
# discovered and snapshotted only after all producers have actually terminated.
for mod in ['current_rejection_feedback_v1','current_proposal_portfolio','current_group_feedback_cached',
            'fixed_anchor_acceptance','multiobjective_acceptance_v2','explicit_envelope_timing_policy',
            'endpoint_timing_policy','endpoint_timing_policy_streaming_v2','native_problem_identity',
            'prepare_native_group_step_v2','run_registered_independent_transactions']:
    source_files.append(D/(mod+'.py'))
bindings={str(p):sha(p) for p in source_files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    prerequisites={n:dict(pid=r['pid'],start_ticks=r['start_ticks']) for n,r in dependencies.items()},
    source_sha256=bindings,original_state=str(original),fixed_resource_limits=read(caps),
    fixed_order=['direct_strict','vector_then_strict'],fraction=.9,
    transition_rule='Use the registered endpoint actor actual terminal state, never the best rejected candidate. Then strict CPD reduction under original immutable wire/SB/CB limits. Recompute targets after every accepted transaction. Both strict phases use the identical v5 menu including late feedback.',
    controls='Same original physical input and absolute caps. Direct strict receives its own current-state selection and complete v5 menu. Extra vector phase has extra opportunity/cost, not equal compute. This pair evaluates a fixed two-phase schedule on one development input, not independent confirmation.',
    limits=dict(concurrent_native_jobs=1,child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='Starts after complete measurements and every existing chain has a terminal receipt and absent live owner. Imported/reused evidence stays separate from new complete-flow timing. Research remains active.'))
while True:
    live=[];missing=[]
    for name,owner in dependencies.items():
        actual=process_identity(owner['pid'])
        if actual and actual['state']!='Z' and actual['start_ticks']==owner['start_ticks']:live.append(name)
        elif not (D/name/'queue/completion.json').exists():missing.append(name)
    write(q/'status.json',dict(status='waiting_for_complete_measurements_and_all_prior_chains',live_dependencies=live,missing_terminal_receipts=missing))
    if missing:
        write(q/'completion.json',dict(passed=False,status='dependency_missing_terminal_receipt',missing=missing,native_calls=0));raise SystemExit(1)
    if not live:break
    time.sleep(30)
assert all(sha(p)==h for p,h in bindings.items())
for name in names:
    phase=read(D/name/'queue/status.json')
    if 'pid' in phase:
        actual=process_identity(phase['pid'])
        assert not actual or actual['state']=='Z' or actual['start_ticks']!=phase['start_ticks']
closed=read(vector/'completion.json')
if not closed['passed'] or closed['operator_stop']!='no_admissible_candidate_in_current_portfolio':
    write(q/'completion.json',dict(passed=False,status='vector_phase_not_successfully_closed',native_calls=0));raise SystemExit(1)
warm=Path(closed['final_state']);assert read(warm/'completion.json')['passed']
assert problem_identity(run_dir(warm))==problem_identity(run_dir(original))
assert read(warm/'endpoint_vector.json')['cpd_s']<=read(original/'endpoint_vector.json')['cpd_s']
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX)
actors=[vector,D/'low_resource_dual_timing_02/strict',D/'low_resource_dual_timing_02/endpoint',
        D/'completed_resource_timing_dev_01/native',D/'completed_resource_timing_dev_01/paired',
        D/'completed_resource_timing_recovery_01/paired']
snapshot=root/'evidence_snapshot';snapshot.mkdir()
attempt_files=[]
for i,actor in enumerate(actors):
    if (actor/'attempts.json').exists():
        dest=snapshot/f'attempts_{i:02d}.json';dest.write_bytes((actor/'attempts.json').read_bytes());attempt_files.append(dest)
history=resolve(attempt_files,[tx for actor in actors for tx in actor.glob('round_*/proposal_*/transaction')])
write(snapshot/'binding.json',dict(source_sha256={str(f):sha(f) for f in attempt_files},resolved_native_batches=list(map(str,history)),vector_terminal=str(vector/'completion.json'),vector_terminal_sha256=sha(vector/'completion.json')))
results={}
for label,initial in [('direct_strict',original),('vector_then_strict',warm)]:
    assert all(sha(p)==h for p,h in bindings.items())
    command=[sys.executable,str(D/'run_independent_critical_portfolio_v5.py'),'--initial-state',str(initial),
        '--batch',str(root/label),'--query-graph',str(D/'bnn_physical_query_graph_01'),
        '--audit-cache',str(D/'rr_audit_cache_bnn_01'),'--policy','timing_under_resources',
        '--budget-mode','explicit_absolute','--fixed-limits',str(caps),'--fraction','.9']
    for tx in history:command+=['--reuse-native-batch',str(tx)]
    for actor in actors:
        for path in actor.glob('round_*/feedback/proposal/plan.json'):command+=['--reuse-plan',str(path)]
        for path in actor.glob('round_*/feedback/capacity'):command+=['--reuse-query-batch',str(path)]
        for path in actor.glob('round_*/exchange_expansion/completion.json'):command+=['--reuse-exchange',str(path)]
    start=time.monotonic()
    with (q/(label+'.log')).open('w') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',case=label,pid=child.pid,start_ticks=process_identity(child.pid)['start_ticks'],command=command))
        code=child.wait()
    completion=root/label/'completion.json'
    ok=code==0 and completion.exists() and read(completion)['passed']
    results[label]=dict(passed=ok,returncode=code,completion=str(completion),new_actor_process_seconds=time.monotonic()-start,initial_state=str(initial))
    write(q/'results.json',results)
    if not ok:break
    actor=root/label;actors.append(actor)
    history=resolve([actor/'attempts.json'],history)
write(q/'completion.json',dict(passed=len(results)==2 and all(x['passed'] for x in results.values()),results=results,
    original_state=str(original),vector_terminal_state=str(warm),fixed_resource_limits=read(caps),source_sha256=bindings,
    complete_single_configuration_algorithm_seconds=None,
    qualification='Development paired schedule comparison on one original physical input. Report vector phase and strict phase costs, historical reuse creation and new execution separately; no cold-time sum or independent sample inference.'))
write(q/'status.json',dict(status='terminal',passed=len(results)==2 and all(x['passed'] for x in results.values())))
