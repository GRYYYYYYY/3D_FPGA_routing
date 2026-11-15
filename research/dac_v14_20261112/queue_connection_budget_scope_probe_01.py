"""Actual budget64 scope probe after current serial full-flow measurements."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'connection_budget_scope_probe_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
files=[Path(__file__).resolve(),root/'plan.json',D/'run_serial_guarded_resource_transactions_v1.py',D/'run_serial_fused_seed_analysis_v3.py',D/'run_serial_census_state_analysis_v1.py',D/'measure_process_tree_v1.py']
bindings={str(p):sha(p) for p in files};bindings.update(plan['source_sha256'])
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=bindings,scope=plan['qualification']))
prior=Path(plan['predecessor']);identity=read(prior/'registration.json')
while not (prior/'completion.json').exists():
    p=process_identity(identity['pid'])
    write(q/'status.json',dict(status='waiting_for_lazy_complete_measurement_terminal',predecessor=str(prior),verified_predecessor_live=bool(p and p['state']!='Z' and p['start_ticks']==identity['start_ticks'])))
    time.sleep(10)
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert all(sha(p)==h for p,h in bindings.items())
tx=Path(plan['transaction']);command=[sys.executable,str(D/'measure_process_tree_v1.py'),'--output',str(root/'measurement'),'--',sys.executable,str(D/'run_serial_guarded_resource_transactions_v1.py'),'--batch',str(tx)]
with (q/'execution.log').open('w') as log:
    proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    write(q/'status.json',dict(status='running',pid=proc.pid,start_ticks=process_identity(proc.pid)['start_ticks'],command=command))
    code=proc.wait()
measure=read(root/'measurement/completion.json');closed=read(tx/'completion.json') if (tx/'completion.json').exists() else None
passed=code==0 and measure['passed'] and closed is not None and closed['passed']
results={}
if passed:
    assert not measure['live_descendants_after_command_exit']
    for name,row in read(tx/'progress.json').items():
        assert row['status'] in ['legal_evaluated','transaction_failed_rolled_back']
        audit=read(tx/(name+'_audit/analysis.json'));assert audit['passed']
        before=read(Path(plan['reference_transaction'])/(name+'_decisions.json'))
        results[name]=dict(status=row['status'],planned_connections=plan['new_planned_connections'],actual_queries=len(audit['queries']),actual_search_attempts=len(audit['attempts']),
            query_core_seconds=sum(x['seconds'] for x in audit['queries']),historical_pooled_query_core_seconds=before['native_core_seconds'],
            CPD_ns=None if row['status']!='legal_evaluated' else row['cpd_s']*1e9,
            resources=row.get('resources'),resource_acceptance=row.get('policies',{}).get('resources_under_timing'),evaluation=row.get('evaluation'))
    files += [root/'measurement/completion.json',tx/'completion.json',tx/'progress.json']
    write(root/'completion.json',dict(passed=True,results=results,current_state=plan['current_state'],committed_to_any_actor=False,
        complete_imported_scope_seconds=measure['complete_command_wall_seconds'],
        sampled_tree_PSS_peak_kib=measure['sampled_tree_PSS_peak_kib'],missing_memory_observations=measure['missing_memory_observations'],
        source_sha256={str(p):sha(p) for p in files},qualification=plan['qualification']))
else:
    write(root/'completion.json',dict(passed=False,returncode=code,measurement=str(root/'measurement/completion.json'),transaction_terminal=None if closed is None else str(tx/'completion.json'),qualification=plan['qualification']))
write(q/'completion.json',dict(passed=passed,completion=str(root/'completion.json'),source_sha256=bindings))
write(q/'status.json',dict(status='terminal',passed=passed))
print(dict(passed=passed,results=results),flush=True)
