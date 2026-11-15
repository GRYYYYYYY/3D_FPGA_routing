"""Wait for all current experiment chains, then measure fresh complete flows."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha,route_body
from seed_census_analysis_pool_v2 import process_identity

for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import run_complete_route_resource_flow_v1  # Bind imported repository audit/IO modules too.

root=D/'complete_route_resource_measurements_02';plan=read(root/'plan.json')
assert plan['passed'] and all(sha(p)==h for p,h in plan['source_sha256'].items())
proof=D/'process_tree_measurement_validation_01/completion.json'
assert read(proof)['passed'] and all(sha(p)==h for p,h in read(proof)['source_sha256'].items())
q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
names=['stable_seed_transfer_recovery_02','direct_scope_resource_equivalence_recovery_02',
       'native_census_resource_equivalence_recovery_02','native_checkpoint_recovery_02','rejection_feedback_controller_dev_01']
dependencies={n:read(D/n/'queue/registration.json') for n in names}
source_files=[Path(__file__).resolve(),root/'plan.json',proof]
for module in list(sys.modules.values()):
    file=getattr(module,'__file__',None)
    if file:
        path=Path(file).resolve()
        if path.suffix=='.py' and path.is_relative_to(D.parents[1]):source_files.append(path)
bindings={str(p):sha(p) for p in source_files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    prerequisites={n:dict(pid=d['pid'],start_ticks=d['start_ticks']) for n,d in dependencies.items()},
    fixed_order=plan['fixed_order'],source_sha256=bindings,
    limits=dict(this_chain_parent_plus_child=2,concurrent_other_registered_native_owners=0,child_seconds=1800,
        memory_bytes_per_process=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='One tiny validation followed by four fixed complete-configuration development observations. Wait for authoritative terminal receipts and absent live handles of ALL current chains; never restart them to make a benchmark slot. This is fresh-process timing, not disk-cache coldness, a repeated formal speedup test, or a research stopping boundary.'))
while True:
    live=[];missing=[]
    for name,owner in dependencies.items():
        actual=process_identity(owner['pid'])
        if actual and actual['state']!='Z' and actual['start_ticks']==owner['start_ticks']:live.append(name)
        elif not (D/name/'queue/completion.json').exists():missing.append(name)
    write(q/'status.json',dict(status='waiting_for_all_registered_chains_terminal',live_dependencies=live,missing_terminal_receipts=missing))
    if missing:
        write(q/'completion.json',dict(passed=False,status='dependency_disappeared_without_receipt_requires_reconciliation',missing=missing,native_calls=0))
        raise SystemExit(1)
    if not live:break
    time.sleep(30)
# A disappeared child with a stale running parent status must not overlap timing.
for name in names:
    phase=read(D/name/'queue/status.json')
    if 'pid' in phase:
        actual=process_identity(phase['pid'])
        assert not actual or actual['state']=='Z' or actual['start_ticks']!=phase['start_ticks']
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX)
assert read(D/'native_checkpoint_recovery_02/queue/completion.json')['passed'],'Checkpoint recovery must seal before full measurements'
results={}
for name in plan['fixed_order']:
    assert all(sha(p)==h for p,h in bindings.items())
    assert all(sha(p)==h for p,h in plan['source_sha256'].items())
    case=root/name;case.mkdir()
    command=[sys.executable,str(D/'measure_process_tree_v1.py'),'--output',str(case/'measurement'),'--',
        sys.executable,str(D/'run_complete_route_resource_flow_v1.py'),'--config',plan['cases'][name],'--output',str(case/'flow')]
    write(case/'host_context_before.json',dict(load_average=os.getloadavg(),cpu_affinity=sorted(os.sched_getaffinity(0)),hostname=os.uname().nodename))
    with (q/(name+'.log')).open('w') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',case=name,pid=child.pid,start_ticks=process_identity(child.pid)['start_ticks'],command=command))
        code=child.wait()
    measure=case/'measurement/completion.json';flow=case/'flow/completion.json'
    passed=code==0 and measure.exists() and flow.exists() and read(measure)['passed'] and read(flow)['passed']
    results[name]=dict(passed=passed,returncode=code,measurement=str(measure),flow=str(flow),
        complete_wall_seconds=read(measure)['complete_command_wall_seconds'] if measure.exists() else None)
    write(q/'results.json',results)
    if not passed:break
comparisons={}
if len(results)==len(plan['fixed_order']) and all(r['passed'] for r in results.values()):
    vectors=[];initials=[]
    for mode in ['unrestricted','paired']:
        cold=read(root/f'eltwise_build_inside_flow_{mode}/flow/completion.json')
        warm=read(root/f'eltwise_reusable_graph_only_{mode}/flow/completion.json')
        a,b=Path(cold['final_state']),Path(warm['final_state'])
        va,vb=read(a/'endpoint_vector.json'),read(b/'endpoint_vector.json')
        ca,cb=read(a/'completion.json'),read(b/'completion.json')
        checks=dict(final_full_vector_exact=all(va[k]==vb[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']),
            final_resources_exact=cold['final_resources']==warm['final_resources'],
            final_ordered_route_body_exact=route_body(Path(ca['run'])/'routed.route')==route_body(Path(cb['run'])/'routed.route'))
        comparisons[mode]=dict(passed=all(checks.values()),checks=checks)
        initials += [Path(cold['initial_state']),Path(warm['initial_state'])]
    initial_vectors=[read(p/'endpoint_vector.json') for p in initials]
    comparisons['initial_roots']=dict(passed=all(all(v[k]==initial_vectors[0][k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']) for v in initial_vectors)
        and len({route_body(Path(read(p/'completion.json')['run'])/'routed.route') for p in initials})==1)
passed=len(results)==len(plan['fixed_order']) and all(v['passed'] for v in results.values()) and all(v['passed'] for v in comparisons.values())
write(q/'completion.json',dict(passed=passed,results=results,cache_mode_equivalence=comparisons,
    source_sha256=bindings,
    qualification='One observation per fixed configuration, not independent circuits/repeats or statistical speedup. Tiny validation cost stays separate. Every reported wall/memory/quality comes from its own exact complete execution. Preserve failures and cache-mode mismatches.'))
write(q/'status.json',dict(status='terminal',passed=passed))
