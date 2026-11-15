"""Full current-binary explicit-seed resource development configurations."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'complete_serial_fused_dev_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert read(D/'serial_fused_serialization_validation_01/completion.json')['passed']
files=[D/'run_serial_fused_seed_analysis_v2.py',D/'materialize_serial_fused_candidate_v3.py',D/'verify_complete_serial_fused_policy_v1.py',Path(__file__).resolve(),D/'run_complete_serial_fused_flow_v1.py',D/'run_serial_fused_resource_repair_v1.py',D/'run_serial_fused_resource_transactions_v1.py',D/'measure_process_tree_v1.py',D/'verify_complete_serial_fused_flow_v1.py',root/'plan.json',D/'serial_fused_serialization_validation_01/completion.json',*sorted((root/'configs').glob('*.json'))]
bindings={str(f):sha(f) for f in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],fixed_order=plan['fixed_order'],source_sha256=bindings,
    scope='Fresh route plus full current-binary serial repair; graph indexes built inside. One fixed seed/domain configuration with actual candidate callback and counted empty source controls. No native/candidate/query result reuse. One additional VPR alongside current at-most-two-process pool. Single development observations; compare exact outputs before time interpretation.'))
results={}
for mode in plan['fixed_order']:
    assert all(sha(f)==h for f,h in bindings.items())
    case=root/mode;case.mkdir();(case/'queue').mkdir();config=Path(plan['cases'][mode]);(case/'config.json').write_bytes(config.read_bytes())
    command=[sys.executable,str(D/'measure_process_tree_v1.py'),'--output',str(case/'measurement'),'--',sys.executable,str(D/'run_complete_serial_fused_flow_v1.py'),'--config',str(config),'--output',str(case/'flow')]
    with (q/(mode+'.log')).open('w') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        # Per-case verifier checks the actual measurement owner as well.
        write(case/'queue/registration.json',dict(pid=child.pid,start_ticks=process_identity(child.pid)['start_ticks'],command=command,source_sha256=bindings))
        write(q/'status.json',dict(status='running',case=mode,pid=child.pid,start_ticks=process_identity(child.pid)['start_ticks'],command=command))
        code=child.wait()
    measure=case/'measurement/completion.json';flow=case/'flow/completion.json'
    ok=code==0 and measure.exists() and flow.exists() and read(measure)['passed'] and read(flow)['passed']
    if ok:
        with (q/(mode+'_verification.log')).open('w') as log:
            code=subprocess.run([sys.executable,str(D/'verify_complete_serial_fused_flow_v1.py'),'--root',str(case),'--cache-mode','build_inside_flow'],stdout=log,stderr=subprocess.STDOUT).returncode
        ok=code==0
    if ok:
        with (q/(mode+'_policy_verification.log')).open('w') as log:
            code=subprocess.run([sys.executable,str(D/'verify_complete_serial_fused_policy_v1.py'),'--root',str(case)],stdout=log,stderr=subprocess.STDOUT).returncode
        ok=code==0
    results[mode]=dict(passed=ok,returncode=code,completion=str(case/'completion.json'))
    write(q/'results.json',results)
    if not ok:break
passed=len(results)==1 and all(r['passed'] for r in results.values())
write(q/'completion.json',dict(passed=passed,results=results,source_sha256=bindings))
write(q/'status.json',dict(status='terminal',passed=passed))
