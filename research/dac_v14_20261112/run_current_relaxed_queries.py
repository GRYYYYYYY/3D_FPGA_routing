#!/usr/bin/env python3
"""Relax background occupancy for exact current-state potential diagnostics."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha
from run_native_frontier_queries import fingerprint,groups,write_cases
p=argparse.ArgumentParser();p.add_argument('--capacity-batch',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);a=p.parse_args()
start=time.monotonic();q=a.capacity_batch.resolve();b=a.batch.resolve()
assert read(q/'analysis.json')['passed'];assert all(sha(p)==h for p,h in read(q/'analysis.json')['source_sha256'].items())
b.mkdir(exist_ok=False)
for n in ['cases.txt','cases.json','capacities.bin','occupancy_owners.json','unit_validation.json','selection.json']:shutil.copy2(q/n,b/n)
driver=D/'current_sta_relaxed_01/critical_capacity_driver';binary=D/'residual_query_offline_01/graph.bin'
assert sha(driver)==read(driver.parent/'execution.json')['output_sha256']['critical_capacity_driver']
assert sha(binary)==read(binary.with_name('graph_binding.json'))['binary_graph_sha256']
files=[Path(__file__),q/'analysis.json',q/'execution_registration.json',q/'cases.json',driver,binary]
bindings={str(p):sha(p) for p in files}
reg=read(q/'execution_registration.json');reg.update(query_modes=[0],source_sha256=bindings,question='Which current selected targets still have potential after relaxing other-net occupancy? Not a legal candidate.')
write(b/'execution_registration.json',reg)
history=D/'current_sta_relaxed_01'
old_cases={fingerprint(c,0):c for c in read(history/'cases.json')}
new_cases=read(b/'cases.json');hits=[c for c in new_cases if fingerprint(c,0) in old_cases]
missing=[c for c in new_cases if fingerprint(c,0) not in old_cases]
answers={}
if hits:
    ex=read(history/'execution.json');an=read(history/'analysis.json');assert an['passed']
    assert ex['output_sha256']['critical_capacity_driver']==sha(driver)
    assert ex['source_sha256'][str(binary)]==sha(binary)
    assert all(sha(p)==h for p,h in ex['source_sha256'].items())
    assert all(sha(history/p)==h for p,h in ex['output_sha256'].items())
    assert all(sha(p)==h for p,h in an['source_sha256'].items())
    logs=groups(history/'query_stdout.log')
    for c in hits:answers[c['net'],c['pin'],0]=logs[c['net'],c['pin'],0]
    bindings.update({str(history/n):sha(history/n) for n in ['execution.json','analysis.json','cases.json','query_stdout.log']})
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
write(b/'reuse_receipts.json',[dict(net=c['net'],pin=c['pin'],source=str(history),query_fingerprint=fingerprint(c,0)) for c in hits])
names=['cases.txt','cases.json','capacities.bin','occupancy_owners.json','unit_validation.json','selection.json','query_stdout.log','query_stderr.log']
write(b/'execution.json',dict(status='offline_terminal_pending_physical_audit',source_sha256=bindings,output_sha256={n:sha(b/n) for n in names},new_queries=len(missing),reused_queries=len(hits),query_process_seconds=seconds,complete_pre_audit_seconds=time.monotonic()-start))
