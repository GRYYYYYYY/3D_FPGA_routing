"""Replay all four actual eltwise paired roles with standalone candidate callbacks."""
import collections,fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from seed_census_analysis_pool_v2 import process_identity
from materialize_serial_fused_candidate_v1 import materialize
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace
from coordinated_repair_tree import from_trace

root=D/'serial_fused_candidate_validation_01';root.mkdir(exist_ok=False)
lock=(D/'critical_scope_runner.lock').open('r');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
reference=D/'complete_serial_seed_policy_dev_01/delay_seed_paired';proof=read(reference/'explicit_policy_verification.json');assert proof['passed']
assert all(sha(f)==h for f,h in proof['source_sha256'].items())
cache=reference/'flow/full_graph_cache';audit_cache=reference/'flow/graph_audit_cache'
files=[Path(__file__).resolve(),D/'run_serial_fused_seed_analysis_v1.py',D/'materialize_serial_fused_candidate_v1.py',reference/'explicit_policy_verification.json',D/'native_resource_census_stage_01/binding.json']
bindings={str(f):sha(f) for f in files}
write(root/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=bindings,
    scope='Four already-completed same-source transactions from one eltwise trajectory, including rejected OFF roles. One standalone native process at a time; dedicated actual candidate callback versus recorded separate same-binary LOAD/STA. Component integration validation, not full-flow timing.'))
costs=[];results=[];write(root/'results.json',results)
def invoke(script,args,tag):
    command=[sys.executable,str(D/script),*map(str,args)];start=time.monotonic()
    with (root/(tag+'.log')).open('w') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write(root/'active_child.json',dict(pid=child.pid,start_ticks=process_identity(child.pid)['start_ticks'],command=command))
        try:code=child.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            import signal
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise
    costs.append(dict(tag=tag,returncode=code,complete_process_seconds=time.monotonic()-start));write(root/'process_costs.json',costs)
    assert code==0,(tag,code)
def structure(path):
    return {n:from_trace(v['trace'],collections.defaultdict(float)) if v['trace'] else None for n,v in read_trace(path).items()}
for index,attempt in enumerate(read(reference/'flow/repair/attempts.json')):
    old=Path(attempt['transaction']);tx=root/f'transaction_{index:02d}';tx.mkdir()
    (tx/'registration.json').write_bytes((old/'registration.json').read_bytes());roles=read(tx/'registration.json')['roles']
    for name,prior in read(old/'progress.json').items():
        assert prior['status']=='legal_evaluated';role=roles[name]
        args=['--source',role['source'],'--batch',tx/name,'--native-cases',role['request'],'--objective',role['objective'],'--seed-order',role['seed_order'],'--candidate-full-sta']
        if role.get('crossing_reuse_enabled'):args += ['--crossing-domain',role['crossing_domain']]
        if role.get('domain_failure_release'):args += ['--domain-feedback']
        tag=f'{index:02d}_{name}'
        invoke('run_serial_fused_seed_analysis_v1.py',args,tag+'_native')
        invoke('audit_native_feedback_objective_cached.py',['--batch',tx,'--role',name,'--cache',audit_cache,'--output',tx/(name+'_audit')],tag+'_scope')
        invoke('audit_failure_release_domain.py' if role.get('domain_failure_release') else 'audit_retained_crossing_domain.py',['--batch',tx,'--role',name],tag+'_domain')
        evaluation=tx/(name+'_evaluation');materialize(tx/name,evaluation,cache)
        native=Path(read(tx/name/'candidate_exports.json')['candidate']);audited=Path(read(tx/(name+'_audit/analysis.json'))['candidate_route'])
        assert structure(native/'routed.route')==structure(audited)
        expected=Path(prior['evaluation']);a,b=read(evaluation/'endpoint_vector.json'),read(expected/'endpoint_vector.json')
        vector_exact=all(a[k]==b[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
        body_exact=route_body(run_dir(evaluation)/'routed.route')==route_body(run_dir(expected)/'routed.route')
        physical_exact=read(run_dir(evaluation)/'independent_audit.json')['physical_metrics']==read(run_dir(expected)/'independent_audit.json')['physical_metrics']
        row=dict(role=name,transaction=index,reference=str(expected),actual=str(evaluation),full_vector_exact=vector_exact,ordered_route_body_exact=body_exact,physical_exact=physical_exact)
        results.append(row);write(root/'results.json',results)
        assert vector_exact and physical_exact,row
        files += [old/'progress.json',old/'registration.json',tx/name/'completion.json',tx/name/'candidate_exports.json',tx/(name+'_audit/analysis.json'),evaluation/'completion.json']
assert len(results)==4 and all(sha(f)==h for f,h in bindings.items())
write(root/'completion.json',dict(passed=True,results=results,native_processes=4,additional_candidate_analysis_processes=0,
    all_ordered_route_bodies_exact=all(r['ordered_route_body_exact'] for r in results),
    source_sha256={str(f):sha(f) for f in files},
    qualification='Actual standalone callback FULL/fresh STA and independently audited physical/scope/domain candidate match all four recorded separate-LOAD controls in complete endpoint vectors and physical resources. Exact source route/vector restoration checked in every worker. Existing circuit/trajectory, not independent transfer, positive domain-release coverage or full-configuration speedup.'))
print(dict(passed=True,roles=len(results),ordered_routes_exact=all(r['ordered_route_body_exact'] for r in results)),flush=True)
