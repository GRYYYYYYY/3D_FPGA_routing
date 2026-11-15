"""Append the whole-method execution check; preserve all prior registered owners."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'standalone_whole_method_check_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(f):sha(f) for f in [Path(__file__).resolve(),root/'plan.json',D/'run_standalone_whole_method_check_01.py']}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,full_method_frozen=False))
try:
    predecessor=Path(plan['predecessor']);identity=read(predecessor/'registration.json')
    while not (predecessor/'completion.json').exists():
        actual=process_identity(identity['pid']);assert actual and actual['state']!='Z' and actual['start_ticks']==identity['start_ticks'],'Predecessor disappeared; reconcile real descendants before recovery'
        write(q/'status.json',dict(status='waiting_for_registered_transaction_interface_check',predecessor=str(predecessor)));time.sleep(15)
    assert read(predecessor/'completion.json')['status']=='registered_transaction_validation_terminal'
    serial=(D/'critical_scope_runner.lock').open('r');write(q/'status.json',dict(status='waiting_for_shared_serial_slot'));fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(f)==h for f,h in bound.items()) and all(sha(f)==h for f,h in plan['input_sha256'].items())
    assert not (root/'completion.json').exists() and not (Path(plan['workspace'])/'execution').exists()
    with (q/'execution.log').open('x') as log:
        child=subprocess.Popen([sys.executable,str(D/'run_standalone_whole_method_check_01.py')],stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',**process_identity(child.pid)));code=child.wait()
    passed=code==0 and (root/'completion.json').exists() and read(root/'completion.json')['passed']
    write(q/'completion.json',dict(passed=passed,returncode=code,status='registered_whole_method_execution_terminal',source_sha256=bound));write(q/'status.json',dict(status='terminal',passed=passed))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),source_sha256=bound));raise
