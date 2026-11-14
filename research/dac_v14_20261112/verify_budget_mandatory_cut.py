#!/usr/bin/env python3
"""Check whether a finite-pool mandatory resource remains mandatory in the full RR graph."""
import argparse,array,collections,math,resource,signal,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_frontier_queries import write_cases
from verify_path_witnesses_v2 import graph_records,f32

p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--pool-search',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);a=p.parse_args()
started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800);ref=a.reference.resolve();pool=a.pool_search.resolve();b=a.batch.resolve();b.mkdir(exist_ok=False)
for root in [ref,pool]:
 c=read(root/'completion.json');assert c['passed'] and all(sha(p)==h for p,h in c['source_sha256'].items())
reg=read(ref/'registration.json');source=Path(reg['input_run']);m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);cut=read(pool/'search.json')['mandatory_cuts'][0]['resource']
driver=D/'current_sta_queries_01/critical_capacity_driver';binary=D/'residual_query_offline_01/graph.bin';files=[Path(__file__),ref/'completion.json',ref/'original_cases.json',ref/'options.json',ref/'matching.json',pool/'completion.json',pool/'search.json',graph,driver,binary];bindings={str(p):sha(p) for p in files}
caps=array.array('I');switches={};node_metadata={}
for section,e in graph_records(graph):
 if section=='switches':t=e.find('timing');switches[int(e.attrib['id'])]=0 if t is None else f32(t.attrib.get('Tdel',0))
 elif section=='rr_nodes':
  n=int(e.attrib['id']);assert n==len(caps);caps.append(int(e.attrib['capacity']))
  if n==cut:node_metadata=dict(attributes=dict(e.attrib),location=dict(e.find('loc').attrib))
 else:break
cases={c['net']:c for c in read(ref/'original_cases.json')};fixed={n:set(c['retained']) for n,c in cases.items()};owners=collections.defaultdict(set)
for n,nodes in fixed.items():
 for node in nodes:owners[node].add(n)
offset={int(n):v for n,v in read(ref/'matching.json')['offsets_s'].items()};eligible=collections.defaultdict(list)
for o in read(ref/'options.json'):
 n=o['net'];extra=set(o['forward'])-fixed[n]
 if o['cost_s']+offset[n]<0 and all(len(owners[node])<caps[node] for node in extra):eligible[n].append(o)
mandatory=[n for n,paths in eligible.items() if paths and all(cut in set(p['forward'])-fixed[n] for p in paths)]
assert len(mandatory)>caps[cut]-len(owners[cut]);zero={n for n,c in enumerate(caps) if c==0};queries=[];domains={}
for net in sorted(mandatory):
 blocked=zero|{cut}|{node for node,ns in owners.items() if len(ns-{net})>=caps[node]};assert not blocked&fixed[net]
 queries.append(dict(cases[net],blocked=sorted(blocked)));domains[net]=dict(forbidden=sorted(blocked),other_fixed_owner_nodes={str(node):sorted(ns-{net}) for node,ns in owners.items() if len(ns-{net})>=caps[node]})
write(b/'registration.json',dict(status='registered_before_full_graph_queries',question='Does the finite-pool mandatory cut exclude all strict-budget paths after exact full-device query, or were unobserved alternatives omitted?',cut_node=cut,cut_metadata=node_metadata,agents=mandatory,offsets_s=offset,
 domain='Only the six selected nets other retained branches are immutable; all other network occupancy relaxed. Ban the candidate cut node and capacity-saturated other-selected retained resources.',source_sha256=bindings,limits=dict(query_seconds=240,memory_bytes=24*1024**3),native_calls=0))
write(b/'query_domains.json',domains);write_cases(b/'cases.txt',queries);t=time.monotonic()
with (b/'stdout.log').open('w') as out,(b/'stderr.log').open('w') as err:proc=subprocess.run([str(driver),str(binary),str(b/'cases.txt'),'capacity'],stdout=out,stderr=err,timeout=240)
query_seconds=time.monotonic()-t;assert proc.returncode==0;rows={};edges=collections.defaultdict(list)
for line in (b/'stdout.log').open():
 v=line.split();net=int(v[1]);assert net in mandatory and int(v[2])==cases[net]['pin'] and int(v[3])==1
 if v[0]=='RESULT':rows[net]=dict(net=net,pin=cases[net]['pin'],stop=int(v[4]),cost_s=float(v[8]),lower_s=float(v[9]),core_seconds=float(v[10]))
 else:assert v[0]=='EDGE' and int(v[4])==len(edges[net]);edges[net].append((int(v[5]),int(v[6]),float(v[7])))
assert rows.keys()==set(mandatory);wanted=set()
for net,r in rows.items():
 assert r['stop'] in [0,2];path=edges[net]
 if r['stop']==0:
  assert r['cost_s']==r['lower_s'] and path[0][0]==cases[net]['sink'] and path[-1][1]==len(caps)
  assert all(x[1]==y[0] for x,y in zip(path,path[1:])) and len({x[0] for x in path})==len(path)
  assert abs(sum(x[2] for x in path)-r['cost_s'])<1e-23 and not {x[0] for x in path}&set(domains[net]['forbidden'])
  assert all(x[0] not in fixed[net] for x in path[:-1]);assert abs(cases[net]['anchors'][str(path[-1][0])]-path[-1][2])<1e-23
  wanted.update((v,u,w) for u,v,w in path[:-1]);r['proxy_score_s']=r['cost_s']+offset[net];r['strict_budget_possible_avoiding_cut']=r['proxy_score_s']<0
 else:r['strict_budget_possible_avoiding_cut']=False
seen=set()
for section,e in graph_records(graph):
 if section=='rr_edges':
  at=e.attrib;edge=int(at['src_node']),int(at['sink_node']),switches[int(at['switch_id'])]
  if edge in wanted:seen.add(edge)
assert seen==wanted
certified=not any(r['strict_budget_possible_avoiding_cut'] for r in rows.values())
for p in b.iterdir():
 if p.is_file():bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=True,conditional_cut_certified=certified,cut_node=cut,metadata=node_metadata,agents=mandatory,capacity=int(caps[cut]),existing_fixed_owners=sorted(owners[cut]),queries=list(rows.values()),query_process_seconds=query_seconds,complete_process_seconds=time.monotonic()-started,source_sha256=bindings,native_calls=0,
 qualification='Exact local strict slack-offset budget certificate under these six retained trees, if certified. It does not establish global CPD optimality or infeasibility after changing retained branches or target scope. If not certified, new graph alternatives invalidate the finite-pool inference and must be explored.'))
print(dict(certified=certified,cut=cut,rows=list(rows.values()),seconds=time.monotonic()-started),flush=True)
