"""Observe surviving measured flow; resume gated queue owner only after its termination."""
import os,signal,time,fcntl
from pathlib import Path
from datetime import datetime,timezone
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from measure_process_tree_v1 import sample_tree

root=D/'supervision_recovery_20261115_01';reg=read(root/'intervention.json')
lock=(root/'owner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
measured=reg['original_measured_process'];gated=reg['paused_queue_owner'];known={measured['pid']:measured['start_ticks']}
write(root/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],source_sha256={str(Path(__file__).resolve()):sha(__file__),str(root/'intervention.json'):sha(root/'intervention.json')},native_calls=0))
with (root/'recovery_memory_samples.jsonl').open('x') as stream:
    import json
    while True:
        p=process_identity(measured['pid'])
        if not p or p['state']=='Z' or p['start_ticks']!=measured['start_ticks']:break
        sample=sample_tree(measured['pid'],known);sample['observed_at']=datetime.now(timezone.utc).isoformat()
        stream.write(json.dumps(sample)+'\n');stream.flush()
        write(root/'status.json',dict(status='watching_original_live_full_flow',measured_process=p,successor_owner=process_identity(gated['pid']),qualification='Recovery samples only; original observation gap and overlap remain explicit.'))
        time.sleep(15)
# GNU-time process waits the original full driver and its awaited children.
remaining=[]
for pid,ticks in known.items():
    p=process_identity(pid)
    if p and p['state']!='Z' and p['start_ticks']==ticks:remaining.append(p)
if remaining:
    write(root/'completion.json',dict(passed=False,status='known_original_descendants_still_live',remaining=remaining,successor_resumed=False));raise SystemExit(1)
p=process_identity(gated['pid']);resumed=False
if p and p['state']!='Z' and p['start_ticks']==gated['start_ticks']:
    assert p['state'] in ['T','t'];os.kill(gated['pid'],signal.SIGCONT);resumed=True
flow=D/'complete_BNN_closed_stream_flow_01/bnn_native_closed_stream/flow'
write(root/'completion.json',dict(passed=True,status='original_measured_process_terminal_observed',flow_completion_exists=(flow/'completion.json').exists(),successor_resumed=resumed,original_measurement_reconstructed=False,native_calls=0,observed_at=datetime.now(timezone.utc).isoformat(),qualification='Supervision handoff only, not scientific flow/measurement verification. Original observer has a gap and briefly overlapped another native case; no complete PSS/observer-wall receipt fabricated. Separate read-only recovery and downstream reconciliation required.'))
write(root/'status.json',dict(status='terminal',successor_resumed=resumed))
