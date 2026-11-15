#!/usr/bin/env python3
"""Audit current-STA capacity queries and serialize independent proposals."""
import argparse
import array
import collections
import math
from pathlib import Path
import re
import resource
import signal
import sys
from retained_prefix_workflow import D,read,write,sha
from check_route import read_trace
from immutable_rr_audit_cache import GraphAuditCache
import numpy as np

resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
parser=argparse.ArgumentParser();parser.add_argument('--batch',type=Path,required=True);parser.add_argument('--query-graph',type=Path,required=True);parser.add_argument('--audit-cache',type=Path,required=True);args=parser.parse_args()
b=args.batch.resolve();ex=read(b/'execution.json');reg=read(b/'execution_registration.json')
assert all(sha(p)==h for p,h in ex['source_sha256'].items())
assert all(sha(b/p)==h for p,h in ex['output_sha256'].items())
assert read(b/'unit_validation.json')['passed']
cases={(c['net'],c['pin']):c for c in read(b/'cases.json')};rows={};paths=collections.defaultdict(list)
for line in (b/'query_stdout.log').open():
    v=line.split();key=tuple(map(int,v[1:4]))
    if v[0]=='RESULT':
        assert key not in rows
        rows[key]=dict(net=key[0],pin=key[1],mode=key[2],stop=int(v[4]),expansions=int(v[5]),labels=int(v[6]),peak_heap=int(v[7]),
            physical_seconds=float(v[8]),lower_seconds=float(v[9]),query_seconds=float(v[10]),edge_count=int(v[11]))
    else:
        assert v[0]=='EDGE' and int(v[4])==len(paths[key]);paths[key].append((int(v[5]),int(v[6]),float(v[7])))
assert rows.keys()=={(net,pin,m) for net,pin in cases for m in reg['query_modes']}
current=Path(reg['input_run']);manifest=read(current/'manifest.json')
graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
binding_path=args.query_graph.resolve()/'graph_binding.json';binding=read(binding_path);assert binding['source_rrg_sha256']==sha(graph) and binding['binary_graph_sha256']==sha(args.query_graph.resolve()/'graph.bin');nreal=binding['nodes']
owners={int(k):v for k,v in read(b/'occupancy_owners.json').items()}
original=read_trace(current/'routed.route');recount=collections.defaultdict(list)
for net,info in original.items():
    for node in {n.inode for n in info['trace']}:recount[node].append(net)
assert owners==recount
caps=array.array('I');caps.frombytes((b/'capacities.bin').read_bytes());assert len(caps)==nreal
wanted={(v,u,w) for path in paths.values() for u,v,w in path if v!=nreal}
needed={node for c in cases.values() for node in c['original_nodes']}|{u for path in paths.values() for u,v,w in path}
cache=GraphAuditCache(graph,args.audit_cache);assert cache.n==nreal
assert np.array_equal(np.asarray(caps,dtype=np.int64),cache.capacities)
metadata=cache.metadata(needed);switches=cache.switches;edge_switches=collections.defaultdict(list);checked_caps=nreal
for u,v,weight in wanted:
 lo=np.uint64((u*nreal+v)*cache.stride);hi=lo+np.uint64(cache.stride);begin,end=np.searchsorted(cache.edges,[lo,hi])
 for value in cache.edges[begin:end]:
  sw=int(value)%cache.stride
  if switches[sw]==weight:edge_switches[u,v,weight].append(sw)
write(b/'physical_query_cache_receipt.json',cache.receipt)
assert checked_caps==nreal and wanted==edge_switches.keys()
near=lambda x,y:math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-24)
repairs=[]
for key,r in rows.items():
    c=cases[key[:2]];net,pin=key[:2];path=paths[key];tree=set(c['retained']);owned=set(c['original_nodes']);anchors={int(k):v for k,v in c['anchors'].items()}
    assert len(path)==r['edge_count'] and r['stop']==0 and near(r['physical_seconds'],r['lower_seconds'])
    assert path[0][0]==c['sink'] and path[-1][1]==nreal
    assert all(a[1]==z[0] for a,z in zip(path,path[1:])) and len({e[0] for e in path})==len(path)
    anchor=path[-1][0];assert anchor in anchors and near(path[-1][2],anchors[anchor])
    assert all(u not in tree for u,v,w in path[:-1])
    assert near(sum(e[2] for e in path),r['physical_seconds'])
    parents={v:(u,sw) for u,v,sw,w in c['tree_edges']}
    prefix=0.;node=anchor
    while node in parents:
        node,sw=parents[node];prefix+=switches[sw]
    assert node==c['root'] and near(prefix,anchors[anchor])
    forward=[anchor]+[u for u,v,w in reversed(path[:-1])]
    suffix_switches=[min(edge_switches[v,u,w]) for u,v,w in reversed(path[:-1])]
    new_nodes=tree|set(forward)
    conflicts={str(node):dict(capacity=caps[node],other_nets=[n for n in owners.get(node,[]) if n!=net])
        for node in new_nodes if len(owners.get(node,[]))-int(node in owned)+1>caps[node]}
    assert r['physical_seconds']<=c['current_physical_seconds']+1e-23
    if key[2]==1:assert not conflicts
    for sink in c['other_sinks']:
        node=sink
        while node in parents:assert node in tree;node=parents[node][0]
        assert node==c['root']
    r.update(current_physical_seconds=c['current_physical_seconds'],improvement_ns=(c['current_physical_seconds']-r['physical_seconds'])*1e9,
        anchor=anchor,suffix_nodes=forward,suffix_switches=suffix_switches,
        capacity_conflicts=conflicts,rr_capacity_feasible=not conflicts,
        retained_nodes=len(tree),removed_nodes=len(c['removed']),added_nodes=len(new_nodes-owned),
        native_full_checked=False,final_STA_evaluated=False)
    if key[2]==1 and r['improvement_ns']>1e-6:
        repairs.append((r,c,forward,suffix_switches))
assert len(repairs)<=len(cases)

# Serialize only genuinely improving capacity-feasible candidates into copies.
# Every other net section is preserved byte-for-byte; the original stays frozen.
route_text=(current/'routed.route').read_text()
for r,c,forward,suffix_switches in repairs:
    net,pin=r['net'],r['pin'];retained=set(c['retained']);children=collections.defaultdict(list)
    for u,v,sw,w in c['tree_edges']:
        if u in retained and v in retained:children[u].append((v,sw))
    for u,v,sw in zip(forward,forward[1:],suffix_switches):children[u].append((v,sw))
    sink_pins={}
    for n in original[net]['trace']:
        if n.kind=='SINK':
            assert n.inode not in sink_pins or sink_pins[n.inode]==n.pin
            sink_pins[n.inode]=n.pin
    lines=[];seen=set()
    def emit(node,sw):
        m=metadata[node];xyz=lambda p:'('+','.join(map(str,p))+')'
        label='Class:' if m['kind'] in ['SOURCE','SINK'] else 'Pin:' if m['kind'] in ['OPIN','IPIN'] else 'Track:'
        line=f"Node:\t{node}\t{m['kind']} {xyz(m['low'])}"
        if m['low']!=m['high']:line+=' to '+xyz(m['high'])
        line+=f"  {label} {m['ptc']}  Switch: {sw}"
        if m['kind']=='SINK':line+=f' Net_pin_index: {sink_pins[node]}'
        lines.append(line+'\n')
    def visit(node):
        assert node not in seen;seen.add(node)
        if not children[node]:emit(node,-1)
        for child,sw in children[node]:emit(node,sw);visit(child)
    visit(c['root']);assert seen==retained|set(forward)
    match=re.search(r'^Net '+str(net)+r' \(.*?\)\n.*?(?=^Net |\Z)',route_text,re.M|re.S);assert match
    header=match.group(0).splitlines()[0]+'\n\n'
    replacement=header+''.join(lines)+'\n'
    result=route_text[:match.start()]+replacement+route_text[match.end():]
    target=b/f'repair_net{net}_pin{pin}.route';target.write_text(result)
    parsed=read_trace(target)
    assert parsed.keys()==original.keys()
    assert all(parsed[n]==original[n] for n in original if n!=net)
    old_paths={}
    def edge_set(info):
        return {(u.inode,v.inode,u.switch) for u,v in zip(info['trace'],info['trace'][1:]) if u.switch!=-1}
    expected={(u,v,sw) for u,v,sw,w in c['tree_edges'] if u in retained and v in retained}|set(zip(forward,forward[1:],suffix_switches))
    assert edge_set(parsed[net])==expected
    assert {(n.inode,n.pin) for n in parsed[net]['trace'] if n.kind=='SINK'}==set(sink_pins.items())
    r['candidate_route']=str(target);r['candidate_route_sha256']=sha(target)
assert all(sha(p)==h for p,h in ex['source_sha256'].items())
write(b/'analysis.json',dict(passed=True,native_route_calls=0,results=list(rows.values()),
    directed_edges_checked=len(wanted),all_rr_capacities_checked=checked_caps,
    source_sha256={str(p):sha(p) for p in [Path(__file__),b/'execution.json',b/'cases.json',b/'query_stdout.log',graph,binding_path,args.audit_cache.resolve()/'completion.json',D/'immutable_rr_audit_cache.py',b/'physical_query_cache_receipt.json']},
    qualification='Exact shortest path only for zero-RC, full-device fixed-tree graph and stated graph-derived anchors. Other-net RR occupancy is fixed; native reserved-OPIN/nonconfig/bus-mux checks and finalSTA still pending. Targets selected by generic current-state STA selector, not hardcoded identities. This remains an external prototype; native FULL/STA acceptance pending. Candidate files are separate copies; all other net traces and all other terminal identities preserved.'))
print([{k:v for k,v in r.items() if k in ['net','pin','mode','physical_seconds','improvement_ns','rr_capacity_feasible','candidate_route']} for r in rows.values()],flush=True)
