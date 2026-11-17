"""First post-confirmation read-only verification owner; preserve original results."""
import os,fcntl,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'CP1r3_supplemental_verifier_01';q=root/'queue_priority_03';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
plan=read(root/'plan.json');handoff=D/'confirmation_priority_handoff_03/plan.json'
bound={str(root/'plan.json'):sha(root/'plan.json'),**plan['source_sha256'],str(handoff):sha(handoff),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,new_native_or_STA_calls=0))
def live(reg):
    p=process_identity(reg['pid']);return p and p['state']!='Z' and p['start_ticks']==reg['start_ticks']
try:
    pred=D/'cp1r3_distinct_input_cohort_01/queue_priority_02';reg=read(pred/'registration.json')
    while not (pred/'completion.json').exists():
        assert live(reg),'Original confirmation owner requires reconciliation'
        write(q/'status.json',dict(status='waiting_for_original_CP1r3_confirmation_terminal'));time.sleep(15)
    while live(reg):time.sleep(2)
    assert all(sha(p)==h for p,h in bound.items())
    rows=[]
    for target in plan['targets']:
        case=Path(target['case']);original_path=D/'cp1r3_distinct_input_cohort_01'/(target['input']+'_results.json')
        original=read(original_path).get(target['arm'],{}) if original_path.exists() else {}
        row=dict(input=target['input'],arm=target['arm'],original_status=original.get('status'),
            execution_ended=(case/'measurement/completion.json').exists(),original_verification_passed=original.get('status')=='complete_legal_verified',
            supplementary_verification_passed=False,quality=None,legal_no_gain=None,
            timeout='timeout' in original.get('status',''),infrastructure_error=None,
            original_complete_seconds=original.get('complete_seconds'),new_native_or_STA_calls=0)
        if original.get('command_returncode')!=0 or not (case/'flow/completion.json').exists():
            row.update(status='original_execution_not_eligible_for_complete_verifier',infrastructure_error=original.get('status') in ['execution_or_verification_failed','unexecuted_physical_input_admission_failed'])
        else:
            # The child owns the existing shared serial lock nonblockingly.
            # All downstream work depends on this owner; no new routing occurs.
            before=time.monotonic();log=q/(target['input']+'_'+target['arm']+'.log')
            with log.open('x') as stream:
                child=subprocess.Popen([sys.executable,'-B',str(D/'cp1r3_supplemental_verifier_v1.py'),'--execute-case',target['input'],target['arm']],stdout=stream,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
                write(q/'status.json',dict(status='supplementary_original_checks_reverification',input=target['input'],arm=target['arm'],**process_identity(child.pid)))
                code=child.wait()
            receipt=root/'cases'/target['input']/target['arm']/'completion.json'
            checked=read(receipt) if receipt.exists() else {}
            row.update(status='supplementary_checks_passed_additional_admission_pending' if code==0 and checked.get('passed') else 'supplementary_verification_failed',
                supplementary_verification_passed=code==0 and checked.get('passed',False),supplementary_command_seconds=time.monotonic()-before,
                supplementary_receipt=str(receipt) if receipt.exists() else None,returncode=code,
                remaining_admission=['independent complete-request/raw-STA/physical closure','paired actual root/full endpoint matching'],
                original_failure_rewritten=False)
        rows.append(row);write(root/'priority_03_role_status.json',rows)
    write(q/'completion.json',dict(passed=True,status='registered_supplementary_audit_terminal',
        all_supplementary_checks_passed=all(r['supplementary_verification_passed'] for r in rows),
        original_roles=len(rows),source_sha256=bound,new_native_or_STA_calls=0,
        paper_benefit_claims_authorized=False,original_failures_preserved=True,
        qualification='Queue completion records attempted or ineligible audit roles, not all-role scientific success. Original status remains; command end and verification are separate. Additional admission/pair gates remain explicit.'))
    write(q/'status.json',dict(status='terminal'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),source_sha256=bound,new_native_or_STA_calls=0,no_automatic_retry=True));raise
