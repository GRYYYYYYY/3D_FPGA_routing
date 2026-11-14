#!/usr/bin/env python3
"""Check physical directed edges, seed-prefix transform and independent oracle bounds."""
import argparse,collections,math,resource,signal
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import graph_records,f32
from analyze_search_domain_v2 import inside
ap=argparse.ArgumentParser();ap.add_argument('--batch',default='preferred_query_certificate_offline_03');args=ap.parse_args()
resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
b=D/args.batch;ex=read(b/'execution.json');assert all(sha(p)==h for p,h in ex['source_sha256'].items());assert all(sha(b/n)==h for n,h in ex['output_sha256'].items());assert read(b/'unit_validation.json')['passed']
rows={};paths=collections.defaultdict(list);work={}
for l in (b/'query_stdout.log').read_text().splitlines():
 v=l.split()
 if v[0]=='WORK':
  assert int(v[1]) not in work;work[int(v[1])]=dict(full_crossing_records=int(v[2]),indexed_crossing_records=int(v[3]));continue
 key=(int(v[1]),int(v[2]))
 if v[0]=='RESULT':
  assert key not in rows;opt=lambda x:None if x=='-' else float(x)
  rows[key]=dict(search=key[0],mode=key[1],stop=int(v[3]),expansions=int(v[4]),labels=int(v[5]),peak_heap=int(v[6]),upper_seconds=opt(v[7]),physical_seconds=opt(v[8]),lower_seconds=opt(v[9]),query_seconds=float(v[10]),edges=int(v[11]),seed_floor=float(v[12]),admissible_seeds=int(v[13]))
 else:
  assert v[0]=='EDGE' and int(v[3])==len(paths[key]);paths[key].append((int(v[4]),int(v[5]),float(v[6]),float(v[7])))
cases={int(c['domain']['search']):c for c in read(b/'cases.json')};modes=sorted({k[1] for k in rows});assert len(cases)==10 and len(rows)==len(modes)*10
base=D/'residual_query_offline_01';nreal=read(base/'graph_binding.json')['nodes'];oracle=read(D/'residual_seed_oracle_01/analysis.json');reg=read(D/'residual_seed_oracle_01/registration.json');rm=read(D/'search_domain_eltwise_dev_01/runs/eltwise_layer_T/manifest.json');graph=Path(rm['command'][rm['command'].index('--read_rr_graph')+1]);assert sha(graph)==rm['shared_inputs'][str(graph)]['sha256']
want_nodes=set();want_edges=set()
for c in cases.values():want_nodes.update(s['node'] for s in c['seeds']);want_nodes.add(int(c['domain']['sink']));want_nodes.update(map(int,c['domain']['preferred'].split(',')))
for path in paths.values():
 for u,v,w,t in path:
  assert t==0;want_nodes.add(u)
  if v!=nreal:want_nodes.add(v);want_edges.add((v,u,w))
nodes={};found=set();switch={};total_layers=0;all_layers=[];all_crossings=0;by_source=collections.Counter()
for section,e in graph_records(graph):
 a=e.attrib
 if section=='switches':
  t=e.find('timing');v={} if t is None else t.attrib;assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal']);switch[int(a['id'])]=f32(v.get('Tdel',0))
 elif section=='rr_nodes':
  k=int(a['id']);v=e.find('loc').attrib;layer=int(v.get('layer_low',v.get('layer',0)));total_layers=max(total_layers,layer+1)
  assert k==len(all_layers);all_layers.append(layer)
  if k in want_nodes:nodes[k]=dict(layer=layer,direction=a.get('direction','NONE'),**{n:int(v[n]) for n in ['xlow','xhigh','ylow','yhigh']})
 elif section=='rr_edges':
  item=(int(a['src_node']),int(a['sink_node']),switch[int(a['switch_id'])])
  if all_layers[item[0]]!=all_layers[item[1]]:all_crossings+=1;by_source[item[0]]+=1
  if item in want_edges:found.add(item)
assert want_edges==found and total_layers==2
assert work.keys()==cases.keys()
for key,c in cases.items():
 assert work[key]['full_crossing_records']==all_crossings
 assert work[key]['indexed_crossing_records']==sum(by_source[n] for n in set(map(int,c['domain']['preferred'].split(','))))
assert read(b/'control_reproduction.json')['passed'] and read(b/'index_reproduction.json')['passed']
near=lambda x,y:x==y or math.isclose(x,y,rel_tol=1e-11,abs_tol=1e-24)
reuse={r['search']:r for r in read(D/'residual_path_reuse_offline_01/analysis.json')['rows']}
for key,r in sorted(rows.items()):
 c=cases[r['search']];dom=c['domain'];sink=int(dom['sink']);sl=nodes[sink]['layer'];preferred=set(map(int,dom['preferred'].split(',')));seeds={}
 for s in c['seeds']:
  assert nodes[s['node']]['layer']==s['layer']
  if s['layer']!=sl and inside(nodes[s['node']],dom,total_layers):seeds[s['node']]=min(seeds.get(s['node'],math.inf),s['delay'])
 floor=min(seeds.values(),default=0.) if r['mode']==2 else 0.;assert floor==r['seed_floor'] and len(seeds)==r['admissible_seeds']
 path=paths[key];assert len(path)==r['edges'];upper=r['upper_seconds'];lower=r['lower_seconds'];opt=c['oracle']['preferred_one_cross_BB_seconds'];assert opt is not None
 assert r['expansions']<=256 and r['labels']<=16384 and r['peak_heap']<=65536
 if upper is not None:
  assert path and upper+1e-24>=opt and near(upper,r['physical_seconds']);assert path[0][0]==sink and path[-1][1]==nreal and path[-1][0] in seeds
  assert len({e[0] for e in path})==len(path) and all(a[1]==z[0] for a,z in zip(path,path[1:]));assert near(path[-1][2]+floor,seeds[path[-1][0]])
  crosses=[]
  for u,v,w,t in path[:-1]:
   assert (v,u,w) in found and inside(nodes[u],dom,total_layers) and inside(nodes[v],dom,total_layers)
   if nodes[u]['layer']!=nodes[v]['layer']:assert nodes[u]['layer']==sl and v in preferred;crosses.append((v,u))
  assert len(crosses)==1 and near(sum(e[2] for e in path)+floor,upper)
 else:assert not path
 if lower is not None:assert lower<=opt+1e-24
 if r['stop']==0:assert upper is not None and near(upper,opt) and near(lower,opt)
 if r['stop']==2:assert False,'All original physical preferred minima are finite'
 witness=reuse[r['search']]['S'];assert witness is None or isinstance(witness,dict);ub=None if witness is None else witness['seconds'];r.update(oracle_seconds=opt,criticality=c['oracle']['criticality'],cached_no_cross_upper_seconds=ub,no_cross_oracle_seconds=c['oracle']['no_cross_BB_seconds'],strict_no_cross_dominance_certificate=ub is not None and lower is not None and ub+1e-24<lower,relative_upper_gap=upper/opt-1 if upper is not None else None)
summary={}
for mode in modes:
 rs=[r for r in rows.values() if r['mode']==mode];summary[mode]=dict(queries=len(rs),paths=sum(r['upper_seconds'] is not None for r in rs),exact=sum(r['stop']==0 for r in rs),certified_no_cross_better=sum(r['strict_no_cross_dominance_certificate'] for r in rs),positive_prefix_floor=sum(r['seed_floor']>0 for r in rs),expansions=sum(r['expansions'] for r in rs),query_seconds=sum(r['query_seconds'] for r in rs),stop_counts=dict(collections.Counter(r['stop'] for r in rs)),max_upper_gap=max((r['relative_upper_gap'] for r in rs if r['relative_upper_gap'] is not None),default=None))
source={str(p):sha(p) for p in [Path(__file__),b/'registration.json',b/'execution.json',b/'unit_validation.json',b/'query_stdout.log',graph,D/'residual_seed_oracle_01/analysis.json',D/'residual_path_reuse_offline_01/analysis.json']}
assert all(sha(p)==h for p,h in ex['source_sha256'].items());write(b/'analysis.json',dict(passed=True,native_route_calls=0,source_sha256=source,summaries=summary,rows=list(rows.values()),crossing_lookup_work=work,real_directed_edges_checked=len(found),qualification='All10guided cases from31complete focus seed groups on one seen circuit. Actual zero-RC directed RRG edges/single preferred crossing/nativeBB/actualseedprefix checked; bounds compared with independent full oracle. No arbitrary multi-cross/native congestion optimality or legal route-tree-extension guarantee. Common prefix floor has no observed effect if zero; unit validation does not establish practical gain. Query costs exclude graph loading and offline audit; no formal online speedup or QoR result.'))
print(dict(summaries=summary,crossing_lookup_work=work))
