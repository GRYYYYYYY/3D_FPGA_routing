"""Package precision-only release after existing timing/fixture queues, serially."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'confirmation_release_cp1r3_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(root/'plan.json'):sha(root/'plan.json'),**plan['source_sha256']}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,new_native_calls=0))
try:
    pred=Path(plan['predecessor']);reg=read(pred/'registration.json')
    while not (pred/'completion.json').exists():
        live=process_identity(reg['pid']);assert live and live['state']!='Z' and live['start_ticks']==reg['start_ticks']
        write(q/'status.json',dict(status='waiting_for_registered_empty_query_fixture_validation'))
        time.sleep(15)
    done=read(pred/'completion.json');assert done['passed'] and done['status']=='registered_empty_query_replay_terminal'
    serial=(D/'critical_scope_runner.lock').open('r');write(q/'status.json',dict(status='waiting_for_shared_serial_slot_packaging'));fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(f)==h for f,h in bound.items())
    env={**os.environ,'H3D_CP1R3_SERIAL_OWNER':str(os.getpid()),'PYTHONDONTWRITEBYTECODE':'1'}
    with (q/'packaging.log').open('x') as log:
        child=subprocess.Popen([sys.executable,str(D/'prepare_confirmation_release_cp1r3.py')],stdout=log,stderr=subprocess.STDOUT,env=env)
        write(q/'status.json',dict(status='packaging_running',**process_identity(child.pid)));code=child.wait()
    assert code==0 and read(root/'completion.json')['passed']
    write(q/'completion.json',dict(passed=True,status='registered_CP1r3_packaging_terminal',new_native_calls=0,report=str(root/'completion.json'),source_sha256=bound))
    write(q/'status.json',dict(status='terminal'))
except Exception as error:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(error),new_native_calls=0,source_sha256=bound));raise
