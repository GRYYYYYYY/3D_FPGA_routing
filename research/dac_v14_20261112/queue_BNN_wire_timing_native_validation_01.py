"""Single serial owner for the fixed composed candidate LOAD and read-only gates."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

root=D/'BNN_wire_timing_native_validation_01';plan=read(root/'plan.json');q=root/'queue';q.mkdir(exist_ok=False)
lock=(q/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
files=[Path(__file__).resolve(),root/'plan.json',root/'preflight.json',*map(Path,plan['prepared_files'])]
hashes={str(f):sha(f) for f in files}
write(q/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=hashes,scope=plan['qualification']))
previous=Path(plan['predecessor']);registered=read(previous/'registration.json')
while not (previous/'completion.json').exists():
    p=process_identity(registered['pid']);live=bool(p and p['state']!='Z' and p['start_ticks']==registered['start_ticks'])
    write(q/'status.json',dict(status='waiting_for_registered_closed_stream_flow_terminal',
                             verified_predecessor_live=live,predecessor=str(previous)))
    if not live:
        write(q/'completion.json',dict(passed=False,status='predecessor_ended_without_receipt',native_calls_new=0));sys.exit(1)
    time.sleep(15)
write(q/'status.json',dict(status='waiting_for_current_serial_owner_to_release_slot'))
serial=(D/'critical_scope_runner.lock').open('r');fcntl.flock(serial,fcntl.LOCK_EX)
assert all(sha(f)==h for f,h in hashes.items())
command=[sys.executable,str(D/'measure_process_tree_v1.py'),'--output',str(root/'measurement'),'--',
    sys.executable,str(D/'run_independent_timing_cone_analysis_stream_v1.py'),'--source',plan['source_run'],
    '--batch',str(root/'candidate_evaluation'),'--candidate-route',plan['candidate_route'],
    '--full-graph-cache',plan['full_graph_cache'],'--timing-echo']
with (q/'candidate_LOAD.log').open('w') as log:
    child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);identity=process_identity(child.pid)
    write(q/'status.json',dict(status='running',phase='fixed_composed_candidate_LOAD',pid=child.pid,start_ticks=identity['start_ticks']))
    code=child.wait()
receipt=root/'candidate_evaluation/completion.json'
ok=code==0 and receipt.exists() and read(receipt)['passed']
write(q/'execution_receipt.json',dict(command_passed=ok,returncode=code,command=command,
    completion=str(receipt),source_sha256=hashes))
with (q/'verification.log').open('w') as log:
    verify=subprocess.run([sys.executable,str(D/'verify_BNN_wire_timing_native_validation_v1.py')],stdout=log,stderr=subprocess.STDOUT).returncode
passed=verify==0 and (root/'verification.json').exists() and read(root/'verification.json')['passed']
write(q/'completion.json',dict(passed=passed,actual_native_gates_passed=ok,registered_roles=1,
    source_sha256=hashes,verification=str(root/'verification.json'),native_search_calls=0))
write(q/'status.json',dict(status='terminal',passed=passed,actual_native_gates_passed=ok))
