"""Resume only failed R1; consume successful Tf02 verbatim, never rerun it."""
import fcntl,os,subprocess,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

proof=D/'native_checkpoint_adapter_v4_replay_01/completion.json';v=read(proof);assert v['passed'] and v['native_calls_new']==0
assert all(sha(p)==h for p,h in v['source_sha256'].items())
prior=D/'native_checkpoint_recovery_02/queue';p=read(prior/'completion.json');assert not p['passed']
assert not p['results']['bnn_R1_native']['passed'] and p['results']['bnn_Tf_native']['passed']
for file in [prior/'registration.json',prior/'status.json']:
 r=read(file)
 if 'pid' in r:
  live=process_identity(r['pid']);assert not live or live['state']=='Z' or live['start_ticks']!=r['start_ticks']
tf=D/'native_checkpoint_recovery_02/bnn_Tf_native/completion.json';tfclosed=read(tf)
assert tfclosed['passed'] and all(sha(f)==h for f,h in tfclosed['source_sha256'].items())
assert read(D/'native_checkpoint_recovery_02/bnn_R1_native/pool/completion.json')['jobs']==0
old=D/'stable_seed_transfer_dev_01/bnn_R1_native';reg=read(old/'registration.json')
q=D/'native_checkpoint_recovery_03/queue';q.mkdir(parents=True,exist_ok=False)
ownerlock=(q/'owner.lock').open('w');fcntl.flock(ownerlock,fcntl.LOCK_EX|fcntl.LOCK_NB)
files=[Path(__file__).resolve(),D/'run_seed_census_checkpoint_recovery_v4.py',D/'resource_checkpoint_recovery_v4.py',D/'completed_native_worker_replay_v2.py',D/'sealed_native_pool_replay.py',D/'pool_state_evaluator_v7.py',proof,prior/'completion.json',tf,old/'registration.json']
bindings={str(f):sha(f) for f in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],original_checkpoint=str(old),reused_Tf_completion=str(tf),reused_Tf_completion_sha256=sha(tf),cases={'bnn_R1_native':str(old)},source_sha256=bindings,qualification='Only R1 is executed. Original root cap/seed/order/rank/menu unchanged. Exact historical completed workers are consumed without repeated search or LOAD; absent later LOAD receives a real independent full physical audit and new observation context seal. Runtime identity remains original worker identity, separately from new search pool identity. Tf02 is already terminal and reused verbatim. New segment time cannot reconstruct historical whole time. Shared serial slot and existing native guards remain.'))
write(q/'status.json',dict(status='waiting_for_current_serial_owner_to_release_slot'))
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX)
assert all(sha(f)==h for f,h in bindings.items())
cmd=[sys.executable,str(D/'run_seed_census_checkpoint_recovery_v4.py'),'--initial-state',reg['initial_state'],'--batch',str(q.parent/'bnn_R1_native'),'--resume-from',str(old),'--full-graph-cache',reg['full_graph_cache'],'--bundle-size',str(reg['bundle_size']),'--domain-mode',reg['domain_mode'],'--graph-echo',reg['graph_echo'],'--seed-order',reg['seed_order'],'--accepted-steps',str(reg['local_probe']['accepted_steps']),'--rank-windows',str(reg['local_probe']['ranked_candidates_per_state'])]
with (q/'bnn_R1_native.log').open('w') as log:
 child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
 write(q/'status.json',dict(status='running',case='bnn_R1_native',pid=child.pid,start_ticks=process_identity(child.pid)['start_ticks'],command=cmd))
 code=child.wait()
receipt=q.parent/'bnn_R1_native/completion.json'
results={'bnn_R1_native':dict(passed=code==0 and receipt.exists() and read(receipt)['passed'],returncode=code,completion=str(receipt)),'bnn_Tf_native':dict(passed=True,reused_successful_terminal=True,new_native_calls=0,completion=str(tf),completion_sha256=sha(tf))}
assert all(sha(f)==h for f,h in bindings.items())
write(q/'results.json',results);passed=all(r['passed'] for r in results.values())
write(q/'completion.json',dict(passed=passed,results=results,complete_single_configuration_algorithm_seconds=None,source_sha256=bindings,qualification='Actual R1 continuation plus previously sealed successful Tf02, without a duplicated Tf run or historical whole-time reconstruction.'))
write(q/'status.json',dict(status='terminal',passed=passed))
