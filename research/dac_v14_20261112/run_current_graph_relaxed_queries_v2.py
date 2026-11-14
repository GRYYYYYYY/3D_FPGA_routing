#!/usr/bin/env python3
"""Relax background occupancy for exact current-state potential diagnostics."""
import argparse
import resource,signal
from pathlib import Path
import shutil
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha
from run_native_frontier_queries import fingerprint,groups,write_cases
p=argparse.ArgumentParser();p.add_argument('--reuse-batch',type=Path,action='append',default=[]);p.add_argument('--capacity-batch',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);p.add_argument('--query-graph',type=Path,required=True);a=p.parse_args();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
start=time.monotonic();q=a.capacity_batch.resolve();b=a.batch.resolve()
assert read(q/'analysis.json')['passed'];assert all(sha(p)==h for p,h in read(q/'analysis.json')['source_sha256'].items())
b.mkdir(exist_ok=False)
for n in ['cases.txt','cases.json','capacities.bin','occupancy_owners.json','unit_validation.json','selection.json']:shutil.copy2(q/n,b/n)
driver=D/'current_sta_relaxed_01/critical_capacity_driver';binary=a.query_graph.resolve()/'graph.bin'
assert sha(driver)==read(driver.parent/'execution.json')['output_sha256']['critical_capacity_driver']
assert sha(binary)==read(binary.with_name('graph_binding.json'))['binary_graph_sha256']
source=Path(read(q/'execution_registration.json')['input_run']);manifest=read(source/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);assert sha(graph)==manifest['shared_inputs'][str(graph)]['sha256']==read(binary.with_name('graph_binding.json'))['source_rrg_sha256']
files=[Path(__file__),q/'analysis.json',q/'execution_registration.json',q/'cases.json',driver,binary,binary.with_name('graph_binding.json'),graph]
bindings={str(p):sha(p) for p in files}
reg=read(q/'execution_registration.json');reg.update(query_modes=[0],source_sha256=bindings,question='Which current selected targets still have potential after relaxing other-net occupancy? Not a legal candidate.')
write(b/'execution_registration.json',reg)
histories=[D/'current_sta_relaxed_01',D/'current_sta_Tf_relaxed_02',D/'plateau_R1_relaxed_02']
histories+=list(D.glob('current_sta_policy_*/joint_*/relaxed'))+list((D/'plateau_successor_potential_01').glob('*'))
histories += [p.resolve() for p in a.reuse_batch]
cache={};validated=set();logs={};new_cases=read(b/'cases.json');hits=[];missing=[];answers={};receipts=[]
for history in histories:
    if not (history/'analysis.json').exists() or history==b:continue
    ex=read(history/'execution.json')
    binaries={k:v for k,v in {**ex.get('source_sha256',{}),**ex.get('output_sha256',{})}.items() if k.endswith('critical_capacity_driver')}
    if sha(driver) not in binaries.values() or ex.get('source_sha256',{}).get(str(binary))!=sha(binary):continue
    for c in read(history/'cases.json'):cache[fingerprint(c,0)]=history
for c in new_cases:
    history=cache.get(fingerprint(c,0))
    if history is None:missing.append(c);continue
    if history not in validated:
        ex=read(history/'execution.json');an=read(history/'analysis.json');assert an['passed']
        assert all(sha(p)==h for p,h in ex['source_sha256'].items())
        assert all(sha(history/p)==h for p,h in ex['output_sha256'].items())
        assert all(sha(p)==h for p,h in an['source_sha256'].items())
        validated.add(history);logs[history]=groups(history/'query_stdout.log')
        bindings.update({str(history/n):sha(history/n) for n in ['execution.json','analysis.json','cases.json','query_stdout.log']})
    key=(c['net'],c['pin'],0)
    if key not in logs[history]:missing.append(c);continue
    hits.append(c);answers[key]=logs[history][key]
    receipts.append(dict(net=c['net'],pin=c['pin'],source=str(history),query_fingerprint=fingerprint(c,0)))
seconds=0.
if missing:
    write_cases(b/'missing.txt',missing);t=time.monotonic()
    with (b/'new.log').open('w') as out,(b/'query_stderr.log').open('w') as err:
        r=subprocess.run(['prlimit','--as='+str(24*1024**3),'--',str(driver),str(binary),str(b/'missing.txt')],stdout=out,stderr=err,timeout=900)
    seconds=time.monotonic()-t
    write(b/'process.json',dict(returncode=r.returncode,query_process_seconds=seconds));assert r.returncode==0
    answers.update(groups(b/'new.log'))
else:(b/'query_stderr.log').write_text('')
with (b/'query_stdout.log').open('w') as f:
    for key in sorted(answers):f.writelines(answers[key])
write(b/'reuse_receipts.json',receipts)
names=['cases.txt','cases.json','capacities.bin','occupancy_owners.json','unit_validation.json','selection.json','query_stdout.log','query_stderr.log']
write(b/'execution.json',dict(status='offline_terminal_pending_physical_audit',source_sha256=bindings,output_sha256={n:sha(b/n) for n in names},new_queries=len(missing),reused_queries=len(hits),query_process_seconds=seconds,complete_pre_audit_seconds=time.monotonic()-start))
