"""Execute the same unexecuted circuit cohort with a separately frozen proc fix."""
import fcntl
import os
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity
from cp1r2_confirmation_cohort_v1 import ROOT, execute

plan=read(ROOT/'plan.json'); q=ROOT/'queue'; q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(p):sha(p) for p in [ROOT/'plan.json',Path(__file__).resolve(),D/'cp1r2_confirmation_cohort_v1.py']}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,fixed_order=plan['fixed_arm_order']))
try:
    assert read(D/'execution_reconciliation_20261116_01/completion.json')['passed']
    prior=D/'cp1r1_cross_circuit_cohort_01/queue'
    ident=read(prior/'registration.json')
    while not (prior/'completion.json').exists():
        actual=process_identity(ident['pid'])
        assert actual and actual['state']!='Z' and actual['start_ticks']==ident['start_ticks']
        write(q/'status.json',dict(status='waiting_for_CP1r1_packaging_attempts'))
        time.sleep(5)
    assert read(prior/'completion.json')['status']=='registered_cohort_terminal'

    serial=(D/'critical_scope_runner.lock').open('r')
    write(q/'status.json',dict(status='waiting_for_shared_serial_slot'))
    fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(p)==h for p,h in bound.items()) and all(sha(p)==h for p,h in plan['source_sha256'].items())
    execute(plan)
    write(q/'completion.json',dict(passed=True,status='registered_cohort_terminal',source_sha256=bound,comparison=str(ROOT/'comparison.json'),research_complete=False))
    write(q/'status.json',dict(status='terminal'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),source_sha256=bound))
    raise
