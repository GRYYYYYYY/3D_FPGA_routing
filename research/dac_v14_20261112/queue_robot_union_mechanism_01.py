"""Single serial owner; run registered scope pair once after existing work."""
import fcntl,os,subprocess,sys,time,traceback
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'robot_union_mechanism_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bound={str(p):sha(p) for p in [Path(__file__).resolve(),root/'plan.json',D/'verify_robot_union_mechanism_01.py']}
write(q/'registration.json',dict(**process_identity(os.getpid()),source_sha256=bound,fixed_order=plan['fixed_order']))
try:
    prior=Path(plan['predecessor']);identity=read(prior/'registration.json')
    while not (prior/'completion.json').exists():
        actual=process_identity(identity['pid']);assert actual and actual['state']!='Z' and actual['start_ticks']==identity['start_ticks'],'Predecessor missing; reconcile descendants before new work'
        write(q/'status.json',dict(status='waiting_for_CP1_cross_circuit_cohort',predecessor=str(prior)));time.sleep(15)
    closed=read(prior/'completion.json')
    if closed['status']!='registered_cohort_terminal' or not closed['passed']:
        write(q/'completion.json',dict(passed=False,status='predecessor_requires_reconciliation_roles_unexecuted',native_calls_new=0,source_sha256=bound));write(q/'status.json',dict(status='unexecuted_predecessor_reconciliation'));raise SystemExit(0)
    serial=(D/'critical_scope_runner.lock').open('r');write(q/'status.json',dict(status='waiting_for_shared_serial_slot'));fcntl.flock(serial,fcntl.LOCK_EX)
    assert all(sha(f)==h for f,h in bound.items()) and all(sha(f)==h for f,h in plan['source_sha256'].items())
    tx=root/'transaction';tx.mkdir(exist_ok=False);(tx/'registration.json').write_bytes((root/'prepared_transaction_registration.json').read_bytes())
    cmd=[sys.executable,str(D/'measure_process_tree_v1.py'),'--output',str(root/'measurement'),'--',sys.executable,plan['supervisor'],'--receipt',str(root/'supervision.json'),'--',sys.executable,plan['backend'],'--batch',str(tx)]
    env={k:v for k,v in os.environ.items() if not k.startswith('VPR_')};env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    with (q/'execution.log').open('x') as log:
        child=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',**process_identity(child.pid),command=cmd));code=child.wait()
    measurement=read(root/'measurement/completion.json');supervision=read(root/'supervision.json')
    assert not measurement['live_descendants_after_command_exit'] and not supervision['residual_descendants']
    write(q/'execution_receipt.json',dict(returncode=code,source_sha256=bound,measurement=str(root/'measurement/completion.json'),supervision=str(root/'supervision.json')))
    with (q/'verification.log').open('x') as log:
        check=subprocess.run([sys.executable,str(D/'verify_robot_union_mechanism_01.py')],stdout=log,stderr=subprocess.STDOUT)
    assert check.returncode==0 and read(root/'verification.json')['passed']
    write(q/'completion.json',dict(passed=True,status='registered_union_mechanism_terminal',execution_returncode=code,verification=str(root/'verification.json'),source_sha256=bound,qualification='Accounting/evidence terminal; native failure or no gain is retained, not a research stop.'))
    write(q/'status.json',dict(status='terminal'))
except Exception as exc:
    write(q/'completion.json',dict(passed=False,status='reconciliation_required',error=repr(exc),source_sha256=bound));traceback.print_exc();raise
