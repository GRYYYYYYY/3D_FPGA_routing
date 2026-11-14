#!/usr/bin/env python3
"""Enforce complete selected-tree capacity after the optimistic IPIN assignment."""
import array,collections,math,resource,shutil,signal,subprocess,time,argparse
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_frontier_queries import write_cases
from timing_budget_cbs import solve
from verify_path_witnesses_v2 import graph_records,f32

p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);a=p.parse_args()
start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800);assert shutil.disk_usage(D).free>=80*1024**3
ref=a.reference.resolve();b=a.batch.resolve();b.mkdir(exist_ok=False);complete=read(ref/'completion.json');assert complete['passed'] and all(sha(p)==h for p,h in complete['source_sha256'].items())
reg=read(ref/'registration.json');source=Path(reg['input_run']);manifest=read(source/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);driver=D/'current_sta_queries_01/critical_capacity_driver';binary=D/'residual_query_offline_01/graph.bin'
files=[Path(__file__),D/'timing_budget_cbs.py',D/'test_timing_budget_cbs.py',ref/'completion.json',ref/'matching.json',ref/'options.json',ref/'original_cases.json',graph,driver,binary];bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(status='registered_before_CBS',question='Can the six current-STA input-cone connections all meet strictly improved slack-offset budgets with full RR-node compatibility, while background nets are still relaxed?',reference=str(ref),input_run=str(source),source_sha256=bindings,
 objective='Lexicographic maximum (newdelay-currentdelay+worstslack-currentslack), then total physical delay; all per-agent proxy scores must be strictly negative.',
 query_reuse='A known witness achieving the maximum valid subset-query lower bound is exact under the new constraints. Exact out-of-budget subset lower bounds can prune without another query.',
 limits=dict(states=256,search_seconds=900,query_seconds=120,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3),native_calls=0))
caps=array.array('I');switches={}
for sec,e in graph_records(graph):
 if sec=='switches':t=e.find('timing');switches[int(e.attrib['id'])]=0 if t is None else f32(t.attrib.get('Tdel',0))
 elif sec=='rr_nodes':assert len(caps)==int(e.attrib['id']);caps.append(int(e.attrib['capacity']))
 else:break
cases={c['net']:c for c in read(ref/'original_cases.json')};fixed={n:set(c['retained']) for n,c in cases.items()};match=read(ref/'matching.json');offset={int(n):x for n,x in match['offsets_s'].items()};zero={n for n,c in enumerate(caps) if c==0};pool=collections.defaultdict(list)
def option_path(r):return dict(nodes=fixed[r['net']]|set(r['forward']),cost=r['cost_s'],forward=r['forward'],weights=r['weights'],origin=str(ref/'options.json'))
for r in read(ref/'options.json'):pool[r['net']].append(option_path(r))
lower={n:min(x['cost'] for x in rows) for n,rows in pool.items()};initial={r['net']:option_path(r) for r in match['chosen']}
for n in initial:
 if initial[n]['cost']!=lower[n]:initial[n]=next(r for r in pool[n] if r['cost']==lower[n])
assert all(p['cost']==lower[n] for n,p in initial.items())
cache={};receipts=[];known_bounds={n:[(frozenset(),lower[n])] for n in cases};newpaths=[]
def query(net,forbidden):
 forbidden=frozenset(forbidden);key=net,forbidden
 if key in cache:return cache[key]
 bound=max(cost for subset,cost in known_bounds[net] if subset<=forbidden)
 receipt=dict(net=net,pin=cases[net]['pin'],forbidden=sorted(forbidden),certified_lower_s=bound)
 if bound+offset[net]>=0:
  receipt.update(kind='reused_budget_exclusion',reason='Exact subset lower bound already exceeds strict slack-offset budget');result=None
 else:
  result=next((p for p in pool[net] if p['cost']==bound and not p['nodes']&forbidden),None)
  if result is not None:receipt.update(kind='reused_exact_witness',physical_cost=result['cost'],origin=result['origin'])
  else:
   directory=b/f'query_{len(receipts):03d}_net{net}';directory.mkdir();c=dict(cases[net],blocked=sorted(zero|forbidden));assert not fixed[net]&set(c['blocked']);write_cases(directory/'case.txt',[c]);t=time.monotonic()
   with (directory/'stdout.log').open('w') as out,(directory/'stderr.log').open('w') as err:proc=subprocess.run([str(driver),str(binary),str(directory/'case.txt'),'capacity'],stdout=out,stderr=err,timeout=120)
   receipt.update(kind='new_exact_query',process_seconds=time.monotonic()-t,returncode=proc.returncode);assert proc.returncode==0;edges=[]
   for line in (directory/'stdout.log').read_text().splitlines():
    v=line.split();assert tuple(map(int,v[1:4]))==(net,c['pin'],1)
    if v[0]=='RESULT':receipt.update(stop=int(v[4]),physical_cost=float(v[8]),lower_s=float(v[9]),core_seconds=float(v[10]))
    else:assert v[0]=='EDGE' and int(v[4])==len(edges);edges.append((int(v[5]),int(v[6]),float(v[7])))
   assert receipt['stop'] in [0,2],'Resource limit is unknown, not budget infeasibility'
   if receipt['stop']==2:result=None;known_bounds[net].append((forbidden,math.inf))
   else:
    assert receipt['physical_cost']==receipt['lower_s'];assert edges[0][0]==c['sink'] and edges[-1][1]==len(caps)
    assert all(x[1]==y[0] for x,y in zip(edges,edges[1:])) and len({x[0] for x in edges})==len(edges)
    assert abs(sum(x[2] for x in edges)-receipt['physical_cost'])<1e-23;assert abs(c['anchors'][str(edges[-1][0])]-edges[-1][2])<1e-23
    forward=[edges[-1][0]]+[e[0] for e in reversed(edges[:-1])];weights=[e[2] for e in reversed(edges[:-1])]
    assert set(forward)&fixed[net]=={forward[0]} and not set(forward)&set(c['blocked'])
    result=dict(nodes=fixed[net]|set(forward),cost=receipt['physical_cost'],forward=forward,weights=weights,origin=str(directory));pool[net].append(result);newpaths.append(result);known_bounds[net].append((forbidden,result['cost']))
   write(directory/'result.json',receipt)
 receipts.append(receipt);write(b/'query_receipts.json',receipts);cache[key]=result;return result
t=time.monotonic();result=solve(initial,fixed,caps,offset,query);search_seconds=time.monotonic()-t;paths=result.pop('paths',{})
# Audit new witness edges even for branches excluded by the timing budget.
wanted={(u,v,w) for p in newpaths for u,v,w in zip(p['forward'],p['forward'][1:],p['weights'])};seen={}
if wanted:
 for sec,e in graph_records(graph):
  if sec!='rr_edges':continue
  at=e.attrib;sw=int(at['switch_id']);edge=int(at['src_node']),int(at['sink_node']),switches[sw]
  if edge in wanted:seen[edge]=min(sw,seen.get(edge,sw))
 assert wanted==seen.keys()
write(b/'search.json',result)
if paths:
 owners=collections.defaultdict(list)
 import sys
 sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace
 for net,info in read_trace(source/'routed.route').items():
  for node in {x.inode for x in info['trace']}:owners[node].append(net)
 selected=collections.defaultdict(set)
 for net,path in paths.items():
  for node in path['nodes']:selected[node].add(net)
 conflicts={str(node):dict(capacity=int(caps[node]),other_nets=sorted(set(owners[node])-set(paths)),selected_nets=sorted(nets)) for node,nets in selected.items() if len((set(owners[node])-set(paths))|nets)>caps[node]}
 targets=[dict(net=net,pin=cases[net]['pin'],sink=cases[net]['sink'],suffix_nodes=path['forward'],suffix_weights=path['weights'],physical_seconds=path['cost'],before_physical_seconds=cases[net]['current_physical_seconds'],offset_s=offset[net],proxy_score_s=path['cost']+offset[net]) for net,path in paths.items()]
 write(b/'opportunity.json',dict(status='compatible',input_run=str(source),targets=targets,current_other_net_conflicts=conflicts,near_ns=reg['near_ns'],qualification='All selected critical-cone paths meet strict slack-offset proxy budgets and mutually satisfy RR capacities. Background restoration and native FULL/STA pending.'))
for p in b.rglob('*'):
 if p.is_file():bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=True,status=result['status'],agents=len(initial),expanded=result['expanded'],objective=result.get('objective'),search_seconds=search_seconds,complete_process_seconds=time.monotonic()-start,new_queries=sum(r['kind']=='new_exact_query' for r in receipts),reused_queries=sum(r['kind']!='new_exact_query' for r in receipts),native_calls=0,source_sha256=bindings,
 qualification='Complete selected-tree capacity and strict local proxy budgets; all outside occupancy relaxed. Infeasibility is conditional on these retained trees and budgets, not global routing/STA. A limit is unresolved. Successful paths still need full background restoration and native FULL/STA.'))
if paths:write(b/'candidate_binding.json',dict(passed=True,source_sha256={str(p):sha(p) for p in [b/'opportunity.json',b/'completion.json',b/'registration.json']}))
print(dict(status=result['status'],expanded=result['expanded'],new=sum(r['kind']=='new_exact_query' for r in receipts),reused=sum(r['kind']!='new_exact_query' for r in receipts),seconds=time.monotonic()-start),flush=True)
