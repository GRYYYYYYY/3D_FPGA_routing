#!/usr/bin/env python3
"""Run the registered offline four-arm study with bounded child resources."""
import json
import mmap
import os
from pathlib import Path
import resource
import shutil
import signal
import struct
import subprocess
import time
from retained_prefix_workflow import D, read, write, sha, require_formal_terminal

require_formal_terminal()
resource.setrlimit(resource.RLIMIT_AS, (24*1024**3, 24*1024**3))
signal.alarm(1800)
b = D / 'tree_aware_candidate_offline_01'
reg = read(b / 'registration.json')
assert not (b / 'execution_registration.json').exists()
assert all(sha(p) == h for p, h in reg['input_sha256'].items())
assert shutil.disk_usage(D).free >= 80*1024**3
graph = D / 'residual_query_offline_01/graph.bin'
assert sha(graph) == read(graph.with_name('graph_binding.json'))['binary_graph_sha256']
for name in ['tree_lower_audit.h', 'test_tree_preferred_query.cpp']:
    shutil.copy2(D / name, b / 'src' / name)
inputs = [Path(__file__), D/'prepare_tree_aware.py', b/'registration.json', graph,
          *sorted((b/'src').glob('*'))]
bindings = {str(p): sha(p) for p in inputs}
write(b/'execution_registration.json', dict(status='registered_before_compile', pid=os.getpid(),
    start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
    source_sha256=bindings, limits=reg['limits'], native_route_calls=0))
started=time.monotonic()
for name in ['test_tree_preferred_query', 'tree_query_driver']:
    with (b/(name+'_compile.log')).open('w') as out:
        subprocess.run(['g++','-std=c++20','-O2','-Wall','-Wextra','-D_GLIBCXX_ASSERTIONS',
            '-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(b/'src'),
            str(b/'src'/(name+'.cpp')),'-o',str(b/name)], stdout=out,stderr=subprocess.STDOUT,
            check=True,timeout=120)
unit=subprocess.run([str(b/'test_tree_preferred_query')],text=True,capture_output=True,timeout=120)
(b/'unit_stdout.log').write_text(unit.stdout)
(b/'unit_stderr.log').write_text(unit.stderr)
write(b/'unit_validation.json',dict(passed=unit.returncode==0,returncode=unit.returncode,
    stdout=unit.stdout,source_sha256=bindings,
    scope='600 random directed two-layer graphs; four models, three expansion caps, two storage caps; independent forward phase Floyd and actual witness checks; modeP exact original-adapter control.'))
assert unit.returncode==0,unit.stderr
print(unit.stdout.strip(),flush=True)
raw=D/'actual_search_tree_eltwise_dev_01/actual_cases.jsonl'
cases=[json.loads(line) for line in raw.open()]
assert len(cases)==3809
prefix_ref={r['search']:r for r in read(raw.with_name('preferred_prefix_analysis.json'))['rows']}
with graph.open('rb') as source, mmap.mmap(source.fileno(),0,access=mmap.ACCESS_READ) as mm, (b/'cases.txt').open('w') as out:
    n=struct.unpack_from('<I',mm,8)[0]
    def node_info(node):
        assert 0<=node<n
        return struct.unpack_from('<iiiii',mm,36+20*node)
    out.write(str(len(cases))+'\n')
    for c in cases:
        r=c['domain'];preferred=set(map(int,r['preferred'].split(',')));inherited={}
        for node,expand,delay,parent,switch,pin in c['tree']:
            assert node not in inherited, 'Observed data has no duplicated SINK node; general duplicates need pin-aware ancestry.'
            inherited[node]=parent>=0 and (inherited[parent] or parent in preferred and node_info(parent)[4]!=node_info(node)[4])
        seed_ids={row[0] for row in c['seeds']}
        assert seed_ids<=inherited.keys()
        def inside(node):
            x,y,dx,dy,l=node_info(node)
            return int(r['xmin'])<=dx<=int(r['xmax']) and int(r['ymin'])<=dy<=int(r['ymax']) and int(r['layer_min'])<=l<=int(r['layer_max'])
        actual={node for node in seed_ids if inherited[node] and node_info(node)[4]==int(r['sink_layer']) and inside(node)}
        assert actual==set(prefix_ref[int(r['search'])]['retained_seed_ids'])
        out.write(' '.join([r['search'],r['sink']]+[r[k] for k in ['xmin','xmax','ymin','ymax','layer_min','layer_max']]+
            list(map(str,[len(c['seeds']),len(preferred),len(inherited),sum(inherited.values())])))+'\n')
        for node,layer,delay in c['seeds']:out.write(f'{node} {delay:.17g}\n')
        for values in [sorted(preferred),sorted(inherited),sorted(node for node,used in inherited.items() if used)]:
            out.write(' '.join(map(str,values))+'\n')
query_start=time.monotonic()
with (b/'query_stdout.log').open('w') as out,(b/'query_stderr.log').open('w') as err:
    subprocess.run([str(b/'tree_query_driver'),str(graph),str(b/'cases.txt'),'256'],
        stdout=out,stderr=err,check=True,timeout=900)
query_wall=time.monotonic()-query_start
assert all(sha(p)==h for p,h in bindings.items())
assert all(sha(p)==h for p,h in reg['input_sha256'].items())

# Exact old focus control, excluding only arm identifier and query elapsed time.
def records(path, mode):
    result={}
    for line in path.open():
        v=line.split()
        if v[0] not in ['RESULT','EDGE'] or int(v[2])!=mode:continue
        search=int(v[1]);v[2]='P'
        if v[0]=='RESULT':v[10]='<elapsed>'
        result.setdefault(search,[]).append(v)
    return result
old=records(D/'preferred_query_certificate_offline_03/query_stdout.log',4)
new=records(b/'query_stdout.log',0)
checks={str(k):v==new.get(k) for k,v in old.items()}
write(b/'control_reproduction.json',dict(passed=all(checks.values()),checks=checks,
    scope='All ten old Pi focus results/paths/stop/work/lower/upper fields reproduced by new P; query timer excluded.'))
write(b/'execution.json',dict(status='offline_terminal_pending_physical_audit',
    source_sha256=bindings,output_sha256={name:sha(b/name) for name in ['cases.txt','unit_validation.json',
        'tree_query_driver','test_tree_preferred_query','query_stdout.log','query_stderr.log','control_reproduction.json']},
    elapsed_seconds=time.monotonic()-started,query_process_with_lower_audit_seconds=query_wall,
    native_route_calls=0,contexts=3809,queries=4*3809))
assert all(checks.values()),checks
print('15236 queries complete, old10 P controls exact; independent physical audit pending',flush=True)
