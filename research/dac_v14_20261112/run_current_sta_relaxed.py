#!/usr/bin/env python3
"""Relax other-net capacity only after exact fixed-capacity queries have no gain."""
import argparse
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import time
from retained_prefix_workflow import D, read, write, sha

parser=argparse.ArgumentParser();parser.add_argument('--queries',type=Path,required=True);parser.add_argument('--batch',type=Path,required=True)
args=parser.parse_args();q=args.queries.resolve();b=args.batch.resolve()
resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
assert shutil.disk_usage(D).free>=80*1024**3
a=read(q/'analysis.json');ex=read(q/'execution.json');reg=read(q/'execution_registration.json')
assert a['passed'] and all(r['mode']==1 and r['improvement_ns']<1e-6 for r in a['results'])
assert all(sha(p)==h for p,h in a['source_sha256'].items())
assert all(sha(p)==h for p,h in ex['source_sha256'].items())
assert all(sha(q/p)==h for p,h in ex['output_sha256'].items())
b.mkdir(exist_ok=False);(b/'src').mkdir()
for name in ['capacities.bin','occupancy_owners.json','cases.json','cases.txt','unit_validation.json','selection.json']:
    shutil.copy2(q/name,b/name)
for name in ['critical_capacity_adapter.h','h3d_candidate_path.h']:
    shutil.copy2(q/'src'/name,b/'src'/name)
driver=D/'critical_capacity_potential_01/src/critical_capacity_driver.cpp'
text=driver.read_text();assert text.count('for(int mode=0;mode<2;++mode)')==1
(b/'src/critical_capacity_driver.cpp').write_text(text.replace('for(int mode=0;mode<2;++mode)','for(int mode=0;mode<1;++mode)'))
binary=D/'residual_query_offline_01/graph.bin'
inputs=[Path(__file__),q/'analysis.json',q/'execution.json',q/'execution_registration.json',driver,binary,
        *sorted((b/'src').glob('*')),*[b/n for n in ['capacities.bin','occupancy_owners.json','cases.json','cases.txt','selection.json']]]
bindings={str(p):sha(p) for p in inputs}
write(b/'execution_registration.json',dict(status='registered_before_compile_and_query',input_run=reg['input_run'],
    question='Do current-path fixed-tree delays have a lower physical reference once other-net capacity is relaxed?',
    evidence='All current worst-path targets have zero exact fixed-capacity improvement. Preserve tree, anchors and endpoints; change only capacity filtering.',
    source_sha256=bindings,query_modes=[0],pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
    limits=reg['limits'],native_route_calls=0,qualification='Optimistic reference, not a legal repair or globally optimal CPD. No repeated fixed-capacity queries.'))
started=time.monotonic()
with (b/'compile.log').open('w') as out:
    subprocess.run(['g++','-std=c++20','-O2','-Wall','-Wextra','-D_GLIBCXX_ASSERTIONS','-fsanitize=undefined','-fno-sanitize-recover=all',
        '-I',str(b/'src'),str(b/'src/critical_capacity_driver.cpp'),'-o',str(b/'critical_capacity_driver')],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=120)
begin=time.monotonic()
with (b/'query_stdout.log').open('w') as out,(b/'query_stderr.log').open('w') as err:
    subprocess.run([str(b/'critical_capacity_driver'),str(binary),str(b/'cases.txt')],stdout=out,stderr=err,check=True,timeout=900)
elapsed=time.monotonic()-begin
assert all(sha(p)==h for p,h in bindings.items())
write(b/'execution.json',dict(status='offline_terminal_pending_physical_audit',source_sha256=bindings,
    output_sha256={name:sha(b/name) for name in ['capacities.bin','occupancy_owners.json','cases.json','cases.txt','unit_validation.json','query_stdout.log','query_stderr.log','critical_capacity_driver']},
    native_route_calls=0,elapsed_seconds=time.monotonic()-started,query_process_seconds=elapsed))
print(dict(status='relaxed_query_terminal',queries=len(a['results']),query_process_seconds=elapsed),flush=True)
