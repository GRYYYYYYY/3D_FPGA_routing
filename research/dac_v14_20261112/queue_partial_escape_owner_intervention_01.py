"""Single serial owner for fixed BFS LOAD and two matched native controls."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
root=D/'partial_escape_owner_intervention_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
files=[Path(__file__).resolve(),root/'plan.json',root/'prepared_transaction_registration.json',*map(Path,plan['prepared_files'])]
hashes={str(p):sha(p) for p in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256=hashes,scope=plan['qualification']))
prior=Path(plan['predecessor']);previous=read(prior/'registration.json')
while not (prior/'completion.json').exists():
 actual=process_identity(previous['pid']);live=bool(actual and actual['state']!='Z' and actual['start_ticks']==previous['start_ticks'])
 write(q/'status.json',dict(status='waiting_for_original_whole_owner_probe_terminal',verified_predecessor_live=live))
 if not live:
  write(q/'completion.json',dict(passed=False,status='predecessor_ended_without_receipt',results={},native_calls_new=0,source_sha256=hashes));sys.exit(1)
 time.sleep(15)
write(q/'status.json',dict(status='waiting_for_current_serial_owner_to_release_slot'))
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX)
assert all(sha(p)==h for p,h in hashes.items())
began=time.monotonic();results={};costs=[]
def invoke(command,phase):
 started=time.monotonic()
 with (q/(phase+'.log')).open('w') as log:
  child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
  identity=process_identity(child.pid)
  write(q/'status.json',dict(status='running',phase=phase,pid=child.pid,start_ticks=identity['start_ticks']))
  code=child.wait()
 costs.append(dict(phase=phase,returncode=code,complete_process_seconds=time.monotonic()-started))
 write(q/'process_costs.json',costs);return code
proposal=Path(plan['candidate_construction']);proof=read(proposal/'completion.json')
command=[sys.executable,str(D/'run_serial_census_state_analysis_v1.py'),'--source',proof['input_run'],
 '--batch',str(root/'BFS_candidate_evaluation'),'--candidate-route',plan['candidate_route'],
 '--full-graph-cache',str(D/'full_route_graph_cache_bnn_01'),'--fresh-physical-audit']
code=invoke(command,'BFS_candidate_LOAD')
receipt=root/'BFS_candidate_evaluation/completion.json'
results['BFS_candidate_LOAD']=dict(passed=code==0 and receipt.exists() and read(receipt)['passed'],returncode=code,completion=str(receipt))
write(q/'results.json',results)
assert all(sha(p)==h for p,h in hashes.items())
tx=root/'transaction';tx.mkdir();(tx/'registration.json').write_bytes((root/'prepared_transaction_registration.json').read_bytes())
code=invoke([sys.executable,str(D/'run_partial_escape_owner_transactions_v1.py'),'--batch',str(tx)],'native_two_connection_pair')
results['native_two_connection_pair']=dict(passed=code==0 and (tx/'completion.json').exists() and read(tx/'completion.json')['passed'],returncode=code,completion=str(tx/'completion.json'))
write(q/'results.json',results)
write(q/'execution_receipt.json',dict(passed=all(v['passed'] for v in results.values()),results=results,
 complete_shared_imported_execution_seconds=time.monotonic()-began,source_sha256=hashes))
code=invoke([sys.executable,str(D/'verify_partial_escape_owner_intervention_v1.py')],'readonly_verification')
passed=code==0 and (root/'verification.json').exists() and read(root/'verification.json')['passed']
write(q/'completion.json',dict(passed=passed,execution_all_native_gates_passed=all(v['passed'] for v in results.values()),results=results,
 complete_shared_imported_workflow_seconds=time.monotonic()-began,source_sha256=hashes))
write(q/'status.json',dict(status='terminal',passed=passed))
