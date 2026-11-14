#!/usr/bin/env python3
"""Endpoint-only shared-resource reference with all route ownership released.

This proves only a conditional local delay threshold when the numerical tests
succeed; no global routing or final-STA lower bound is claimed.
"""
import array
import collections
import math
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,nodes,prefixes,prune_sinks
from verify_path_witnesses_v2 import graph_records,f32
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
assert shutil.disk_usage(D).free>=80*1024**3
first=read(D/'postcoordination_R1_queries_01/analysis.json');second=read(D/'plateau_R1_counterfactual_01/analysis.json')
assert first['passed'] and second['passed']
for doc in [first,second]:assert all(sha(p)==h for p,h in doc['source_sha256'].items())
witnesses=[next(r for r in doc['results'] if r['improvement_ns']>1e-6) for doc in [first,second]]
caps=array.array('I');caps.frombytes((D/'plateau_R1_queries_02/capacities.bin').read_bytes())
common=sorted(n for n in set(witnesses[0]['suffix_nodes'])&set(witnesses[1]['suffix_nodes']) if caps[n]==1)
assert common;resource_node=common[0]
source=Path(read(D/'postroute_plateau_policy_experiment_01.json')['start_state'])
m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
assert sha(graph)==m['shared_inputs'][str(graph)]['sha256']
driver=D/'current_sta_queries_01/critical_capacity_driver';binary=D/'residual_query_offline_01/graph.bin'
assert sha(driver)==read(D/'current_sta_queries_01/execution.json')['output_sha256']['critical_capacity_driver']
assert sha(binary)==read(binary.with_name('graph_binding.json'))['binary_graph_sha256']
b=D/'endpoint_capacity_reference_01';b.mkdir(exist_ok=False)
files=[Path(__file__),D/'coordinated_repair_tree.py',D/'postcoordination_R1_queries_01/analysis.json',D/'plateau_R1_counterfactual_01/analysis.json',
    D/'plateau_R1_queries_02/capacities.bin',source/'manifest.json',source/'routed.route',graph,driver,binary]
bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(status='registered_before_query',question='Does the shared-node threshold persist even when all route occupancy and retained branches are removed, leaving only fixed SOURCE/SINK endpoints?' ,
    input_run=str(source),targets=[dict(net=r['net'],pin=r['pin']) for r in witnesses],shared_unit_resources=common,test_resource=resource_node,
    selection='First sorted unit-capacity resource shared by both independently audited improving witnesses; not selected from query outcomes.',
    arms=['All other-net occupancy ignored and target tree reduced to its SOURCE root; exact query for each fixed endpoint pair.',
        'Same endpoint-only fully relaxed graph, additionally forbid selected shared resource.'],
    qualification='Optimistic endpoint-only zero-RC graph. No complete route/packing/STA feasibility claim. Persistence of the threshold would strengthen a physical local bound; failure shows that the fixed background/retained-tree constraints matter. No global FPGA optimum or finalCPD bound.',
    source_sha256=bindings,pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],native_calls=0))
switches={}
for section,e in graph_records(graph):
    if section!='switches':break
    t=e.find('timing');switches[int(e.attrib['id'])]=0. if t is None else f32(t.attrib.get('Tdel',0))
traces=read_trace(source/'routed.route');owners=collections.defaultdict(set)
for n,info in traces.items():
    for node in {x.inode for x in info['trace']}:owners[node].add(n)
original={r['net']:from_trace(traces[r['net']]['trace'],switches) for r in witnesses}
retained={r['net']:dict(root=original[r['net']]['root'],edges={},sinks={}) for r in witnesses}
# Optimistic diagnostic: remove all network occupancy, including original other sinks.
owners=collections.defaultdict(set)
assert all(len(ns)<=caps[node] for node,ns in owners.items())
assert not owners.get(resource_node)
rows=[];wanted=set();nreal=len(caps)
for w in witnesses:
    net,pin=w['net'],w['pin'];tree=retained[net];sink=original[net]['sinks'][pin]
    kinds={node.inode:node.kind for node in traces[net]['trace']};prefix=prefixes(tree)
    anchors={node:value for node,value in prefix.items() if kinds[node] not in ['SINK','IPIN']}
    current=prefixes(original[net])[sink]
    for forbidden in [False,True]:
        blocked={node for node,ns in owners.items() if len(ns)-int(net in ns)>=caps[node]}
        blocked|={node for node,capacity in enumerate(caps) if capacity==0}
        if forbidden:blocked.add(resource_node)
        assert not nodes(tree)&blocked
        d=b/f'net{net}_forbid{int(forbidden)}';d.mkdir()
        write(d/'case.json',dict(net=net,pin=pin,sink=sink,tree=tree,anchors=anchors,blocked=sorted(blocked),current_physical_seconds=current))
        with (d/'cases.txt').open('w') as f:
            f.write('1\n'+' '.join(map(str,[net,pin,sink,len(nodes(tree)),len(anchors),len(blocked)]))+'\n')
            f.write(' '.join(map(str,sorted(nodes(tree))))+'\n')
            for node,value in sorted(anchors.items()):f.write(f'{node} {value:.17g}\n')
            f.write(' '.join(map(str,sorted(blocked)))+'\n')
        started=time.monotonic()
        with (d/'stdout.log').open('w') as out,(d/'stderr.log').open('w') as err:
            subprocess.run([str(driver),str(binary),str(d/'cases.txt'),'capacity'],stdout=out,stderr=err,check=True,timeout=120)
        elapsed=time.monotonic()-started;result=None;edges=[]
        for line in (d/'stdout.log').read_text().splitlines():
            v=line.split();assert tuple(map(int,v[1:4]))==(net,pin,1)
            if v[0]=='RESULT':
                assert result is None
                result=dict(net=net,pin=pin,forbidden=forbidden,stop=int(v[4]),expansions=int(v[5]),labels=int(v[6]),peak_heap=int(v[7]),
                    physical_seconds=float(v[8]),lower_seconds=float(v[9]),core_seconds=float(v[10]),edge_count=int(v[11]),process_seconds=elapsed,current_physical_seconds=current)
            else:
                assert v[0]=='EDGE' and int(v[4])==len(edges);edges.append((int(v[5]),int(v[6]),float(v[7])))
        assert result is not None and result['stop']==0 and result['physical_seconds']==result['lower_seconds']
        assert len(edges)==result['edge_count'] and edges[0][0]==sink and edges[-1][1]==nreal
        assert all(a[1]==z[0] for a,z in zip(edges,edges[1:])) and len({u for u,v,w in edges})==len(edges)
        assert edges[-1][2]==anchors[edges[-1][0]] and not {u for u,v,w in edges[:-1]}&nodes(tree)
        assert not {u for u,v,w in edges}&blocked
        assert math.isclose(sum(w for u,v,w in edges),result['physical_seconds'],rel_tol=1e-12,abs_tol=1e-24)
        result['edges']=edges;result['uses_shared_resource']=resource_node in {u for u,v,w in edges}
        rows.append(result);wanted|={(v,u,w) for u,v,w in edges if v!=nreal};write(d/'result.json',result)
        print(dict(net=net,forbidden=forbidden,cost_ns=result['physical_seconds']*1e9),flush=True)
found=set()
for section,e in graph_records(graph):
    if section=='rr_edges':
        a=e.attrib;edge=(int(a['src_node']),int(a['sink_node']),switches[int(a['switch_id'])])
        if edge in wanted:found.add(edge)
assert wanted==found
threshold=max(r['current_physical_seconds'] for r in rows)
equal_current=all(math.isclose(r['current_physical_seconds'],threshold,rel_tol=1e-12,abs_tol=1e-24) for r in rows)
necessity=equal_current and all(r['physical_seconds']>=threshold-1e-23 for r in rows if r['forbidden'])
assert all(sha(p)==h for p,h in bindings.items())
write(b/'analysis.json',dict(passed=True,rows=rows,shared_unit_resources=common,test_resource=resource_node,
    resource_capacity=caps[resource_node],both_current_delays_equal=equal_current,threshold_seconds=threshold,
    subthreshold_shared_resource_necessity_verified=necessity,
    interpretation='If necessity is true, both sub-threshold endpoint-only paths require the same capacity1 node even without any other routes; original legal pair provides an upper reference. If false, the stronger physical bound is not supported and removing the background/retained-tree constraints exposes alternatives. Returned individual paths are optimistic witnesses, not a complete routing or finalCPD result.',
    real_directed_edges_checked=len(wanted),native_calls=0,new_queries=4,source_sha256=bindings))
print(dict(necessity_verified=necessity,threshold_ns=threshold*1e9),flush=True)
