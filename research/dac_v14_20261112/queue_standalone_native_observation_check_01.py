"""One serial interface validation after the existing recovery and integration chain."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'standalone_native_observation_equivalence_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(f):sha(f) for f in [Path(__file__).resolve(),root/'plan.json',D/'run_standalone_native_observation_check_01.py']}
identity=process_identity(os.getpid());write(q/'registration.json',dict(pid=os.getpid(),start_ticks=identity['start_ticks'],source_sha256=bound,native_calls_planned=1,route_search_calls=0))
try:
    predecessor=D/'unified_input_integration_01/queue'
    while not (predecessor/'completion.json').exists():
        write(q/'status.json',dict(status='waiting_for_registered_unified_input_chain',predecessor=str(predecessor)));time.sleep(15)
    assert read(predecessor/'completion.json')['status']=='all_registered_roles_terminal'
    serial=(D/'critical_scope_runner.lock').open('r');write(q/'status.json',dict(status='waiting_for_shared_serial_slot'));fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(f)==h for f,h in bound.items()) and all(sha(f)==h for f,h in plan['input_sha256'].items())
    assert not (root/'completion.json').exists() and not (Path(plan['workspace'])/'execution').exists()
    with (q/'execution.log').open('x') as log:
        child=subprocess.Popen([sys.executable,str(D/'run_standalone_native_observation_check_01.py')],stdout=log,stderr=subprocess.STDOUT)
        identity=process_identity(child.pid);write(q/'status.json',dict(status='running',pid=child.pid,start_ticks=identity['start_ticks']));code=child.wait()
    passed=code==0 and (root/'completion.json').exists() and read(root/'completion.json')['passed']
    write(q/'completion.json',dict(passed=passed,returncode=code,status='registered_interface_validation_terminal',source_sha256=bound));write(q/'status.json',dict(status='terminal',passed=passed))
except Exception as exc:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(exc),source_sha256=bound));raise
