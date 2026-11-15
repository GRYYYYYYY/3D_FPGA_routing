"""Read-only terminal quality/time analysis, separate from experiment scheduling."""
import fcntl,os,subprocess,sys,time,traceback
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'orphaned_BNN_quality_analysis_01';root.mkdir(exist_ok=True)
lock=(root/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not (root/'registration.json').exists() and not (root/'completion.json').exists()
preflight=D/'orphaned_BNN_quality_preflight_01/completion.json';assert read(preflight)['passed']
files=[Path(__file__).resolve(),D/'verify_orphaned_BNN_quality_v1.py',D/'orphaned_flow_time_evidence_v1.py',preflight]
bound={str(f):sha(f) for f in files};identity=process_identity(os.getpid())
write(root/'registration.json',dict(pid=os.getpid(),start_ticks=identity['start_ticks'],source_sha256=bound,
    native_calls_planned=0,scheduling_owner=False,predecessor='supervision_recovery_20261115_01/completion.json'))
try:
    predecessor=D/'supervision_recovery_20261115_01/completion.json'
    while not predecessor.exists():
        write(root/'status.json',dict(status='waiting_for_original_terminal_receipt',native_calls=0));time.sleep(15)
    terminal=read(predecessor);assert terminal['passed'],terminal
    assert all(sha(f)==h for f,h in bound.items())
    case=D/'complete_BNN_closed_stream_flow_01/bnn_native_closed_stream'
    if not (case/'flow/completion.json').exists():
        write(root/'completion.json',dict(passed=False,status='original_flow_terminated_without_complete_flow_receipt',
            VPR_calls_new=0,source_sha256=bound,qualification='Actual failure retained; no quality or original observer completion invented.'))
        write(root/'status.json',dict(status='terminal',passed=False));raise SystemExit(0)
    command=[sys.executable,str(D/'verify_orphaned_BNN_quality_v1.py'),'--root',str(case),'--output',str(root/'verification')]
    with (root/'verification.log').open('x') as stream:
        child=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT)
        child_identity=process_identity(child.pid)
        write(root/'status.json',dict(status='verifying_actual_full_quality_and_original_time',pid=child.pid,start_ticks=child_identity['start_ticks'],command=command))
        code=child.wait()
    write(root/'completion.json',dict(passed=code==0,status='read_only_verification_terminal',returncode=code,
        verification=str(root/'verification/completion.json') if code==0 else None,VPR_calls_new=0,
        full_observer_measurement_reconstructed=False,source_sha256=bound,
        qualification='No original experiment receipt altered; original complete quality and GNU-time fields separated from unrecoverable observer gaps. Downstream equivalence comparison remains separate.'))
    write(root/'status.json',dict(status='terminal',passed=code==0))
except Exception as exc:
    write(root/'completion.json',dict(passed=False,status='read_only_analysis_failed',error=repr(exc),VPR_calls_new=0,source_sha256=bound))
    write(root/'status.json',dict(status='terminal',passed=False));traceback.print_exc();raise
