#!/usr/bin/env python3
"""Select mutually compatible paths from already audited IPIN alternatives."""
import argparse,array,collections,resource,signal,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from finite_capacity_assignment import solve
from verify_path_witnesses_v2 import graph_records
sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace
p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);a=p.parse_args()
started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800);ref=a.reference.resolve();b=a.batch.resolve();b.mkdir(exist_ok=False)
c=read(ref/'completion.json');assert c['passed'] and all(sha(p)==h for p,h in c['source_sha256'].items());reg=read(ref/'registration.json');source=Path(reg['input_run']);m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
files=[Path(__file__),D/'finite_capacity_assignment.py',D/'test_finite_capacity_assignment.py',ref/'completion.json',ref/'original_cases.json',ref/'options.json',ref/'matching.json',graph];bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(status='registered_before_search',question='Can full-node MRV/mandatory-resource selection find a compatible strict-budget combination in the already audited IPIN path pool, without more distance queries?',source_sha256=bindings,limits=dict(states=100000,seconds=60),native_calls=0,new_distance_queries=0))
caps=array.array('I')
for section,e in graph_records(graph):
 if section=='rr_nodes':assert int(e.attrib['id'])==len(caps);caps.append(int(e.attrib['capacity']))
 elif section=='rr_edges':break
cases={r['net']:r for r in read(ref/'original_cases.json')};fixed={n:set(c['retained']) for n,c in cases.items()};offset={int(n):x for n,x in read(ref/'matching.json')['offsets_s'].items()};pools={n:[] for n in cases}
for option in read(ref/'options.json'):
 n=option['net']
 if option['cost_s']+offset[n]<0:pools[n].append(dict(nodes=fixed[n]|set(option['forward']),cost=option['cost_s'],option=option))
result=solve(pools,fixed,caps);write(b/'search.json',result)
if result['status']=='compatible':
 selected={n:pools[n][i] for n,i in result['assignment'].items()};counts=collections.Counter(node for path in selected.values() for node in path['nodes']);assert all(v<=caps[n] for n,v in counts.items())
 owners=collections.defaultdict(set)
 for net,info in read_trace(source/'routed.route').items():
  for node in {r.inode for r in info['trace']}:owners[node].add(net)
 picked=collections.defaultdict(set)
 for net,path in selected.items():
  for node in path['nodes']:picked[node].add(net)
 conflicts={str(node):dict(capacity=int(caps[node]),other_nets=sorted(owners[node]-set(selected)),selected_nets=sorted(nets)) for node,nets in picked.items() if len((owners[node]-set(selected))|nets)>caps[node]}
 targets=[]
 for n,path in selected.items():
  o=path['option'];targets.append(dict(net=n,pin=cases[n]['pin'],sink=cases[n]['sink'],suffix_nodes=o['forward'],suffix_weights=o['weights'],suffix_switches=o['switches'],physical_seconds=o['cost_s'],before_physical_seconds=cases[n]['current_physical_seconds'],offset_s=offset[n],proxy_score_s=o['cost_s']+offset[n]))
 write(b/'opportunity.json',dict(status='compatible',input_run=str(source),targets=targets,current_other_net_conflicts=conflicts,near_ns=reg['near_ns'],proxy_objective=max(t['proxy_score_s'] for t in targets),qualification='Finite audited path pool; full selected-tree node capacities and strict proxy budgets satisfied. Background restoration and native FULL/STA remain required.'))
assert all(sha(p)==h for p,h in bindings.items())
for p in b.iterdir():
 if p.is_file():bindings[str(p)]=sha(p)
write(b/'completion.json',dict(passed=True,status=result['status'],states=result['states'],search_seconds=result['seconds'],complete_process_seconds=time.monotonic()-started,pool_sizes={n:len(p) for n,p in pools.items()},new_distance_queries=0,native_calls=0,source_sha256=bindings,
 qualification='Negative result excludes only these known paths, not the full RR graph; limit is unknown. A compatible result is an explicit selected-tree capacity witness, not complete routing quality.'))
if result['status']=='compatible':write(b/'candidate_binding.json',dict(passed=True,source_sha256={str(p):sha(p) for p in [b/'opportunity.json',b/'registration.json',b/'completion.json']}))
print(dict(status=result['status'],states=result['states'],seconds=time.monotonic()-started),flush=True)
