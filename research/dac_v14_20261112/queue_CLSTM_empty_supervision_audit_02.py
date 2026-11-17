"""Independent empty-supervision stage audit after baseline reconciliation; no native calls."""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'CLSTM_domain_empty_supervision_audit_02';q=root/'queue';q.mkdir(exist_ok=False)
owner=(q/'owner.lock').open('w');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
plan=read(root/'execution_plan.json')
bound={**plan['source_sha256'],str(root/'execution_plan.json'):sha(root/'execution_plan.json'),
    
    str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,
    predecessor=str(D/'vertical_cost_admission_reconciliation_01/execution'),native_calls_launched=0))
def live(reg):
    p=process_identity(reg['pid']);return p and p['state']!='Z' and p['start_ticks']==reg['start_ticks']
try:
    pred=D/'vertical_cost_admission_reconciliation_01/execution';reg=read(pred/'registration.json')
    while not (pred/'completion.json').exists():
        assert live(reg),'Predecessor missing without terminal receipt'
        write(q/'status.json',dict(status='waiting_for_original_baseline_reconciliation_terminal'));time.sleep(15)
    while live(reg):time.sleep(2)
    assert all(sha(p)==h for p,h in bound.items())
    with (D/'critical_scope_runner.lock').open('r') as serial:
        write(q/'status.json',dict(status='waiting_for_shared_serial_slot'))
        fcntl.flock(serial,fcntl.LOCK_EX)
        assert all(sha(p)==h for p,h in bound.items())
        assert not (root/'audit.json').exists()
        start=time.monotonic()
        from run_vertical_cost_baseline_v2 import clean_environment
        with (q/'execution.log').open('x') as log:
            child=subprocess.Popen([sys.executable,'-B',str(D/'audit_interrupted_clstm_domain_02.py'),
                '--execute','--serial-lock-fd',str(serial.fileno())],
                stdout=log,stderr=subprocess.STDOUT,pass_fds=(serial.fileno(),),env=clean_environment(os.environ))
            write(q/'status.json',dict(status='readonly_existing_CLSTM_native_stage_audit',**process_identity(child.pid)))
            code=child.wait()
        terminal=root/'audit.json';result=read(terminal) if terminal.exists() else {}
        write(q/'completion.json',dict(passed=code==0 and result.get('passed',False),
            status='registered_empty_receipt_audit_terminal',returncode=code,complete_command_seconds=time.monotonic()-start,
            complete_candidate_admitted=False,full_method_complete=False,new_native_or_STA_calls=0,
            source_sha256=bound,automatic_retry=False,research_complete=False))
        write(q/'status.json',dict(status='terminal'))
except BaseException as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),
        source_sha256=bound,automatic_retry=False,research_complete=False));raise
