#!/usr/bin/env python3
"""Discover extra noncritical owner branches along audited critical-owner paths."""
import argparse,collections,copy,resource,sys,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from immutable_rr_audit_cache import GraphAuditCache,KINDS
from coordinated_repair_tree import from_trace,nodes,prune_sinks,prefixes,attach,downstream_pins
from conditional_distance_certificate import certify
from check_route import read_trace
p=argparse.ArgumentParser()
for n in ['diagnostic','feedback','output','audit-cache']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));b=a.output.resolve();b.mkdir(exist_ok=False)
previous=a.diagnostic.resolve();c=read(previous/'completion.json');assert c['passed'] and all(sha(p)==h for p,h in c['source_sha256'].items())
f=a.feedback.resolve();op=read(f/'owners/completion.json');cone=read(f/'cone.json');assert op['passed'] and Path(op['input_state'])==Path(c['input_state']);source=Path(read(Path(c['input_state'])/'completion.json')['run'])
m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);g=GraphAuditCache(graph,a.audit_cache)
files=[Path(__file__).resolve(),D/'conditional_distance_certificate.py',previous/'completion.json',f/'owners/completion.json',f/'capacity/occupancy_owners.json',f/'cone.json',source/'routed.route',a.audit_cache.resolve()/'completion.json']
bound={str(p):sha(p) for p in files};write(b/'registration.json',dict(status='registered_before_scope_expansion',source_sha256=bound,native_calls=0,new_queries=0,question='Which additional noncritical branches block the optimistic critical-owner paths, and can exact relaxed distances be certified under the expanded actual occupancy without repeating queries?'))
owners={int(n):set(ns) for n,ns in read(f/'capacity/occupancy_owners.json').items()};traces=read_trace(source/'routed.route');protected={x['net'] for x in cone['routed_connections']};zero=set(map(int,np.flatnonzero(g.capacities==0)));rows=[]
for index,r in enumerate(c['rows']):
 target=tuple(r['target']);old_removed={int(n):set(ps) for n,ps in r['removed_pins'].items()};removed=copy.deepcopy(old_removed);trees={n:from_trace(traces[n]['trace'],g.switches) for n in removed};pruned={n:prune_sinks(trees[n],ps) for n,ps in removed.items()};oprow=next(x for x in op['rows'] if tuple(x['target'])==target)
 target_tree=attach(pruned[target[0]],target[1],trees[target[0]]['sinks'][target[1]],oprow['relaxed_suffix_nodes'],oprow['relaxed_suffix_switches'],[g.switches[s] for s in oprow['relaxed_suffix_switches']])
 partial={**pruned,target[0]:target_tree};relaxed=r['modes']['noncritical_background_relaxed']['answers'];extra_resources=collections.defaultdict(set);blocked_rows=[]
 def actual_owners(node):
  ns=set(owners.get(node,[]))
  for net,tree in partial.items():
   ns.discard(net)
   if node in nodes(tree):ns.add(net)
  return ns
 for answer in relaxed:
  assert answer['stop']==0
  for node in answer['suffix_nodes']:
   other=actual_owners(node)-{answer['net']};need=len(other)+1-int(g.capacities[node])
   if need<=0:continue
   releasable=other-protected;assert len(releasable)>=need,'Witness displaces an unselected current critical owner'
   # Capacity-one conflicts have a unique required owner. For capacity>1,
   # release all noncritical owners conservatively; this is not minimality.
   for net in releasable:extra_resources[net].add(node)
   blocked_rows.append(dict(owner_query=[answer['net'],answer['pin']],node=node,capacity=int(g.capacities[node]),other_nets=sorted(other),required_releases=need,noncritical_owners=sorted(releasable)))
 for net,resources in extra_resources.items():
  if net not in trees:trees[net]=from_trace(traces[net]['trace'],g.switches)
  pins=set().union(*(downstream_pins(trees[net],node) for node in resources));assert pins
  removed.setdefault(net,set()).update(pins)
 pruned={net:prune_sinks(trees[net],pins) for net,pins in removed.items()};partial={**pruned,target[0]:target_tree}
 counts=collections.Counter({node:len(ns) for node,ns in owners.items()})
 for net,tree in partial.items():
  for node in nodes(trees[net]):counts[node]-=1
  for node in nodes(tree):counts[node]+=1
 g.require_occupancy(counts)
 directory=b/f'target_{index:03d}';directory.mkdir();new_cases=[];certificates=[]
 old_cases={(x['net'],x['pin']):x for x in read(previous/f'target_{index:03d}/noncritical_background_relaxed/cases.json')}
 for answer in relaxed:
  net,pin=answer['net'],answer['pin'];tree=partial[net];retained=nodes(tree);values=prefixes(tree);blocked=zero|{node for node,count in counts.items() if count-int(node in retained)>=g.capacities[node]}
  newcase=dict(net=net,pin=pin,sink=trees[net]['sinks'][pin],retained=sorted(retained),anchors={str(n):values[n] for n in sorted(retained) if KINDS[int(g.nodes[n,1])] not in ['IPIN','SINK']},blocked=sorted(blocked))
  assert not retained&blocked;g.require_edges(zip(answer['suffix_nodes'],answer['suffix_nodes'][1:],answer['suffix_switches']))
  certificate=certify(old_cases[net,pin],newcase,answer,g.switches);assert certificate['certified'];certificate.update(net=net,pin=pin,current_physical_s=answer['current_physical_s'],delta_s=answer['delta_s']);new_cases.append(newcase);certificates.append(certificate)
 # Independently test that the critical-owner witness paths can coexist as
 # complete trees. Noncritical released pins remain absent pending restoration.
 core=copy.deepcopy(partial);compatible=True;conflicts=[]
 for answer in relaxed:
  net,pin=answer['net'],answer['pin'];tree=core[net];edges=tree['edges'];forward=answer['suffix_nodes'];switches=answer['suffix_switches']
  for u,v,sw in zip(forward,forward[1:],switches):
   entry=(u,sw,g.switches[sw])
   if v in edges and tuple(edges[v])!=entry:compatible=False;conflicts.append(dict(net=net,node=v,existing=edges[v],requested=entry))
   else:edges[v]=entry
  tree['sinks'][pin]=trees[net]['sinks'][pin]
 if compatible:
  for net in r['critical_owners']:
   values=prefixes(core[net]);assert core[net]['sinks']==trees[net]['sinks']
   for answer in relaxed:
    if answer['net']==net:assert abs(values[core[net]['sinks'][answer['pin']]]-answer['distance_s'])<1e-23
  joint_counts=collections.Counter(counts)
  for net in r['critical_owners']:
   for node in nodes(partial[net]):joint_counts[node]-=1
   for node in nodes(core[net]):joint_counts[node]+=1
  g.require_occupancy(joint_counts)
 write(directory/'expanded_cases.json',new_cases);write(directory/'partial_core_trees.json',core)
 old_count=sum(map(len,old_removed.values()));new_count=sum(map(len,removed.values()));row=dict(target=list(target),old_removed_pins=r['removed_pins'],expanded_removed_pins={str(n):sorted(ps) for n,ps in removed.items()},old_connections=old_count,expanded_connections=new_count,additional_connections=new_count-old_count,extra_blocked_resources=blocked_rows,conditional_distance_certificates=certificates,critical_core_paths_compatible=compatible,critical_core_conflicts=conflicts,current_winning_path_model=r['modes']['noncritical_background_relaxed']['path_model'],partial_core_trees=str(directory/'partial_core_trees.json'),new_queries=0)
 rows.append(row)
 for sub in ['current_other_occupancy','noncritical_background_relaxed']:
  for name in ['analysis.json','cases.json','stdout.log']:p=previous/f'target_{index:03d}'/sub/name;bound[str(p)]=sha(p)
write(b/'completion.json',dict(passed=True,rows=rows,input_state=c['input_state'],source_sha256=bound,new_queries=0,native_calls=0,route_commits=0,complete_process_seconds=time.monotonic()-started,
 qualification='Relaxed exact distance is reused only with unchanged retained anchors, restricted-domain inclusion and the same witness feasible under expanded actual partial occupancy. Critical-owner core trees are checked when compatible. Released noncritical pins are still missing; this is not a legal final candidate or native STA improvement. Capacity>1 owner choice is conservative, not a minimum-closure proof.'))
print([dict(target=r['target'],old=r['old_connections'],expanded=r['expanded_connections'],core_compatible=r['critical_core_paths_compatible'],new_queries=0) for r in rows],flush=True)
