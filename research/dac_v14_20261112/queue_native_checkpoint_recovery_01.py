"""Serial recovery of original native-only checkpoints after engineering owners."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

proof=D/'native_checkpoint_recovery_preflight_01/completion.json'
assert read(proof)['passed']
assert all(sha(p)==h for p,h in read(proof)['source_sha256'].items())
q=D/'native_checkpoint_recovery_01/queue';q.mkdir(parents=True,exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
prior=D/'native_census_resource_equivalence_recovery_02/queue'
owner=read(prior/'registration.json')
cases={'bnn_R1_native':D/'stable_seed_transfer_dev_01/bnn_R1_native',
       'bnn_Tf_native':D/'stable_seed_transfer_recovery_01/bnn_Tf_native'}
bindings={str(p):sha(p) for p in [Path(__file__).resolve(),D/'run_seed_census_checkpoint_recovery_v1.py',
          D/'resource_checkpoint_recovery_v1.py',proof,prior/'registration.json']}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    prerequisite=str(prior),prerequisite_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),
    cases={k:str(v) for k,v in cases.items()},source_sha256=bindings,
    limits=dict(combined_native_VPR_maximum=3,this_chain_parent_plus_child=2),
    qualification='Fresh LOAD/FULL/STA revalidates original accepted checkpoints and saved pending candidates. Original anchors/seed/rank/rules preserved; completed searches are consumed without rerouting. No fabricated original final pool seal or cold timing. Runtime validation is still pending.'))
write(q/'status.json',dict(status='waiting_for_native_census_equivalence_owner_terminal'))
while True:
    live=process_identity(owner['pid'])
    if not live or live['state']=='Z' or live['start_ticks']!=owner['start_ticks']:break
    time.sleep(15)
if not (prior/'completion.json').exists():
    write(q/'completion.json',dict(passed=False,status='predecessor_disappeared_requires_reconciliation',native_calls=0))
    sys.exit(1)
results={}
for name,old in cases.items():
    assert all(sha(p)==h for p,h in bindings.items())
    reg=read(old/'registration.json')
    cmd=[sys.executable,str(D/'run_seed_census_checkpoint_recovery_v1.py'),
        '--initial-state',reg['initial_state'],'--batch',str(q.parent/name),'--resume-from',str(old),
        '--full-graph-cache',reg['full_graph_cache'],'--bundle-size',str(reg['bundle_size']),
        '--domain-mode',reg['domain_mode'],'--graph-echo',reg['graph_echo'],'--seed-order',reg['seed_order'],
        '--accepted-steps',str(reg['local_probe']['accepted_steps']),
        '--rank-windows',str(reg['local_probe']['ranked_candidates_per_state'])]
    with (q/(name+'.log')).open('w') as log:
        child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',case=name,pid=child.pid,start_ticks=process_identity(child.pid)['start_ticks'],command=cmd))
        code=child.wait()
    receipt=q.parent/name/'completion.json'
    results[name]=dict(passed=code==0 and receipt.exists() and read(receipt)['passed'],returncode=code,completion=str(receipt))
    write(q/'results.json',results)
write(q/'completion.json',dict(passed=all(v['passed'] for v in results.values()),results=results,
    complete_single_configuration_algorithm_seconds=None,source_sha256=bindings))
write(q/'status.json',dict(status='terminal',passed=all(v['passed'] for v in results.values())))
