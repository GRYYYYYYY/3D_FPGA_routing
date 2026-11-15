"""One serial whole-net diagnostic; no mutation of the completed R1 actor."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from seed_census_analysis_pool_v2 import process_identity

root=D/'R1_whole_net_residual_probe_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
files=[Path(__file__).resolve(),root/'plan.json',D/'run_serial_fused_resource_transactions_v2.py',D/'run_serial_fused_seed_analysis_v3.py',D/'materialize_serial_fused_candidate_v3.py',D/'serial_fused_serialization_validation_01/completion.json',Path(plan['diagnosis']),*map(Path,plan['prepared_files'])]
# The old validated callback backend is used; the new source-snapshot binary is NOT executed.
hashes={str(f):sha(f) for f in files};prior=D/'budget47_current_timing_composition_01/queue';p=read(prior/'registration.json')
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=hashes,predecessor=str(prior),predecessor_identity=dict(pid=p['pid'],start_ticks=p['start_ticks']),scope=plan['qualification']))
write(q/'status.json',dict(status='waiting_for_current_serial_owner_to_release_slot',predecessor=str(prior)))
# Wait on the shared exclusive slot now. Existing successor queues retain their
# own registered dependencies/inputs and will block normally on this same slot.
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX)
if not (prior/'completion.json').exists():
 write(q/'completion.json',dict(passed=False,native_calls=0,reason='Serial predecessor ended without a terminal receipt; reconciliation required',source_sha256=hashes));sys.exit(1)
assert all(sha(f)==h for f,h in hashes.items())
tx=root/'transaction';tx.mkdir();(tx/'registration.json').write_bytes((root/'prepared_transaction_registration.json').read_bytes())
with (q/'transaction.log').open('w') as log:
 child=subprocess.Popen([sys.executable,str(D/'run_serial_fused_resource_transactions_v2.py'),'--batch',str(tx)],stdout=log,stderr=subprocess.STDOUT)
 observed=process_identity(child.pid);write(q/'status.json',dict(status='running',phase='whole_net_native_scope_and_order_probe',pid=child.pid,start_ticks=observed['start_ticks']));code=child.wait()
passed=code==0 and (tx/'completion.json').exists() and read(tx/'completion.json')['passed']
write(q/'completion.json',dict(passed=passed,returncode=code,transaction=str(tx),source_sha256=hashes,qualification=plan['qualification']));write(q/'status.json',dict(status='terminal',passed=passed))
print(dict(passed=passed,transaction=str(tx)),flush=True)
