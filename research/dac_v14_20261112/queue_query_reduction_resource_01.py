"""Four development roles for connection-budget grouping after prior work."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'query_reduction_resource_dev_01';q=root/'queue';q.mkdir(parents=True,exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
prior=D/'complete_BNN_terminal_wire_flow_01/queue';owner=read(prior/'registration.json')
proof=D/'query_reduction_grouping_validation_01/completion.json'
assert read(proof)['passed'] and all(sha(p)==h for p,h in read(proof)['source_sha256'].items())
cases=['eltwise_A0_native','eltwise_A0_paired','bnn_A0_native','bnn_A0_paired']
configs={name:read(D/'stable_seed_transfer_dev_01'/name/'registration.json') for name in cases}
files=[Path(__file__).resolve(),D/'run_query_reduction_resource_repair_v1.py',D/'current_resource_connection_budget_v1.py',D/'current_resource_query_reduction_v1.py',D/'current_resource_bundle_v2.py',D/'budget64_fragmentation_analysis_01/completion.json',proof,prior/'registration.json']
for name in cases:
    base=D/'stable_seed_transfer_dev_01'/name
    assert read(base/'completion.json')['passed']
    assert configs[name]['seed_order']=='delay_rr_id'
    files += [base/'registration.json',base/'completion.json']
bindings={str(p):sha(p) for p in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    prerequisite=str(prior),prerequisite_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),
    fixed_order=cases,query_reduction_factor=2,connection_budget=64,net_cap=8,rank_windows=3,seed_order='delay_rr_id',
    source_sha256=bindings,
    selection='Keep K8 grouping unless complete-cut budget64 reduces proposed queries by at least factor2. Both possible groups preserve atomic cuts and current rank ordering. No circuit/net overrides. Recompute from own current state after every commit.',
    comparison='Original sealed K8 and budget64 fixed-seed actors provide matched input/seed/domain references; both own-current native and paired modes are run with the new grouping. Prior timings are historical imported observations, not contemporaneous speedup controls.',
    limits=dict(native_workers_parent_plus_child=2,concurrent_native_serial_slots=1,child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='Factor2development grouping heuristic motivated by actual77-to64fragmentation and identical2722totalqueries, not a calibrated runtime model; two known circuits; not an independent confirmation set or full cold timing. Actual native, FULLSTA, physical/domain and final context seals remain unchanged. No total trajectory step/call cap.'))
while True:
    actual=process_identity(owner['pid'])
    if not actual or actual['state']=='Z' or actual['start_ticks']!=owner['start_ticks']:break
    write(q/'status.json',dict(status='waiting_for_terminal_wire_full_flow_terminal',prerequisite_owner=actual));time.sleep(30)
if not (prior/'completion.json').exists():
    write(q/'completion.json',dict(passed=False,status='prerequisite_disappeared_without_terminal_receipt',native_calls=0));raise SystemExit(1)
phase=read(prior/'status.json')
if 'pid' in phase:
    actual=process_identity(phase['pid']);assert not actual or actual['state']=='Z' or actual['start_ticks']!=phase['start_ticks']
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX)
results={}
for name in cases:
    assert all(sha(p)==h for p,h in bindings.items())
    reg=configs[name];command=[sys.executable,str(D/'run_query_reduction_resource_repair_v1.py'),
        '--initial-state',reg['initial_state'],'--batch',str(root/name),
        '--full-graph-cache',reg['full_graph_cache'],'--bundle-size','8','--connection-budget','64',
        '--domain-mode',reg['domain_mode'],'--graph-echo','compact','--seed-order','delay_rr_id',
        '--accepted-steps','0','--rank-windows','3']
    if reg['domain_failure_release']:command+=['--domain-feedback']
    started=time.monotonic()
    with (q/(name+'.log')).open('w') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',case=name,pid=child.pid,start_ticks=process_identity(child.pid)['start_ticks'],command=command))
        code=child.wait()
    completion=root/name/'completion.json'
    ok=code==0 and completion.exists() and read(completion)['passed']
    results[name]=dict(passed=ok,returncode=code,completion=str(completion),actor_process_seconds=time.monotonic()-started)
    write(q/'results.json',results)
    if not ok:break
passed=len(results)==4 and all(r['passed'] for r in results.values())
write(q/'completion.json',dict(passed=passed,results=results,source_sha256=bindings,complete_single_configuration_algorithm_seconds=None,
    qualification='Four imported-state development trajectories; compare final quality, full imported cost and actual native connection workload without turning historical component counts into speedup. Preserve failures and all candidates.'))
write(q/'status.json',dict(status='terminal',passed=passed))
