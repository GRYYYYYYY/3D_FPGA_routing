"""One owner after original CP1r3 raw admission; no automatic repeat."""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'vertical_cost_baseline_dev_01';q=root/'queue_priority_05';q.mkdir(exist_ok=False)
owner=(q/'owner.lock').open('w');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
plan=read(root/'execution_plan.json')
bound={**plan['source_sha256'],str(root/'execution_plan.json'):sha(root/'execution_plan.json'),
    str(D/'confirmation_priority_handoff_05/plan.json'):sha(D/'confirmation_priority_handoff_05/plan.json'),
    str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,
    predecessor=str(D/'CP1r3_raw_admission_01/queue_priority_04'),native_calls_launched=0))
def live(reg):
    p=process_identity(reg['pid']);return p and p['state']!='Z' and p['start_ticks']==reg['start_ticks']
try:
    pred=D/'CP1r3_raw_admission_01/queue_priority_04';reg=read(pred/'registration.json')
    while not (pred/'completion.json').exists():
        assert live(reg),'Predecessor missing without terminal receipt'
        write(q/'status.json',dict(status='waiting_for_CP1r3_raw_admission_terminal'));time.sleep(15)
    while live(reg):time.sleep(2)
    assert all(sha(p)==h for p,h in bound.items())
    with (D/'critical_scope_runner.lock').open('r') as serial:
        write(q/'status.json',dict(status='waiting_for_shared_serial_slot'))
        fcntl.flock(serial,fcntl.LOCK_EX)
        assert all(sha(p)==h for p,h in bound.items())
        assert not (root/'build').exists() and not (root/'execution').exists()
        start=time.monotonic()
        from run_vertical_cost_baseline_v2 import clean_environment
        with (q/'execution.log').open('x') as log:
            child=subprocess.Popen([sys.executable,'-B',str(D/'run_vertical_cost_baseline_v2.py'),
                '--batch',str(root/'execution'),'--serial-lock-fd',str(serial.fileno())],
                stdout=log,stderr=subprocess.STDOUT,pass_fds=(serial.fileno(),),env=clean_environment(os.environ))
            write(q/'status.json',dict(status='executing_registered_four_strength_control',**process_identity(child.pid)))
            code=child.wait()
        terminal=root/'execution/completion.json';result=read(terminal) if terminal.exists() else {}
        write(q/'completion.json',dict(passed=code==0 and result.get('all_roles_accounted',False),
            status='registered_baseline_attempt_terminal',returncode=code,complete_command_seconds=time.monotonic()-start,
            roles=result.get('roles',{}),zero_equivalence_passed=result.get('zero_equivalence_passed',False),
            source_sha256=bound,automatic_retry=False,research_complete=False))
        write(q/'status.json',dict(status='terminal'))
except BaseException as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),
        source_sha256=bound,automatic_retry=False,research_complete=False));raise
