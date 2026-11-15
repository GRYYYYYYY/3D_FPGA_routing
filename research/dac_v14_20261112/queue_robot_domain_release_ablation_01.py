"""One additional release ablation after all already registered engineering predecessors."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'robot_domain_release_ablation_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
files=[Path(__file__).resolve(),root/'plan.json',root/'prepared_transaction_registration.json',*map(Path,plan['prepared_files'])];bound={str(f):sha(f) for f in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=bound,scope=plan['qualification']))
prior=Path(plan['predecessor']);owner=read(prior/'registration.json')
while not (prior/'completion.json').exists():
 p=process_identity(owner['pid']);live=bool(p and p['state']!='Z' and p['start_ticks']==owner['start_ticks']);write(q/'status.json',dict(status='waiting_for_registered_BNN_composition_LOAD_terminal',verified_predecessor_live=live))
 if not live:write(q/'completion.json',dict(passed=False,status='predecessor_disappeared_without_receipt',native_calls=0));sys.exit(1)
 time.sleep(15)
serial=(D/'critical_scope_runner.lock').open('r');write(q/'status.json',dict(status='waiting_for_current_serial_owner_to_release_slot'));fcntl.flock(serial,fcntl.LOCK_EX)
assert all(sha(f)==h for f,h in bound.items());tx=root/'transaction';tx.mkdir();(tx/'registration.json').write_bytes((root/'prepared_transaction_registration.json').read_bytes())
started=time.monotonic()
with (q/'single_no_release_transaction.log').open('w') as log:
 child=subprocess.Popen([sys.executable,str(D/'run_serial_single_resource_scope_v1.py'),'--batch',str(tx)],stdout=log,stderr=subprocess.STDOUT);identity=process_identity(child.pid);write(q/'status.json',dict(status='running',phase='robot_no_release_scope',pid=child.pid,start_ticks=identity['start_ticks']));code=child.wait()
write(q/'execution_receipt.json',dict(returncode=code,complete_imported_component_seconds=time.monotonic()-started))
verified=False
if code==0:
 with (q/'verification.log').open('w') as log:vcode=subprocess.run([sys.executable,str(D/'verify_robot_domain_release_ablation_v1.py')],stdout=log,stderr=subprocess.STDOUT).returncode
 verified=vcode==0 and (root/'verification.json').exists() and read(root/'verification.json')['passed']
write(q/'completion.json',dict(passed=code==0 and verified,command_returncode=code,verification_passed=verified,source_sha256=bound,verification=str(root/'verification.json')));write(q/'status.json',dict(status='terminal',passed=code==0 and verified))
