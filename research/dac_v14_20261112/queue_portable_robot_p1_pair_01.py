"""One fixed robot p1 physical-input pair after all already registered native work."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'portable_robot_p1_pair_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(p):sha(p) for p in [root/'plan.json',Path(__file__).resolve(),D/'run_portable_robot_p1_pair_01.py',D/'compare_portable_robot_p1_pair_01.py']}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,fixed_order=plan['fixed_order']))
try:
    predecessor=Path(plan['predecessor']);identity=read(predecessor/'registration.json')
    while not (predecessor/'completion.json').exists():
        live=process_identity(identity['pid']);assert live and live['state']!='Z' and live['start_ticks']==identity['start_ticks'],'Predecessor disappeared; reconcile actual descendants'
        write(q/'status.json',dict(status='waiting_for_registered_robot_owner_scope_pair',predecessor=str(predecessor)));time.sleep(15)
    prior=read(predecessor/'completion.json');assert prior['status']=='registered_scope_pair_terminal'
    whole=read(Path(plan['whole_method_prerequisite'])/'completion.json');assert whole['status']=='registered_whole_method_execution_terminal'
    assert whole['passed'], 'Portable whole-method prerequisite failed; new roles remain unexecuted'
    if not prior['passed']:
        write(q/'completion.json',dict(passed=False,status='prerequisite_validation_failed_roles_unexecuted',native_calls_new=0,source_sha256=bound));write(q/'status.json',dict(status='prerequisite_failed_unexecuted'));raise SystemExit(0)
    serial=(D/'critical_scope_runner.lock').open('r');write(q/'status.json',dict(status='waiting_for_shared_serial_slot'));fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(f)==h for f,h in bound.items()) and all(sha(f)==h for f,h in plan['source_sha256'].items())
    with (q/'execution.log').open('x') as log:
        child=subprocess.Popen([sys.executable,str(D/'run_portable_robot_p1_pair_01.py')],stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',**process_identity(child.pid)));code=child.wait()
    assert code==0 and (root/'comparison.json').exists()
    write(q/'completion.json',dict(passed=True,status='registered_pair_terminal',source_sha256=bound,comparison=str(root/'comparison.json'),qualification='Both roles reconciled, including failures; not a research stopping condition.'));write(q/'status.json',dict(status='terminal'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),source_sha256=bound));raise
