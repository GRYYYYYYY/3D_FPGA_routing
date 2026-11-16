"""Only readonly verification of finished native work, under the original serial lock."""
import fcntl
import os
import subprocess
import sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'robot_union_verification_recovery_01';q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
original=D/'robot_union_mechanism_02'
files=[Path(__file__).resolve(),D/'verify_robot_union_mechanism_02_v2.py',original/'plan.json',original/'queue/completion.json',original/'supervision.json',original/'measurement/completion.json',original/'transaction/completion.json']
bound={str(p):sha(p) for p in files}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,native_calls_new=0))
try:
    reg=read(original/'queue/registration.json');live=process_identity(reg['pid'])
    assert not live or live['state']=='Z' or live['start_ticks']!=reg['start_ticks']
    assert read(original/'queue/completion.json')['status']=='reconciliation_required'
    assert read(original/'supervision.json')['passed'] and not read(original/'supervision.json')['residual_descendants']
    serial=(D/'critical_scope_runner.lock').open('r')
    write(q/'status.json',dict(status='waiting_for_shared_serial_slot_readonly_audit'))
    fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(p)==h for p,h in bound.items())
    with (q/'verification.log').open('x') as log:
        p=subprocess.Popen([sys.executable,str(D/'verify_robot_union_mechanism_02_v2.py')],stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='readonly_verification_running',**process_identity(p.pid)))
        code=p.wait()
    assert code==0 and read(original/'verification_v2.json')['passed']
    write(q/'completion.json',dict(passed=True,status='registered_union_mechanism_terminal',native_calls_new=0,original_execution_returncode=0,verification=str(original/'verification_v2.json'),source_sha256=bound,qualification='Correct compact disabled-domain/rollback schema handling; raw trace/query/attempt/byte restoration checks retained. Original execution and failed verifier receipts untouched; no rerouting.'))
    write(q/'status.json',dict(status='terminal'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',native_calls_new=0,error=repr(error),source_sha256=bound))
    raise
