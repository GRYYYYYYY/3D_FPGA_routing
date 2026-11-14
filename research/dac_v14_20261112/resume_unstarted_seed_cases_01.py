"""Run only previously unsubmitted registered cases; retain the interrupted case."""
import fcntl
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

old=D/'stable_seed_transfer_dev_01/queue';original=read(old/'registration.json')
assert process_identity(original['pid']) is None
previous_phase=read(old/'status.json');assert process_identity(previous_phase['pid']) is None
old_lock=(old/'owner.lock').open('r');fcntl.flock(old_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert all(sha(p)==h for p,h in original['source_sha256'].items())
q=D/'stable_seed_transfer_recovery_01/queue';q.mkdir(parents=True,exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
cases=original['cases'];results={};pending=[]
for name,case in cases.items():
    previous=old.parent/name
    if (previous/'completion.json').exists():
        c=read(previous/'completion.json');assert c['passed']
        assert all(sha(p)==h for p,h in c['source_sha256'].items())
        results[name]=dict(passed=True,status='completed_case_reused_without_execution',completion=str(previous/'completion.json'),
            historical_creation_seconds_not_borrowed=True)
    elif previous.exists():
        assert name=='bnn_R1_native'
        results[name]=dict(passed=False,status='interrupted_private_checkpoint_pending_dedicated_recovery',
            checkpoint=str(previous/'current_state.json'),saved_accepts=read(previous/'current_state.json')['accepted_steps'],
            reason='Original pool final seal missing. Keep accepted and unfinished worker evidence; no fabricated seal or root restart.',
            numerical_failure=False)
    else:pending.append(name)
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    hostname=socket.gethostname(),cases=cases,pending_unsubmitted_cases=pending,original_owner=str(old),
    source_sha256={**original['source_sha256'],str(Path(__file__).resolve()):sha(__file__),str(old/'registration.json'):sha(old/'registration.json')},
    native_parent_plus_child=2,combined_VPR_maximum=3,
    qualification='Only untouched registered cases run with the original actor, input, parameters and acceptance. Four sealed cases reused; one interrupted private checkpoint is not discarded or called a numerical failure. Recovery cost is not cold algorithm time.'))
write(q/'results.json',results);started=time.monotonic()
for name in pending:
    case=cases[name]
    assert all(sha(p)==h for p,h in original['source_sha256'].items())
    assert all(sha(p)==h for p,h in case['source_sha256'].items())
    output=q.parent/name
    command=[sys.executable,str(D/'run_seed_census_shadow_resource_repair.py'),
        '--initial-state',case['initial_state'],'--batch',str(output),'--full-graph-cache',case['full_graph_cache'],
        '--bundle-size','8','--domain-mode',case['domain_mode'],'--graph-echo','compact',
        '--seed-order','delay_rr_id','--accepted-steps','0','--rank-windows','3']
    if case['domain_feedback']:command.append('--domain-feedback')
    t=time.monotonic()
    with (q/(name+'.log')).open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        write(q/'status.json',dict(status='running',case=name,pid=process.pid,
            start_ticks=process_identity(process.pid)['start_ticks'],command=command))
        code=process.wait()
    receipt=output/'completion.json'
    results[name]=dict(passed=code==0 and receipt.exists() and read(receipt)['passed'],
        returncode=code,completion=str(receipt),complete_current_actor_seconds=time.monotonic()-t)
    write(q/'results.json',results)
write(q/'completion.json',dict(passed=all(r['passed'] for r in results.values()),results=results,
    terminal=True,complete_recovery_queue_seconds=time.monotonic()-started,
    complete_single_configuration_algorithm_seconds=None,
    outstanding_interrupted_case='bnn_R1_native',
    qualification='Queue terminal is not research terminal. The interrupted private checkpoint requires explicit source/context revalidation and completion; never silently restart its pristine route or invent the missing final pool seal.'))
write(q/'status.json',dict(status='terminal',all_cases_passed=all(r['passed'] for r in results.values())))
