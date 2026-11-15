"""Run the untouched registered Tf pair; preserve both interrupted native checkpoints."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

q = D/'stable_seed_transfer_recovery_02/queue'
q.mkdir(parents=True, exist_ok=False)
lock = (q/'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
prior = D/'stable_seed_transfer_recovery_01/queue'
original = read(prior/'registration.json')
locks=[]
observations=[]
for name in ['stable_seed_transfer_recovery_01', 'direct_scope_resource_equivalence_recovery_01',
             'native_census_resource_equivalence_recovery_01']:
    old = D/name/'queue'
    reg=read(old/'registration.json'); status=read(old/'status.json')
    for identity in [reg,status]:
        if 'pid' not in identity: continue
        live=process_identity(identity['pid'])
        assert not live or live['state']=='Z' or live['start_ticks']!=identity['start_ticks'], (name,live)
        observations.append(dict(owner=name,pid=identity['pid'],recorded_start_ticks=identity['start_ticks'],actual=live))
    handle=(old/'owner.lock').open('r');fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(handle)
case=original['cases']['bnn_Tf_paired']
assert not (D/'stable_seed_transfer_dev_01/bnn_Tf_paired').exists()
assert not (D/'stable_seed_transfer_recovery_01/bnn_Tf_paired').exists()
assert all(sha(p)==h for p,h in original['source_sha256'].items())
assert all(sha(p)==h for p,h in case['source_sha256'].items())
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    cases=original['cases'],submitted_cases=['bnn_Tf_paired'],original_owner=str(prior),
    reconciled_absent_handles=observations,source_sha256={**original['source_sha256'],str(Path(__file__).resolve()):sha(__file__)},
    outstanding_checkpoints=['stable_seed_transfer_dev_01/bnn_R1_native','stable_seed_transfer_recovery_01/bnn_Tf_native'],
    qualification='Only the never-submitted Tf paired case; no change to registered actor, seeds, ranking, root limits, or acceptance. Completion seals this case only, not the transfer cohort. Native checkpoint recovery remains separate.'))
output=q.parent/'bnn_Tf_paired'
command=[sys.executable,str(D/'run_seed_census_shadow_resource_repair.py'),
    '--initial-state',case['initial_state'],'--batch',str(output),'--full-graph-cache',case['full_graph_cache'],
    '--bundle-size','8','--domain-mode',case['domain_mode'],'--graph-echo','compact',
    '--seed-order','delay_rr_id','--accepted-steps','0','--rank-windows','3']
if case['domain_feedback']:command.append('--domain-feedback')
started=time.monotonic()
with (q/'bnn_Tf_paired.log').open('w') as log:
    process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    write(q/'status.json',dict(status='running',case='bnn_Tf_paired',pid=process.pid,
        start_ticks=process_identity(process.pid)['start_ticks'],command=command))
    code=process.wait()
receipt=output/'completion.json'
passed=code==0 and receipt.exists() and read(receipt)['passed']
write(q/'completion.json',dict(passed=passed,returncode=code,case='bnn_Tf_paired',completion=str(receipt),
    complete_case_seconds=time.monotonic()-started,full_transfer_cohort_complete=False,
    complete_single_configuration_algorithm_seconds=None))
write(q/'status.json',dict(status='terminal',passed=passed))
