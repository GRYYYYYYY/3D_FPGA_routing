#!/usr/bin/env python3
"""Exact optimistic SOURCE-only distances for the newly identified dominant cone."""
import argparse,collections,resource,shutil,subprocess,sys,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from immutable_rr_audit_cache import GraphAuditCache
from coordinated_repair_tree import from_trace,prefixes
from run_native_frontier_queries import write_cases
sys.path.insert(0,str(D.parents[1]/'scripts'))
from check_route import read_trace

parser=argparse.ArgumentParser();parser.add_argument('--cone',type=Path,required=True);parser.add_argument('--batch',type=Path,required=True);parser.add_argument('--reuse',type=Path,nargs='*',default=[]);args=parser.parse_args()
start=time.monotonic();b=args.batch.resolve();b.mkdir(exist_ok=False);resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));assert shutil.disk_usage(D).free>=80*1024**3
cone=read(args.cone);assert cone['passed'] and not cone['unresolved_non_source_nodes']
state=Path(cone['source_state']);run=Path(read(state/'completion.json')['run']);m=read(run/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
cache=GraphAuditCache(graph,D/'rr_audit_cache_e695_dev_01');binary=D/'residual_query_offline_01/graph.bin';binding=read(binary.with_name('graph_binding.json'));driver=D/'current_sta_queries_01/critical_capacity_driver'
assert sha(binary)==binding['binary_graph_sha256'] and cache.receipt['graph_sha256']==binding['source_rrg_sha256']
traces=read_trace(run/'routed.route');blocked=np.flatnonzero(cache.capacities==0).tolist();cases=[]
for p in cone['routed_connections']:
 tree=from_trace(traces[p['net']]['trace'],cache.switches);sink=tree['sinks'][p['pin']];cost=prefixes(tree)[sink]
 cases.append(dict(net=p['net'],pin=p['pin'],root=tree['root'],sink=sink,retained=[tree['root']],anchors={str(tree['root']):0.},blocked=blocked,current_physical_seconds=cost))
files=[Path(__file__).resolve(),args.cone.resolve(),D/'immutable_rr_audit_cache.py',D/'rr_audit_cache_e695_dev_01/completion.json',state/'completion.json',run/'routed.route',graph,binary,binary.with_name('graph_binding.json'),driver]
reuse_rows={};reused_logs=[];receipts=[]
for prior in args.reuse:
 prior=prior.resolve();proof=read(prior/'completion.json');assert proof['passed']
 assert all(sha(p)==h for p,h in proof['source_sha256'].items())
 prior_cases={(c['net'],c['pin']):c for c in read(prior/'cases.json')}
 for c in cases:
  key=(c['net'],c['pin'])
  if prior_cases.get(key)==c:
   assert key not in reuse_rows
   reuse_rows[key]=next(r for r in proof['queries'] if (r['net'],r['pin'])==key)
 if any((c['net'],c['pin']) in reuse_rows for c in cases):
  reused_logs.append(prior/'stdout.log');files.extend([prior/'completion.json',prior/'cases.json',prior/'stdout.log'])
  receipts.append(dict(source=str(prior),complete_process_seconds=proof['complete_process_seconds'],qualification='Exact complete case including current physical distance, retained root, sink, anchors and blocked set. Actual graph/binary/driver identities also checked. Historical cost excluded.'))
  for required in [graph,binary,binary.with_name('graph_binding.json'),driver]:assert proof['source_sha256'][str(required)]==sha(required)
new_cases=[c for c in cases if (c['net'],c['pin']) not in reuse_rows]
bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(status='registered_before_queries',question='Can any routed connection on the automatically selected current endpoint maximum-arrival cone improve even after all retained branches and background occupancy are relaxed?',input_run=str(run),targets=[(c['net'],c['pin']) for c in cases],source_sha256=bindings,limits=dict(query_seconds=240,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3),qualification='Fixed physical SOURCE/SINK, zeroRC, full-device optimistic distances. No claim of native legal replacement or globalSTA optimum.',native_calls=0))
write(b/'cases.json',cases);write(b/'reuse_receipts.json',receipts);write_cases(b/'cases.txt',new_cases);t=time.monotonic()
with (b/'stdout.log').open('w') as out,(b/'stderr.log').open('w') as err:proc=subprocess.run([str(driver),str(binary),str(b/'cases.txt'),'capacity'],stdout=out,stderr=err,timeout=240)
query_seconds=time.monotonic()-t;assert proc.returncode==0;rows={};paths=collections.defaultdict(list);case_by_key={(c['net'],c['pin']):c for c in cases}
for line in ''.join(p.read_text() for p in [b/'stdout.log',*reused_logs]).splitlines():
 v=line.split();key=int(v[1]),int(v[2]);
 if key not in case_by_key:continue
 assert int(v[3])==1
 if v[0]=='RESULT':rows[key]=dict(net=key[0],pin=key[1],stop=int(v[4]),cost_s=float(v[8]),lower_s=float(v[9]),core_seconds=float(v[10]))
 else:assert v[0]=='EDGE' and int(v[4])==len(paths[key]);paths[key].append((int(v[5]),int(v[6]),float(v[7])))
assert rows.keys()==case_by_key.keys();checked=0
for key,r in rows.items():
 c=case_by_key[key];path=paths[key];assert r['stop']==0 and r['cost_s']==r['lower_s']
 assert path[0][0]==c['sink'] and path[-1]==(c['root'],cache.n,0.)
 assert all(a[1]==z[0] for a,z in zip(path,path[1:])) and len({x[0] for x in path})==len(path)
 assert not {x[0] for x in path}&set(blocked) and abs(sum(x[2] for x in path)-r['cost_s'])<1e-23
 for dest,src,weight in path[:-1]:
  lo=np.uint64((src*cache.n+dest)*cache.stride);hi=lo+np.uint64(cache.stride)
  begin,end=np.searchsorted(cache.edges,[lo,hi]);available=[int(e)%cache.stride for e in cache.edges[begin:end]]
  assert any(cache.switches[s]==weight for s in available),(src,dest,weight)
  checked+=1
 r['current_physical_s']=c['current_physical_seconds'];r['optimistic_gain_s']=c['current_physical_seconds']-r['cost_s']
 assert r['optimistic_gain_s']>=0
for p in b.iterdir():
 if p.is_file():bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
write(b/'completion.json',dict(passed=True,queries=list(rows.values()),actual_XML_bound_edges_checked=checked,cache_receipt=cache.receipt,query_process_seconds=query_seconds,complete_process_seconds=time.monotonic()-start,source_sha256=bindings,new_queries=len(new_cases),reused_queries=len(reuse_rows),native_calls=0,qualification='Exact fixed-terminal SOURCE-only physical-distance reference on the identified current maximum-arrival cone. Positive gain still needs capacity/tree recovery and nativeFULLSTA; zero gain does not prove complete design optimality or exclude pin/placement/clock/logic changes.'))
print(dict(queries=[(r['net'],r['pin'],r['optimistic_gain_s']) for r in rows.values()],seconds=time.monotonic()-start),flush=True)
