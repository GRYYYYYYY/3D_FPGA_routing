#!/usr/bin/env python3
"""Test a source-entry capacity cut after removing every retained-branch restriction.

Also query the remaining serial worst-path connections from their physical
sources, to distinguish retained-tree loss from fixed-terminal path distance.
"""
import argparse,array,collections,itertools,resource,signal,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_frontier_queries import write_cases
from verify_path_witnesses_v2 import graph_records,f32

p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--serial-reference',type=Path,required=True);p.add_argument('--batch',type=Path,required=True);a=p.parse_args()
started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800);ref=a.reference.resolve();serial=a.serial_reference.resolve();b=a.batch.resolve();b.mkdir(exist_ok=False)
complete=read(ref/'completion.json');assert complete['passed'] and all(sha(p)==h for p,h in complete['source_sha256'].items());reg=read(ref/'registration.json');source=Path(reg['input_run']);m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);driver=D/'current_sta_queries_01/critical_capacity_driver';binary=D/'residual_query_offline_01/graph.bin'
caps=array.array('I');kinds=[];switches={};metadata={}
for section,e in graph_records(graph):
 if section=='switches':t=e.find('timing');switches[int(e.attrib['id'])]=0 if t is None else f32(t.attrib.get('Tdel',0))
 elif section=='rr_nodes':assert int(e.attrib['id'])==len(caps);caps.append(int(e.attrib['capacity']));kinds.append(e.attrib['type'])
 else:break
cases={c['net']:c for c in read(ref/'original_cases.json')};offset={int(n):v for n,v in read(ref/'matching.json')['offsets_s'].items()};entry=collections.defaultdict(set)
for o in read(ref/'options.json'):
 net=o['net']
 if o['cost_s']+offset[net]>=0:continue
 c=cases[net];parents={v:u for u,v,sw,w in c['tree_edges']};prefix=[o['forward'][0]]
 while prefix[-1]!=c['root']:prefix.append(parents[prefix[-1]])
 full=list(reversed(prefix))[:-1]+o['forward'];channel=next(node for node in full if kinds[node] in ['CHANX','CHANY']);entry[net].add(channel)
candidates=[]
for k in range(2,len(cases)+1):
 for agents in itertools.combinations(sorted(cases),k):
  cut=set().union(*(entry[n] for n in agents));capacity=sum(caps[node] for node in cut)
  if cut and capacity<k:candidates.append((capacity,k,tuple(sorted(cut)),agents))
assert candidates,'Known paths do not expose a source-entry capacity deficit'
capacity,_,cut,agents=min(candidates);cut=set(cut);zero={n for n,c in enumerate(caps) if c==0};queries=[];roles={}
for net in agents:
 c=cases[net];queries.append(dict(c,retained=[c['root']],anchors={str(c['root']):0.},blocked=sorted(zero|cut)));roles[net]=dict(kind='source_entry_cut',pin=c['pin'],current_s=c['current_physical_seconds'],offset_s=offset[net])
sa=read(serial/'analysis.json');assert sa['passed'] and all(sha(p)==h for p,h in sa['source_sha256'].items())
assert read(serial/'execution_registration.json')['input_run']==str(source)
for c in read(serial/'cases.json'):
 if c['net'] in cases:continue
 queries.append(dict(c,retained=[c['root']],anchors={str(c['root']):0.},blocked=sorted(zero)));roles[c['net']]=dict(kind='serial_root_only',pin=c['pin'],current_s=c['current_physical_seconds'])
files=[Path(__file__),ref/'completion.json',ref/'options.json',ref/'original_cases.json',ref/'matching.json',serial/'analysis.json',serial/'cases.json',source/'native_sta_frontier.jsonl',graph,driver,binary];bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(status='registered_before_query',question='Does the source-entry budget cut persist even with source-only anchors, and do other current worst-path connections have any root-only physical delay potential?',cut_nodes=sorted(cut),cut_capacity=capacity,cut_agents=list(agents),known_entry_sets={n:sorted(s) for n,s in entry.items()},query_roles=roles,
 domain='For every query only the physical SOURCE is retained, with zero prefix cost. All other network occupancy and all existing branches are relaxed. Candidate cut channels are forbidden only for source-entry queries.',
 limits=dict(query_seconds=240,memory_bytes=24*1024**3),source_sha256=bindings,native_calls=0))
write_cases(b/'cases.txt',queries);t=time.monotonic()
with (b/'stdout.log').open('w') as out,(b/'stderr.log').open('w') as err:proc=subprocess.run([str(driver),str(binary),str(b/'cases.txt'),'capacity'],stdout=out,stderr=err,timeout=240)
query_seconds=time.monotonic()-t;assert proc.returncode==0;rows={};paths=collections.defaultdict(list)
for line in (b/'stdout.log').open():
 v=line.split();net=int(v[1]);assert net in roles and int(v[2])==roles[net]['pin'] and int(v[3])==1
 if v[0]=='RESULT':rows[net]=dict(net=net,**roles[net],stop=int(v[4]),cost_s=float(v[8]),lower_s=float(v[9]),core_seconds=float(v[10]))
 else:assert v[0]=='EDGE' and int(v[4])==len(paths[net]);paths[net].append((int(v[5]),int(v[6]),float(v[7])))
assert rows.keys()==roles.keys();by_net={c['net']:c for c in queries};wanted=set()
for net,r in rows.items():
 assert r['stop'] in [0,2];path=paths[net];c=by_net[net]
 if r['stop']==0:
  assert r['cost_s']==r['lower_s'] and path[0][0]==c['sink'] and path[-1][1]==len(caps) and path[-1][0]==c['root'] and path[-1][2]==0
  assert all(x[1]==y[0] for x,y in zip(path,path[1:])) and len({x[0] for x in path})==len(path)
  assert abs(sum(x[2] for x in path)-r['cost_s'])<1e-23 and not {x[0] for x in path}&set(c['blocked']);wanted.update((v,u,w) for u,v,w in path[:-1])
  r['physical_gain_s']=r['current_s']-r['cost_s']
  if r['kind']=='source_entry_cut':r['strict_proxy_possible_avoiding_cut']=r['cost_s']+r['offset_s']<0
 else:
  assert r['kind']=='source_entry_cut';r['strict_proxy_possible_avoiding_cut']=False
seen=set()
for section,e in graph_records(graph):
 at=e.attrib
 if section=='rr_nodes' and int(at['id']) in cut:metadata[int(at['id'])]=dict(attributes=dict(at),location=dict(e.find('loc').attrib))
 elif section=='rr_edges':
  edge=int(at['src_node']),int(at['sink_node']),switches[int(at['switch_id'])]
  if edge in wanted:seen.add(edge)
assert wanted==seen
certified=all(not rows[n]['strict_proxy_possible_avoiding_cut'] for n in agents)
for p in b.iterdir():
 if p.is_file():bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=True,source_only_cut_certified=certified,cut_nodes=sorted(cut),cut_metadata=metadata,cut_capacity=capacity,cut_agents=list(agents),queries=list(rows.values()),query_process_seconds=query_seconds,complete_process_seconds=time.monotonic()-started,source_sha256=bindings,native_calls=0,
 qualification='Source-only optimistic zero-RC reference at fixed physical source/sink mapping. A certified cut rules out simultaneous strict slack-offset input-cone improvement even after changing all retained branches; serial source-only distances assess a separate potential. Not a full-design native STA optimality certificate, and not a result after placement/packing/pin mapping changes. Any feasible alternative from a failed certificate requires follow-up.'))
print(dict(certified=certified,agents=list(agents),cut=sorted(cut),capacity=capacity,queries=[(r['net'],r['kind'],r.get('physical_gain_s'),r.get('strict_proxy_possible_avoiding_cut')) for r in rows.values()],seconds=time.monotonic()-started),flush=True)
