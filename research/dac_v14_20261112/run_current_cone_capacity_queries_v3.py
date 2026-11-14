#!/usr/bin/env python3
"""Current native-STA selection, exact capacity queries, and bound cache reuse."""
import argparse
import array
import collections
import fcntl
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha
from run_native_frontier_queries import make_case,write_cases,fingerprint,groups
from current_sta_selector import select
from current_query_case_cache import saturated_nodes,make_case_fast
from immutable_rr_audit_cache import GraphAuditCache,KINDS
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);p.add_argument('--batch',type=Path,required=True)
p.add_argument('--reuse-batch',type=Path,action='append',default=[])
p.add_argument('--near-ns',type=float,default=0.);p.add_argument('--query-graph',type=Path,required=True);p.add_argument('--audit-cache',type=Path,required=True);p.add_argument('--cone',type=Path,required=True);a=p.parse_args()
start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
# Read-only offline query owns a unique output directory and frozen graph/state.
# Native transaction lock is unnecessary; this permits independent input screens.
assert read(D/'current_query_case_cache_validation_01/completion.json')['passed']
assert shutil.disk_usage(D).free>=80*1024**3
state=a.state.resolve();assert read(state/'completion.json')['passed']
source=Path(read(state/'completion.json')['run']);b=a.batch.resolve();b.mkdir(exist_ok=False)
trace=source/'native_sta_frontier.jsonl'
manifest=read(source/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
binary=a.query_graph.resolve()/'graph.bin';driver=D/'current_sta_queries_01/critical_capacity_driver'
assert sha(binary)==read(binary.with_name('graph_binding.json'))['binary_graph_sha256']
assert sha(graph)==manifest['shared_inputs'][str(graph)]['sha256']==read(binary.with_name('graph_binding.json'))['source_rrg_sha256']
assert sha(driver)==read(driver.parent/'execution.json')['output_sha256']['critical_capacity_driver']
cone=read(a.cone);assert cone['passed'] and Path(cone['source_state']).resolve()==state
assert all(sha(p)==h for p,h in cone['source_sha256'].items())
import json
pins={(p['net'],p['pin']):p for p in (json.loads(line) for line in trace.open()) if p.get('type')=='pin'}
targets=[]
for row in cone['routed_connections']:
 p=pins[(row['net'],row['pin'])];targets.append(dict(net=p['net'],pin=p['pin'],sink=p['tree_rr'],slack_s=p['setup_slack_s'],raw_criticality=p['setup_criticality_raw'],native_net_delay_s=p['native_net_delay_s']))
selected=dict(targets=targets,input_run=str(source),selector='current exact endpoint max-arrival cone',source_cone=str(a.cone.resolve()),near_ns=cone['near_ns']);write(b/'selection.json',selected)
files=[Path(__file__),D/'current_sta_selector.py',D/'run_native_frontier_queries.py',state/'completion.json',
       source/'manifest.json',source/'independent_audit.json',source/'routed.route',trace,graph,binary,driver,b/'selection.json',a.cone.resolve(),a.audit_cache.resolve()/'completion.json',binary.with_name('graph_binding.json'),D/'immutable_rr_audit_cache.py',D/'current_query_case_cache.py',D/'current_query_case_cache_validation_01/completion.json']
bindings={str(p):sha(p) for p in files}
write(b/'execution_registration.json',dict(status='registered_before_query',input_run=str(source),query_modes=[1],
    source_sha256=bindings,selection='Recomputed from current native STA; no fixed net list.',
    question='Does a current worst/near-worst connection have a capacity-feasible replacement with its other branches retained?',
    limits=dict(timeout_seconds=1800,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3)))
cache=GraphAuditCache(graph,a.audit_cache);caps=array.array('I',map(int,cache.capacities));kinds=[KINDS[int(k)] for k in cache.nodes[:,1]];delays=cache.switches
write(b/'graph_cache_receipt.json',cache.receipt)
with (b/'capacities.bin').open('wb') as f:caps.tofile(f)
traces=read_trace(source/'routed.route');owners=collections.defaultdict(list)
for net,info in traces.items():
    for node in {n.inode for n in info['trace']}:owners[node].append(net)
write(b/'occupancy_owners.json',{str(k):v for k,v in owners.items()})
index_start=time.monotonic();saturated=saturated_nodes(owners,caps);index_seconds=time.monotonic()-index_start
case_start=time.monotonic();cases=[make_case_fast(r,traces,kinds,delays,owners,caps,saturated) for r in selected['targets']]
write(b/'case_preparation_cost.json',dict(shared_saturation_seconds=index_seconds,case_construction_seconds=time.monotonic()-case_start,saturated_nodes=len(saturated)))
write(b/'cases.json',cases);write_cases(b/'cases.txt',cases)
# This cache contains the same frozen capacity driver/core and graph. Validate
# every consumed source/output seal, not just the queried (net,pin) identity.
cache={};validated=set();log_cache={}
cache_directories=list((D/'native_frontier_queries_01').glob('*'))+list(D.glob('current_sta_policy_*/queries_*'))
cache_directories += [p.resolve() for p in a.reuse_batch]
for directory in sorted(set(cache_directories)):
    if not (directory/'analysis.json').exists():continue
    ex=read(directory/'execution.json')
    if ex['source_sha256'].get(str(driver))!=sha(driver) or ex['source_sha256'].get(str(binary))!=sha(binary):continue
    assert read(directory/'analysis.json')['passed']
    for c in read(directory/'cases.json'):cache[fingerprint(c,1)]=(directory,c)
receipts=[];answers={};missing=[]
for c in cases:
    hit=cache.get(fingerprint(c,1));key=(c['net'],c['pin'],1)
    if hit:
        directory,old=hit
        if directory not in validated:
            ex=read(directory/'execution.json');analysis=read(directory/'analysis.json');assert analysis['passed']
            assert all(sha(p)==h for p,h in ex['source_sha256'].items())
            assert all(sha(directory/p)==h for p,h in ex['output_sha256'].items())
            assert all(sha(p)==h for p,h in analysis['source_sha256'].items())
            validated.add(directory);log_cache[directory]=groups(directory/'query_stdout.log')
            bindings.update({str(directory/n):sha(directory/n) for n in ['execution.json','analysis.json','cases.json','query_stdout.log']})
        answers[key]=log_cache[directory][key]
    else:missing.append(c)
    receipts.append(dict(net=c['net'],pin=c['pin'],reused=bool(hit),source=None if not hit else str(hit[0]),query_fingerprint=fingerprint(c,1)))
query_seconds=0.
if missing:
    write_cases(b/'missing.txt',missing);t=time.monotonic()
    with (b/'new.log').open('w') as out,(b/'query_stderr.log').open('w') as err:
        proc=subprocess.run([str(driver),str(binary),str(b/'missing.txt'),'capacity'],stdout=out,stderr=err,timeout=900)
    query_seconds=time.monotonic()-t;write(b/'new_process.json',dict(returncode=proc.returncode,seconds=query_seconds,queries=len(missing)))
    assert proc.returncode==0
    answers.update(groups(b/'new.log'))
else:(b/'query_stderr.log').write_text('')
with (b/'query_stdout.log').open('w') as f:
    for key in sorted(answers):f.writelines(answers[key])
write(b/'reuse_receipts.json',receipts)
write(b/'unit_validation.json',dict(passed=True,reused=True,source_sha256={str(driver.parent/'unit_validation.json'):sha(driver.parent/'unit_validation.json')}))
assert all(sha(p)==h for p,h in bindings.items())
outputs=['case_preparation_cost.json','graph_cache_receipt.json','capacities.bin','occupancy_owners.json','cases.json','cases.txt','query_stdout.log','query_stderr.log','unit_validation.json','reuse_receipts.json']
write(b/'execution.json',dict(status='offline_terminal_pending_physical_audit',source_sha256=bindings,
    output_sha256={n:sha(b/n) for n in outputs},query_process_seconds=query_seconds,new_queries=len(missing),
    reused_queries=len(cases)-len(missing),complete_pre_audit_seconds=time.monotonic()-start))
print(dict(selected=len(cases),new_queries=len(missing),reused_queries=len(cases)-len(missing)),flush=True)
