#!/usr/bin/env python3
"""Count exact winning timing paths in an already certified current cone."""
import collections,functools
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
p=D/'bnn_release_joint_dev_01/Tf_combined_weighted_soft_successor_cone.json';c=read(p)
assert c['passed'] and all(sha(path)==h for path,h in c['source_sha256'].items())
rows=[]
for launch,t in c['cones'].items():
 assert not t['unresolved'];adj=collections.defaultdict(list);arcs=[]
 for f in t['fanins']:
  for q in f['choices']:
   if q['edge'] in f['winning_edges']:
    assert q['gap_s']==0;adj[q['source']].append(f['node']);arcs.append((q['source'],f['node'],q['edge']))
 @functools.lru_cache(None)
 def paths(a,b):
  if a==b:return 1
  return sum(paths(v,b) for v in adj[a])
 for ep in c['selected_endpoints']:
  if str(ep['identity'][3])!=launch:continue
  endpoint=ep['identity'][0];sources=t['sources'];total=sum(paths(s,endpoint) for s in sources);assert total>0
  pins=[]
  for q in c['routed_connections']:
   ns=sorted({a['tnode_external'] for a in q['atoms']} & set(t['nodes']))
   pins += [dict(net=q['net'],pin=q['pin'],node=n,paths_through=sum(paths(s,n) for s in sources)*paths(n,endpoint)) for n in ns]
  pairs=[]
  for a in pins:
   for b in pins:
    if a['node']==b['node']:continue
    between=paths(a['node'],b['node'])
    if between:
     count=sum(paths(s,a['node']) for s in sources)*between*paths(b['node'],endpoint)
     assert count<=total
     pairs.append(dict(upstream=[a['net'],a['pin']],downstream=[b['net'],b['pin']],winning_paths_through_both=count,all_current_winning_paths=count==total))
  rows.append(dict(launch_domain=launch,endpoint=ep['identity'],winning_edge_paths=total,pins=pins,ordered_connection_pairs=pairs))
out=D/'bnn_current_critical_dependencies_01.json';assert not out.exists()
write(out,dict(passed=True,rows=rows,source_sha256={str(p):sha(p),str(Path(__file__).resolve()):sha(__file__)},
 qualification='Exact edge-path counts in the currently certified maximum-arrival subgraph only. Not all near-critical paths or hypothetical post-change timing. Serial membership does not prove any resource exchange is legal or CPD-neutral; complete native reroute/STA still required.'))
for r in rows:
 print('winning paths',r['winning_edge_paths'],'pins',[(p['net'],p['pin'],p['paths_through']) for p in r['pins']],flush=True)
 print('26319/26320',[p for p in r['ordered_connection_pairs'] if set([p['upstream'][0],p['downstream'][0]])=={26319,26320}],flush=True)
