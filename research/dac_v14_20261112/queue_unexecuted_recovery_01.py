"""Resume only never-executed tasks; preserve all original queue receipts."""
import fcntl, os, subprocess, sys, time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'unexecuted_recovery_20261115_01'; q=root/'queue'
q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
plan=read(root/'plan.json'); bound=plan['source_sha256']
assert all(sha(f)==h for f,h in bound.items())
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=bound))

def wait_for(directory):
    directory=Path(directory); reg=read(directory/'registration.json')
    while not (directory/'completion.json').exists():
        p=process_identity(reg['pid'])
        if not p or p['state']=='Z' or p['start_ticks']!=reg['start_ticks']:
            raise RuntimeError('Predecessor missing without receipt: '+str(directory))
        write(q/'status.json',dict(status='waiting_for_registered_predecessor',predecessor=str(directory)))
        time.sleep(15)

def run(tag,command):
    start=time.monotonic()
    with (q/(tag+'.log')).open('w') as log:
        child=subprocess.Popen(list(map(str,command)),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        identity=process_identity(child.pid)
        write(q/'status.json',dict(status='running',phase=tag,pid=child.pid,start_ticks=identity['start_ticks']))
        code=child.wait()
    return dict(returncode=code,command=list(map(str,command)),complete_imported_component_seconds=time.monotonic()-start)

try:
    # The watcher keeps the existing solver alive and releases the original queue.
    wait_for(D/'supervision_recovery_20261115_01')
    wait_for(D/'query_reduction_resource_dev_01/queue')
    write(q/'status.json',dict(status='waiting_for_shared_serial_slot'))
    serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(f)==h for f,h in bound.items())
    results={}
    b=D/'BNN_wire_timing_native_validation_01'; bp=read(b/'plan.json')
    assert not any((b/x).exists() for x in ['measurement','candidate_evaluation','verification.json'])
    command=[sys.executable,D/'measure_process_tree_v1.py','--output',b/'measurement','--',sys.executable,D/'run_independent_timing_cone_analysis_stream_v1.py','--source',bp['source_run'],'--batch',b/'candidate_evaluation','--candidate-route',bp['candidate_route'],'--full-graph-cache',bp['full_graph_cache'],'--timing-echo']
    result=run('BNN_fixed_composition_LOAD',command)
    result.update(command_passed=result['returncode']==0 and (b/'candidate_evaluation/completion.json').exists() and read(b/'candidate_evaluation/completion.json')['passed'],source_sha256=bound)
    receipt=q/'BNN_execution_receipt.json';write(receipt,result)
    checked=run('BNN_verify',[sys.executable,D/'verify_BNN_wire_timing_native_validation_v2.py','--execution-receipt',receipt])
    results['BNN_composition']=dict(execution=result,verification=checked)
    write(q/'results.json',results)
    b=D/'robot_domain_release_ablation_01';tx=b/'transaction'
    assert not tx.exists() and not (b/'verification.json').exists()
    tx.mkdir();(tx/'registration.json').write_bytes((b/'prepared_transaction_registration.json').read_bytes())
    result=run('robot_no_release',[sys.executable,D/'run_serial_single_resource_scope_v1.py','--batch',tx])
    receipt=q/'robot_execution_receipt.json';write(receipt,result)
    checked=run('robot_verify',[sys.executable,D/'verify_robot_domain_release_ablation_v2.py','--execution-receipt',receipt]) if result['returncode']==0 else None
    results['robot_release']=dict(execution=result,verification=checked);write(q/'results.json',results)
    b=D/'complete_BNN_terminal_wire_flow_01';bp=read(b/'plan.json');case=b/'bnn_native_terminal_wire'
    assert not case.exists();case.mkdir();(case/'queue').mkdir();(case/'config.json').write_bytes(Path(bp['config']).read_bytes())
    command=[sys.executable,D/'measure_process_tree_v1.py','--output',case/'measurement','--',sys.executable,D/'run_complete_resource_terminal_wire_timing_v1.py','--config',bp['config'],'--output',case/'flow']
    # Case verification checks the measured command's exact process identity.
    start=time.monotonic()
    with (q/'terminal_wire.log').open('w') as log:
        child=subprocess.Popen(list(map(str,command)),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        identity=process_identity(child.pid)
        write(case/'queue/registration.json',dict(pid=child.pid,start_ticks=identity['start_ticks'],command=list(map(str,command)),source_sha256=bound))
        write(q/'status.json',dict(status='running',phase='terminal_wire_full_flow',pid=child.pid,start_ticks=identity['start_ticks']))
        code=child.wait()
    checked=run('terminal_wire_verify',[sys.executable,D/'verify_complete_resource_terminal_wire_timing_v1.py','--root',case]) if code==0 else None
    results['terminal_wire']=dict(returncode=code,verification=checked,baseline_comparison='pending separate qualified comparison; original observer was lost; no old whole measurement fabricated')
    write(q/'results.json',results)
    passed=all(v.get('verification') is not None and v['verification']['returncode']==0 for v in results.values())
    write(q/'completion.json',dict(passed=passed,status='registered_never_executed_tasks_terminal',results=results,source_sha256=bound))
    write(q/'status.json',dict(status='terminal',passed=passed))
except Exception as exc:
    write(q/'completion.json',dict(passed=False,status='recovery_stopped_for_reconciliation',error=repr(exc),source_sha256=bound))
    raise
