"""Wait for original registered chain, activate fixed configs, execute six roles once."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from cp1r3_confirmation_cohort_v1 import ROOT,execute
from seal_cp1r3_distinct_cohort_outcomes_01 import seal

protocol=read(ROOT/'protocol.json');q=ROOT/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(ROOT/'protocol.json'):sha(ROOT/'protocol.json'),**protocol['source_sha256']}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,registered_inputs=3,registered_roles=6,
    actual_release_and_configs_not_yet_activated=True,configuration_freeze_required_before_any_native=True))
try:
    pred=Path(protocol['predecessor']);reg=read(pred/'registration.json')
    while not (pred/'completion.json').exists():
        live=process_identity(reg['pid']);assert live and live['state']!='Z' and live['start_ticks']==reg['start_ticks']
        write(q/'status.json',dict(status='waiting_for_registered_robot_prefix_recovery'));time.sleep(15)
    previous=read(pred/'completion.json');assert previous['passed'] and previous['status']=='registered_development_recovery_terminal'
    serial=(D/'critical_scope_runner.lock').open('r');write(q/'status.json',dict(status='waiting_for_shared_serial_slot_confirmation'));fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(f)==h for f,h in bound.items())
    env={**os.environ,'H3D_CP1R3_COHORT_SERIAL_OWNER':str(os.getpid()),'PYTHONDONTWRITEBYTECODE':'1'}
    before=time.monotonic()
    with (q/'activation.log').open('x') as log:
        child=subprocess.Popen([sys.executable,str(D/'activate_cp1r3_distinct_input_cohort_01.py')],stdout=log,stderr=subprocess.STDOUT,env=env)
        write(q/'status.json',dict(status='activating_frozen_configs_and_public_reconstruction',**process_identity(child.pid)));code=child.wait()
    write(ROOT/'activation_cost.json',dict(complete_seconds=time.monotonic()-before,returncode=code,native_calls_new=0,scope='Protocol preparation/public reconstruction/admission, not algorithm wall time'))
    assert code==0 and read(ROOT/'preflight.json')['passed']
    plan=read(ROOT/'plan.json');assert all(sha(f)==h for f,h in plan['source_sha256'].items())
    execute(plan);receipt=seal()
    write(q/'completion.json',dict(passed=True,status='registered_cohort_terminal',comparison=str(ROOT/'comparison.json'),terminal_evidence=str(receipt),source_sha256=bound,research_complete=False));write(q/'status.json',dict(status='terminal'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),source_sha256=bound,no_automatic_retry=True));raise
