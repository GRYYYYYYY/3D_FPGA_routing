"""Actual graph-only reuse development roles, paired then unrestricted."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'complete_serial_reusable_graph_dev_01';q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX|fcntl.LOCK_NB)
files=[Path(__file__).resolve(),D/'run_complete_serial_resource_flow_v1.py',D/'run_serial_current_resource_repair_v3.py',D/'run_serial_resource_transactions_v4.py',D/'measure_process_tree_v1.py',D/'verify_complete_serial_flow_v2.py',D/'complete_serial_pair_comparison_01.json',*sorted((root/'configs').glob('*.json'))]
bindings={str(f):sha(f) for f in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],fixed_order=['paired','unrestricted'],source_sha256=bindings,
    scope='Fresh route plus full serial repair, supplied graph-only indexes. Reverse policy order relative to the completed build-inside pair. No native/candidate/query result reuse. One additional VPR alongside current at-most-two-process pool. Single development observations; compare exact outputs before time interpretation.'))
results={}
for mode in ['paired','unrestricted']:
    assert all(sha(f)==h for f,h in bindings.items())
    case=root/mode;case.mkdir();(case/'queue').mkdir();config=root/'configs'/(mode+'.json')
    command=[sys.executable,str(D/'measure_process_tree_v1.py'),'--output',str(case/'measurement'),'--',sys.executable,str(D/'run_complete_serial_resource_flow_v1.py'),'--config',str(config),'--output',str(case/'flow')]
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
            code=subprocess.run([sys.executable,str(D/'verify_complete_serial_flow_v2.py'),'--root',str(case),'--cache-mode','reusable_graph_only'],stdout=log,stderr=subprocess.STDOUT).returncode
        ok=code==0
    results[mode]=dict(passed=ok,returncode=code,completion=str(case/'completion.json'))
    write(q/'results.json',results)
    if not ok:break
passed=len(results)==2 and all(r['passed'] for r in results.values())
write(q/'completion.json',dict(passed=passed,results=results,source_sha256=bindings))
write(q/'status.json',dict(status='terminal',passed=passed))
