"""Single appended owner; preserve running and completed predecessor batches."""
import fcntl,os,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from cp1_confirmation_cohort_v1 import ROOT,execute
plan=read(ROOT/'plan.json');q=ROOT/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(f):sha(f) for f in [ROOT/'plan.json',Path(__file__).resolve(),D/'cp1_confirmation_cohort_v1.py']}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,fixed_order=plan['fixed_arm_order']))
try:
    predecessor=Path(plan['predecessor']);identity=read(predecessor/'registration.json')
    while not (predecessor/'completion.json').exists():
        live=process_identity(identity['pid']);assert live and live['state']!='Z' and live['start_ticks']==identity['start_ticks'],'Predecessor missing; inspect actual descendants before proceeding'
        write(q/'status.json',dict(status='waiting_for_corrected_robot_p1',predecessor=str(predecessor)));time.sleep(15)
    terminal=read(predecessor/'completion.json');assert terminal['passed'] and terminal['status']=='registered_pair_terminal','Predecessor supervision unresolved; ordinary accounted scientific failures are allowed'
    serial=(D/'critical_scope_runner.lock').open('r');write(q/'status.json',dict(status='waiting_for_shared_serial_slot'));fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(f)==h for f,h in bound.items()) and all(sha(f)==h for f,h in plan['source_sha256'].items())
    execute(plan)
    write(q/'completion.json',dict(passed=True,status='registered_cohort_terminal',source_sha256=bound,comparison=str(ROOT/'comparison.json'),research_complete=False));write(q/'status.json',dict(status='terminal'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),source_sha256=bound));raise
