"""Exact current-winning-path action patterns without materializing each path.

This is a grouping reference, not a post-reroute CPD/legality prediction. Action
bits are idempotent, including multiple atom pins mapping to one routed sink.
"""
import collections,math
from fractions import Fraction

def patterns(cone,actions):
 assert cone['passed'];all_patterns=collections.Counter();details=[]
 for domain,t in cone['cones'].items():
  assert not t['unresolved'];nodes=set(t['nodes']);sources=set(t['sources']);parents={};children=collections.defaultdict(list)
  for f in t['fanins']:
   ps=[p['source'] for p in f['choices'] if p['edge'] in f['winning_edges']]
   assert len(ps)==len(f['winning_edges']) and ps and all(p in nodes for p in ps)
   parents[f['node']]=ps
   for source in ps:children[source].append(f['node'])
  assert nodes==sources|parents.keys() and not sources&parents.keys()
  indegree={n:len(parents.get(n,[])) for n in nodes};ready=collections.deque(sorted(sources));counts={};visited=0
  while ready:
   n=ready.popleft();bits=0
   for i,a in enumerate(actions):
    if n in a['atom_nodes']:bits|=1<<i
   paths=collections.Counter({bits:1}) if n in sources else collections.Counter()
   if n not in sources:
    for p in parents[n]:
     for mask,count in counts[p].items():paths[mask|bits]+=count
   assert paths;counts[n]=paths;visited+=1
   for child in children[n]:
    indegree[child]-=1
    if indegree[child]==0:ready.append(child)
  assert visited==len(nodes),'Cyclic or incomplete certified subgraph'
  for ep in cone['selected_endpoints']:
   if str(ep['identity'][3])!=str(domain):continue
   value=counts[ep['identity'][0]];all_patterns.update(value)
   details.append(dict(endpoint=ep['identity'],edge_paths=sum(value.values()),distinct_patterns=len(value)))
 assert all_patterns
 return dict(pattern_counts=dict(all_patterns),edge_paths=sum(all_patterns.values()),distinct_patterns=len(all_patterns),endpoints=details)

def evaluate(pattern_data,actions,selected):
 selected=set(selected);assert selected<=set(range(len(actions)));repair=set();gain={}
 for i in selected:
  a=actions[i];assert math.isfinite(a['optimistic_gain_ns']) and a['optimistic_gain_ns']>0
  repair.add(tuple(a['target']));repair.update(map(tuple,a['donors']));gain[i]=Fraction(a['optimistic_gain_ns'])
 distribution=collections.Counter()
 for mask,count in pattern_data['pattern_counts'].items():
  total=sum((gain[i] for i in selected if int(mask)&(1<<i)),Fraction())
  distribution[total]+=count
 minimum=min(distribution)
 return dict(repair_connections=len(repair),repair_pins=sorted(repair),min_current_winning_path_gain_ns=float(minimum),all_current_paths_covered=minimum>0,
  gain_distribution=[dict(gain_ns=float(value),edge_paths=count) for value,count in sorted(distribution.items())])
