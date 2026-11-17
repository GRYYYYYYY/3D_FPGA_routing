"""Execute exactly the registered no-release role under the existing serial lock."""
from pathlib import Path
import fcntl,json,os,sys,time,hashlib,subprocess,datetime
from measure_process_tree_v1 import measure
D=Path(__file__).resolve().parent;B=D/'LSTM_release_ablation_01';Q=B/'queue'
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(8*1024*1024),b''):h.update(x)
 return h.hexdigest()
assert not Q.exists();Q.mkdir()
plan=read(B/'plan.json');identity=dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19])
write(Q/'registration.json',dict(**identity,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),B/'plan.json',B/'prepared_transaction_registration.json',B/'run_single_registered_scope.py',B/'verify_no_release.py']},scope=plan['scope']))
write(Q/'status.json',dict(status='waiting_for_serial_slot',**identity))
lock=(D/'critical_scope_runner.lock').open('r');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
start=time.monotonic();assert all(sha(p)==h for p,h in plan['source_sha256'].items())
reg=read(B/'prepared_transaction_registration.json');assert all(sha(p)==h for p,h in reg['source_sha256'].items());assert all(sha(p)==h for p,h in reg['roles']['reuse_on']['source_sha256'].items())
write(B/'source_preflight.json',dict(passed=True,complete_readonly_seconds=time.monotonic()-start,registered_source_bytes_unchanged=True,native_calls_new=0))
tx=B/'transaction';tx.mkdir();(tx/'registration.json').write_bytes((B/'prepared_transaction_registration.json').read_bytes())
write(Q/'status.json',dict(status='running',phase='one_no_release_transaction',**identity))
cmd=[sys.executable,str(B/'run_single_registered_scope.py'),'--batch',str(tx)]
m=measure(cmd,B/'measurement');write(Q/'execution_receipt.json',dict(returncode=m['returncode'],complete_imported_component_seconds=m['complete_command_wall_seconds']))
verified=False
if m['passed']:
 write(Q/'status.json',dict(status='running',phase='existing_same_source_release_ablation_checks',**identity))
 vm=measure([sys.executable,str(B/'verify_no_release.py'),'--execution-receipt',str(Q/'execution_receipt.json')],B/'verification_measurement')
 verified=vm['passed'] and (B/'verification.json').exists() and read(B/'verification.json')['passed']
write(Q/'completion.json',dict(passed=m['passed'] and verified,execution_ended=True,verification_passed=verified,complete_imported_component_seconds=m['complete_command_wall_seconds'],verification_seconds=vm['complete_command_wall_seconds'] if m['passed'] else None,new_registered_native_workers=1,qualification='Only this component cost; no clean complete-flow overhead inferred. Frozen original trajectory never mutated.'))
write(Q/'status.json',dict(status='terminal',passed=verified,**identity));print(read(Q/'completion.json'),flush=True)
