from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
"""Audit four old prefixes once, after the already registered confirmation cohort."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'interrupted_stage_reconciliation_01';plan=read(root/'plan.json')
q=root/'queue_priority_03';q.mkdir(exist_ok=False)
owner=(q/'owner.lock').open('w');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(root/'plan.json'):sha(root/'plan.json'),**plan['source_sha256']}
bound.update({str(D/'confirmation_priority_handoff_02/plan.json'):sha(D/'confirmation_priority_handoff_02/plan.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())})
bound.update({str(D/'confirmation_priority_handoff_03/plan.json'):sha(D/'confirmation_priority_handoff_03/plan.json')})
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,new_native_calls=0))
try:
    pred=D/'CP1r3_supplemental_verifier_01/queue_priority_03';reg=read(pred/'registration.json')
    while not (pred/'completion.json').exists():
        live=process_identity(reg['pid']);assert live and live['state']!='Z' and live['start_ticks']==reg['start_ticks']
        write(q/'status.json',dict(status='waiting_for_registered_distinct_confirmation_cohort'));time.sleep(15)
    # Readonly reconciliation can follow scientific negatives and recorded
    # infrastructure failures alike, once the predecessor truly relinquished
    # its slot. It launches no experiments from the failed predecessor.
    live=process_identity(reg['pid'])
    while live and live['state']!='Z' and live['start_ticks']==reg['start_ticks']:
        time.sleep(2);live=process_identity(reg['pid'])
    serial=(D/'critical_scope_runner.lock').open('r')
    write(q/'status.json',dict(status='waiting_for_shared_serial_slot_readonly_stage_audit'))
    fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(p)==h for p,h in bound.items())
    env={**os.environ,'H3D_INTERRUPTED_AUDIT_SERIAL_OWNER':str(os.getpid()),'PYTHONDONTWRITEBYTECODE':'1'}
    before=time.monotonic()
    with (q/'audit.log').open('x') as log:
        child=subprocess.Popen([sys.executable,str(D/'audit_interrupted_stages_01.py')],stdout=log,stderr=subprocess.STDOUT,env=env)
        write(q/'status.json',dict(status='readonly_stage_byte_and_STA_audit',**process_identity(child.pid)))
        code=child.wait()
    result=read(root/'completion.json') if (root/'completion.json').exists() else {}
    passed=code==0 and result.get('passed',False)
    write(q/'completion.json',dict(passed=passed,status='registered_readonly_stage_audit_terminal' if passed else 'reconciliation_required',
        returncode=code,complete_audit_seconds=time.monotonic()-before,new_native_calls=0,source_sha256=bound,
        original_receipts_changed=False,no_automatic_retry=True,research_complete=False))
    write(q/'status.json',dict(status='terminal' if passed else 'reconciliation_required'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),source_sha256=bound,new_native_calls=0,no_automatic_retry=True))
    raise
