"""Continue two sealed 47-SB alternatives under one immutable timing envelope."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from seed_census_analysis_pool_v2 import process_identity
root=D/'budget47_current_timing_composition_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bindings=dict(plan['source_sha256']);bindings.update({str(p):sha(p) for p in [Path(__file__).resolve(),root/'plan.json']})
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=bindings,scope=plan['qualification']))
prior=Path(plan['predecessor']);owner=read(prior/'registration.json')
while not (prior/'completion.json').exists():
    p=process_identity(owner['pid'])
    write(q/'status.json',dict(status='waiting_for_architecture_transfer_terminal',predecessor=str(prior),verified_predecessor_live=bool(p and p['state']!='Z' and p['start_ticks']==owner['start_ticks'])))
    time.sleep(10)
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX|fcntl.LOCK_NB)
results={}
def invoke(command,tag):
    start=time.monotonic()
    with (q/(tag+'.log')).open('w') as log:
        child=subprocess.Popen(list(map(str,command)),stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',phase=tag,pid=child.pid,start_ticks=process_identity(child.pid)['start_ticks'],command=list(map(str,command))))
        code=child.wait()
    return code,time.monotonic()-start
for name in plan['fixed_order']:
    assert all(sha(p)==h for p,h in bindings.items())
    source=Path(plan['cases'][name]);case=root/name;case.mkdir();initial=case/'initial';actor=case/'timing'
    code,observe=invoke([sys.executable,D/'run_serial_census_state_analysis_v1.py','--source',run_dir(source),'--batch',initial,'--full-graph-cache',D/'full_route_graph_cache_bnn_01','--timing-echo','--fresh-physical-audit'],name+'_fresh_source_observation')
    ok=code==0 and (initial/'completion.json').exists() and read(initial/'completion.json')['passed']
    elapsed=None
    if ok:
        a,b=read(source/'endpoint_vector.json'),read(initial/'endpoint_vector.json')
        assert all(a[k]==b[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
        assert route_body(run_dir(source)/'routed.route')==route_body(run_dir(initial)/'routed.route')
        command=[sys.executable,D/'run_independent_critical_portfolio_v5.py','--initial-state',initial,'--batch',actor,'--query-graph',D/'bnn_physical_query_graph_01','--audit-cache',D/'rr_audit_cache_bnn_01','--policy','timing_under_resources','--budget-mode','explicit_absolute','--fixed-limits',root/'absolute_limits.json','--fraction','.9']
        code,elapsed=invoke(command,name+'_current_STA_timing')
        ok=code==0 and (actor/'completion.json').exists() and read(actor/'completion.json')['passed']
    results[name]=dict(passed=ok,returncode=code,original_source=str(source),initial_state=str(initial),timing_actor=str(actor),source_reobservation_seconds=observe,complete_timing_segment_process_seconds=elapsed,complete_fresh_route_algorithm_seconds=None)
    write(q/'results.json',results)
passed=len(results)==2 and all(r['passed'] for r in results.values())
write(q/'completion.json',dict(passed=passed,results=results,source_sha256=bindings,qualification=plan['qualification']))
write(q/'status.json',dict(status='terminal',passed=passed))
print(dict(passed=passed,results=results),flush=True)
