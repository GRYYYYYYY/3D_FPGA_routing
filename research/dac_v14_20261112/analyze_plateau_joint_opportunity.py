#!/usr/bin/env python3
"""Bind the ownership counterfactual and construct jointly compatible references."""
import array
import collections
import itertools
import math
from pathlib import Path
import sys
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,nodes,prefixes,prune_sinks,attach,downstream_pins
from verify_path_witnesses_v2 import graph_records,f32
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

names=['endpoint_capacity_reference_01']+[f'endpoint_resource_{n}_01' for n in [327367,338492,413276,82112]]
docs={name:read(D/name/'analysis.json') for name in names}
for a in docs.values():assert a['passed'] and all(sha(p)==h for p,h in a['source_sha256'].items())
joint=read(D/'joint_critical_reference_01/analysis.json');assert joint['passed'] and joint['subthreshold_shared_resource_necessity_verified']
before=read(D/'plateau_R1_counterfactual_01/cases.json');after=read(D/'plateau_R1_queries_02/cases.json')
keys=['net','pin','sink','root','original_nodes','retained','removed','anchors','current_physical_seconds','original_path','other_sinks','tree_edges']
assert all({k:a[k] for k in keys}=={k:b[k] for k in keys} for a,b in zip(before,after))
caps=array.array('I');caps.frombytes((D/'plateau_R1_queries_02/capacities.bin').read_bytes())
paths=collections.defaultdict(dict)
for name,a in docs.items():
    for i,r in enumerate(a['rows']):
        signature=tuple(u for u,v,w in r['edges'])
        paths[r['net']][signature]=dict(source=name,row=i,result=r)
nets=sorted(paths);assert len(nets)==2
pairs=[]
for a,b in itertools.product(paths[nets[0]].values(),paths[nets[1]].values()):
    sets=[{u for u,v,w in x['result']['edges']} for x in [a,b]]
    conflicts=sorted(n for n in sets[0]&sets[1] if caps[n]<2)
    pairs.append(dict(paths=[a,b],capacity_conflicts=conflicts,max_seconds=max(x['result']['physical_seconds'] for x in [a,b])))
feasible=[p for p in pairs if not p['capacity_conflicts']];assert feasible
best=min(feasible,key=lambda p:(p['max_seconds'],tuple(tuple(u for u,v,w in x['result']['edges']) for x in p['paths'])))
unrestricted=[r for r in docs[names[0]]['rows'] if not r['forbidden']]
lower=max(r['physical_seconds'] for r in unrestricted)
assert math.isclose(best['max_seconds'],lower,rel_tol=1e-12,abs_tol=1e-24)
source=Path(read(D/'postroute_plateau_policy_experiment_01.json')['start_state']);m=read(source/'manifest.json')
assert m['metrics']['native_full_check_passed'] and read(source/'independent_audit.json')['audit']['passed']
graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);switches={}
for section,e in graph_records(graph):
    if section!='switches':break
    t=e.find('timing');switches[int(e.attrib['id'])]=0. if t is None else f32(t.attrib.get('Tdel',0))
traces=read_trace(source/'routed.route');owners=collections.defaultdict(set)
for net,info in traces.items():
    for node in {x.inode for x in info['trace']}:owners[node].add(net)
original={n:from_trace(traces[n]['trace'],switches) for n in nets};proposals={};splice=[]
for item in best['paths']:
    r=item['result'];net,pin=r['net'],r['pin'];kept=prune_sinks(original[net],[pin]);edges=r['edges']
    forward=[edges[-1][0]]+[u for u,v,w in reversed(edges[:-1])];weights=[w for u,v,w in reversed(edges[:-1])]
    intersections=[i for i,node in enumerate(forward) if node in nodes(kept)];assert intersections
    at=max(intersections);anchor=forward[at]
    tree=attach(kept,pin,original[net]['sinks'][pin],forward[at:],[None]*len(weights[at:]),weights[at:])
    actual=prefixes(tree)[original[net]['sinks'][pin]]
    assert math.isclose(actual,r['physical_seconds'],rel_tol=1e-12,abs_tol=1e-24)
    proposals[net]=tree
    splice.append(dict(net=net,pin=pin,anchor=anchor,retained_intersections=[forward[i] for i in intersections],
        suffix_nodes=forward[at:],suffix_weights=weights[at:],physical_seconds=actual,reference_source=item['source'],reference_row=item['row']))
proposal_nodes={n:nodes(t) for n,t in proposals.items()};conflicts={};self_conflicts=[]
for node in set().union(*proposal_nodes.values()):
    assigned=[n for n,ns in proposal_nodes.items() if node in ns];others=owners[node]-set(nets)
    if len(assigned)>caps[node]:self_conflicts.append(node)
    if len(assigned)+len(others)>caps[node]:conflicts[str(node)]=dict(capacity=caps[node],critical_nets=assigned,other_nets=sorted(others))
assert not self_conflicts
blockers=sorted({n for c in conflicts.values() for n in c['other_nets']});affected=[]
for n in blockers:
    tree=from_trace(traces[n]['trace'],switches)
    resources=sorted(int(node) for node,c in conflicts.items() if n in c['other_nets'])
    pins=sorted({p for node in resources for p in downstream_pins(tree,node)})
    affected.append(dict(net=n,name=traces[n]['name'],resources=resources,affected_pins=pins,total_pins=len(tree['sinks'])))
old_owners=read(D/'postcoordination_R1_queries_01/occupancy_owners.json');new_owners=read(D/'plateau_R1_queries_02/occupancy_owners.json')
ownership_changes=[dict(node=int(n),before=old_owners.get(n,[]),after=new_owners.get(n,[])) for n in sorted(old_owners.keys()|new_owners.keys(),key=int) if old_owners.get(n,[])!=new_owners.get(n,[])]
evidence=[*[D/n/'analysis.json' for n in names],D/'joint_critical_reference_01/analysis.json',D/'plateau_R1_counterfactual_01/analysis.json',D/'plateau_R1_queries_02/analysis.json',D/'plateau_R1_step_01/decision.json',D/'plateau_R1_counterfactual_01/cases.json',D/'plateau_R1_queries_02/cases.json',source/'routed.route',source/'independent_audit.json',Path(__file__)]
write(D/'plateau_joint_opportunity_01.json',dict(passed=True,source_run=str(source),same_five_target_trees_prefixes_endpoints=True,
    ownership_changes=ownership_changes,conditional_joint_delay_threshold_seconds=joint['threshold_seconds'],conditional_shared_resource=joint['test_resource'],
    path_pool_unique_counts={str(n):len(p) for n,p in paths.items()},path_pairs_tested=len(pairs),path_pairs_RR_capacity_feasible=len(feasible),
    optimistic_joint_minimax_seconds=best['max_seconds'],optimistic_independent_lower_seconds=lower,optimistic_bounds_match=True,
    best_pair=best,actual_retained_tree_splices=splice,critical_pair_self_conflicts=self_conflicts,
    current_other_net_conflicts=conflicts,blockers=blockers,affected_blocker_subtrees=affected,
    total_blocker_sinks=sum(len(r['affected_pins']) for r in affected),native_calls=0,
    qualification='The matching bounds establish the optimal minimax physical path cost only in the two-endpoint zero-RC RR-node-capacity relaxation with other routes/terminals omitted. Both reference paths also attach to actual retained trees at unchanged cost, but their current other-net conflicts remain. No completed coordinated reroute, native FULL or final CPD gain follows from this reference.',
    source_sha256={str(p):sha(p) for p in evidence}))
print(dict(unique_paths={n:len(p) for n,p in paths.items()},pairs=len(pairs),feasible_pairs=len(feasible),relaxed_joint_ns=best['max_seconds']*1e9,blockers=blockers,blocker_sinks=sum(len(r['affected_pins']) for r in affected)),flush=True)
