from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
"""Defer engineering replay until all previously registered balanced timing completes."""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'empty_query_patch_validation_01';plan=read(root/'plan.json');q=root/'queue_priority_04';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(root/'plan.json'):sha(root/'plan.json'),**plan['source_sha256']}
bound.update({str(D/'confirmation_priority_handoff_02/plan.json'):sha(D/'confirmation_priority_handoff_02/plan.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())})
bound.update({str(D/'confirmation_priority_handoff_03/plan.json'):sha(D/'confirmation_priority_handoff_03/plan.json')})
bound.update({str(D/'confirmation_priority_handoff_04/plan.json'):sha(D/'confirmation_priority_handoff_04/plan.json')})
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,native_calls_new=0))
try:
    predecessor=D/'interrupted_flow_recovery_01/queue_priority_04';reg=read(predecessor/'registration.json')
    while not (predecessor/'completion.json').exists():
        p=process_identity(reg['pid']);assert p and p['state']!='Z' and p['start_ticks']==reg['start_ticks']
        write(q/'status.json',dict(status='waiting_for_priority_confirmation_and_recoveries'))
        time.sleep(15)
    done=read(predecessor/'completion.json');assert done['status']=='registered_four_arm_recovery_terminal'
    serial=(D/'critical_scope_runner.lock').open('r');write(q/'status.json',dict(status='waiting_for_shared_serial_slot_readonly_replay'));fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(f)==h for f,h in bound.items())
    with (q/'validation.log').open('x') as log:
        p=subprocess.Popen([sys.executable,str(D/'validate_empty_query_patch_01.py')],stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='readonly_replay_running',**process_identity(p.pid)));code=p.wait()
    assert code==0 and read(root/'completion.json')['passed']
    write(q/'completion.json',dict(passed=True,status='registered_empty_query_replay_terminal',native_calls_new=0,report=str(root/'completion.json'),source_sha256=bound))
    write(q/'status.json',dict(status='terminal'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),source_sha256=bound,native_calls_new=0));raise
