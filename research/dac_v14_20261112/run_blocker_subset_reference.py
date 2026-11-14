#!/usr/bin/env python3
"""Enumerate occupancy-release subsets for an observed blocked critical witness.

This releases capacity in a reference query only. It neither deletes native nets
nor claims that the released nets can actually be rerouted.
"""
import array
import collections
import itertools
import math
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import signal
import time
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import graph_records,f32
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
assert shutil.disk_usage(D).free>=80*1024**3
q=D/'current_sta_queries_01';r=D/'current_sta_relaxed_01'
fixed,relaxed=read(q/'analysis.json'),read(r/'analysis.json')
assert fixed['passed'] and relaxed['passed']
for doc in [fixed,relaxed]:assert all(sha(p)==h for p,h in doc['source_sha256'].items())
targets=[row for row in relaxed['results'] if row['improvement_ns']>1e-6]
assert len(targets)==1,'This registered pilot examines the one observed positive-gap target.'
target=targets[0];net,pin=target['net'],target['pin']
case=next(c for c in read(q/'cases.json') if (c['net'],c['pin'])==(net,pin))
blockers=sorted({owner for c in target['capacity_conflicts'].values() for owner in c['other_nets']})
assert len(blockers)==3,'Observed three-blocker pilot; larger sets need a bounded subset design.'
owners={int(k):v for k,v in read(q/'occupancy_owners.json').items()}
caps=array.array('I');caps.frombytes((q/'capacities.bin').read_bytes())
source=Path(read(q/'execution_registration.json')['input_run'])
m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
driver=q/'critical_capacity_driver';ex=read(q/'execution.json')
assert sha(driver)==ex['output_sha256']['critical_capacity_driver']
binary=D/'residual_query_offline_01/graph.bin';assert sha(binary)==read(binary.with_name('graph_binding.json'))['binary_graph_sha256']
b=D/'blocker_subset_reference_01';b.mkdir(exist_ok=False)
inputs=[Path(__file__),q/'analysis.json',r/'analysis.json',q/'cases.json',q/'capacities.bin',q/'occupancy_owners.json',source/'manifest.json',source/'routed.route',driver,binary,graph]
bindings={str(p):sha(p) for p in inputs}
write(b/'registration.json',dict(status='registered_before_query',question='Which subset of the three observed blocker nets must be released to permit a shorter fixed-tree path?',
    target=dict(net=net,pin=pin),blocker_nets=blockers,source_sha256=bindings,
    subsets='Enumerate all six nonempty proper subsets; reuse exact empty-set fixed-capacity result and exact unconstrained witness for all-three case after admission check.',
    qualification='Minimum subset only within the three witness blocker nets. Release is an optimistic capacity intervention, not actual rerouting and not a CPD performance claim.',
    pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
    limits=dict(timeout_seconds=1800,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3),native_calls=0))
begun=time.monotonic();rows=[];wanted=set();nreal=len(caps)
for count in [1,2]:
    for released_tuple in itertools.combinations(blockers,count):
        released=set(released_tuple);label='_'.join(map(str,released_tuple));d=b/label;d.mkdir()
        blocked={node for node,ns in owners.items() if len([n for n in ns if n!=net and n not in released])>=caps[node]}
        blocked|={node for node,cap in enumerate(caps) if cap==0}
        assert not blocked.intersection(case['retained'])
        with (d/'cases.txt').open('w') as f:
            f.write('1\n');f.write(' '.join(map(str,[net,pin,case['sink'],len(case['retained']),len(case['anchors']),len(blocked)]))+'\n')
            f.write(' '.join(map(str,case['retained']))+'\n')
            for node,delay in case['anchors'].items():f.write(f'{node} {delay:.17g}\n')
            f.write(' '.join(map(str,sorted(blocked)))+'\n')
        begin=time.monotonic()
        with (d/'stdout.log').open('w') as out,(d/'stderr.log').open('w') as err:
            subprocess.run([str(driver),str(binary),str(d/'cases.txt'),'capacity'],stdout=out,stderr=err,check=True,timeout=120)
        elapsed=time.monotonic()-begin;result=None;edges=[]
        for line in (d/'stdout.log').read_text().splitlines():
            v=line.split();assert tuple(map(int,v[1:4]))==(net,pin,1)
            if v[0]=='RESULT':
                assert result is None
                result=dict(released=sorted(released),stop=int(v[4]),expansions=int(v[5]),labels=int(v[6]),peak_heap=int(v[7]),
                    physical_seconds=float(v[8]),lower_seconds=float(v[9]),core_seconds=float(v[10]),edge_count=int(v[11]),process_seconds=elapsed)
            else:
                assert v[0]=='EDGE' and int(v[4])==len(edges);edges.append((int(v[5]),int(v[6]),float(v[7])))
        assert result is not None and result['stop']==0 and result['physical_seconds']==result['lower_seconds']
        assert len(edges)==result['edge_count'] and edges[0][0]==case['sink'] and edges[-1][1]==nreal
        assert all(a[1]==z[0] for a,z in zip(edges,edges[1:]))
        assert len({u for u,v,w in edges})==len(edges)
        anchor=edges[-1][0];assert str(anchor) in case['anchors'] and edges[-1][2]==case['anchors'][str(anchor)]
        assert not {u for u,v,w in edges[:-1]}.intersection(case['retained'])
        assert not {u for u,v,w in edges}.intersection(blocked)
        assert math.isclose(sum(w for u,v,w in edges),result['physical_seconds'],rel_tol=1e-12,abs_tol=1e-24)
        assert target['physical_seconds']-1e-23<=result['physical_seconds']<=case['current_physical_seconds']+1e-23
        remaining_conflicts={str(node):[n for n in owners.get(node,[]) if n!=net and n not in released]
            for node in set(case['retained'])|{u for u,v,w in edges}
            if len([n for n in owners.get(node,[]) if n!=net and n not in released])+1>caps[node]}
        assert not remaining_conflicts
        original_conflicts={str(node):[n for n in owners.get(node,[]) if n!=net]
            for node in {u for u,v,w in edges} if len([n for n in owners.get(node,[]) if n!=net])+1>caps[node]}
        result.update(improvement_ns=(case['current_physical_seconds']-result['physical_seconds'])*1e9,
            edges=edges,original_capacity_conflicts=original_conflicts,remaining_capacity_conflicts=remaining_conflicts,
            output_sha256={name:sha(d/name) for name in ['cases.txt','stdout.log','stderr.log']})
        rows.append(result);wanted|={(v,u,w) for u,v,w in edges if v!=nreal}
        write(d/'result.json',result)
        print(dict(released=result['released'],gain_ns=result['improvement_ns']),flush=True)
# Independent exact-graph directed-edge validation, one shared scan for six runs.
switches={};found=set()
for section,e in graph_records(graph):
    a=e.attrib
    if section=='switches':
        t=e.find('timing');switches[int(a['id'])]=0. if t is None else f32(t.attrib.get('Tdel',0))
    elif section=='rr_edges':
        edge=(int(a['src_node']),int(a['sink_node']),switches[int(a['switch_id'])])
        if edge in wanted:found.add(edge)
assert found==wanted
# The all-three relaxed witness is admitted, and the fully relaxed optimum is
# a lower bound for this subset, so its equality needs no duplicate query.
assert all(len([n for n in owners.get(node,[]) if n!=net and n not in blockers])+1<=caps[node]
    for node in set(case['retained'])|set(target['suffix_nodes']))
traces=read_trace(source/'routed.route');influence=[]
for node_s,conflict in target['capacity_conflicts'].items():
    node=int(node_s)
    for owner in conflict['other_nets']:
        trace=traces[owner]['trace'];children=collections.defaultdict(set);pins={n.inode:n.pin for n in trace if n.kind=='SINK'}
        for u,v in zip(trace,trace[1:]):
            if u.switch!=-1:children[u.inode].add(v.inode)
        stack=[node];seen=set()
        while stack:
            u=stack.pop();assert u not in seen;seen.add(u);stack.extend(children[u])
        influence.append(dict(net=owner,name=traces[owner]['name'],resource=node,downstream_pins=sorted(pins[n] for n in seen if n in pins),total_pins=len(pins)))
assert all(sha(p)==h for p,h in bindings.items())
write(b/'analysis.json',dict(passed=True,target=dict(net=net,pin=pin),blockers=blockers,rows=rows,
    reused_empty_set=next(x for x in fixed['results'] if (x['net'],x['pin'])==(net,pin)),
    reused_all_set=target,blocked_resource_downstream=influence,directed_edges_checked=len(wanted),
    total_process_seconds=time.monotonic()-begun,native_calls=0,source_sha256=bindings,
    qualification='Exact only for each stated occupancy-release/fixed-tree graph. Minimum release cardinality is restricted to these three blocker nets; released nets are not rerouted. No global optimum or achieved CPD improvement.'))
print('All subset references and physical witnesses verified',flush=True)
