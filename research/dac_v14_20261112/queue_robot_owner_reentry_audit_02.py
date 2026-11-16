"""Single readonly audit of completed work; wait behind existing serial owners."""
import fcntl
import os
import subprocess
import sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'robot_owner_reentry_audit_02';q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
files=[Path(__file__).resolve(),D/'audit_robot_owner_reentry_02.py',D/'observation_timing_identity_v2.py',root/'plan.json']
bound={str(p):sha(p) for p in files}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,native_calls_new=0))
try:
    original=read(D/'robot_p1_input_contract_pair_02/queue/registration.json');live=process_identity(original['pid'])
    assert not live or live['state']=='Z' or live['start_ticks']!=original['start_ticks']
    assert read(D/'execution_reconciliation_20261116_01/completion.json')['passed']
    serial=(D/'critical_scope_runner.lock').open('r')
    write(q/'status.json',dict(status='waiting_for_shared_serial_slot_readonly_audit'))
    fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(p)==h for p,h in bound.items())
    with (q/'audit.log').open('x') as log:
        child=subprocess.Popen([sys.executable,str(D/'audit_robot_owner_reentry_02.py')],stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='readonly_audit_running',**process_identity(child.pid)))
        code=child.wait()
    assert code==0 and read(root/'completion.json')['passed']
    write(q/'completion.json',dict(passed=True,status='registered_readonly_audit_terminal',native_calls_new=0,source_sha256=bound,report=str(root/'completion.json')))
    write(q/'status.json',dict(status='terminal'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),source_sha256=bound,native_calls_new=0))
    raise
