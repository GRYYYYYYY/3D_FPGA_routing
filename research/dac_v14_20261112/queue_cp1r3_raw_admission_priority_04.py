"""Read-only remaining admission, immediately after original-check replay."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'CP1r3_raw_admission_01';q=root/'queue_priority_04';q.mkdir(exist_ok=False)
owner=(q/'owner.lock').open('w');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
plan=read(root/'plan.json')
bound={str(root/'plan.json'):sha(root/'plan.json'),**plan['source_sha256'],
    str(D/'confirmation_priority_handoff_04/plan.json'):sha(D/'confirmation_priority_handoff_04/plan.json'),
    str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,new_native_or_STA_calls=0))

def live(reg):
    p=process_identity(reg['pid']);return p and p['state']!='Z' and p['start_ticks']==reg['start_ticks']

try:
    pred=D/'CP1r3_supplemental_verifier_01/queue_priority_03';reg=read(pred/'registration.json')
    while not (pred/'completion.json').exists():
        assert live(reg),'Supplemental owner missing without terminal receipt'
        write(q/'status.json',dict(status='waiting_for_original_checks_supplement_terminal'));time.sleep(15)
    while live(reg):time.sleep(2)
    assert all(sha(p)==h for p,h in bound.items())
    before=time.monotonic()
    with (q/'audit.log').open('x') as log:
        child=subprocess.Popen([sys.executable,'-B',str(D/'cp1r3_raw_admission_v1.py'),'--execute'],
            stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        write(q/'status.json',dict(status='readonly_raw_admission_under_shared_serial_lock',**process_identity(child.pid)))
        code=child.wait()
    receipt=root/'execution/completion.json';result=read(receipt) if receipt.exists() else {}
    passed=code==0 and result.get('passed',False)
    write(q/'completion.json',dict(passed=passed,status='registered_raw_admission_terminal' if passed else 'reconciliation_required',
        all_roles_admitted=result.get('all_roles_admitted',False),matched_pairs=result.get('matched_pairs',[]),
        complete_audit_command_seconds=time.monotonic()-before,returncode=code,source_sha256=bound,
        new_native_or_STA_calls=0,original_failure_rewritten=False,no_automatic_retry=True,research_complete=False))
    write(q/'status.json',dict(status='terminal' if passed else 'reconciliation_required'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),
        source_sha256=bound,new_native_or_STA_calls=0,no_automatic_retry=True));raise
