#!/usr/bin/env python3
"""Separate a retained-tree conditional floor from a source-only path relaxation."""
import collections,copy,math,resource,shutil,signal,subprocess,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha as raw_sha
from immutable_rr_audit_cache import GraphAuditCache
from run_native_frontier_queries import write_cases
b=D/'current_root_prefix_potential_01';b.mkdir(exist_ok=False);started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800);assert shutil.disk_usage(D).free>=80*1024**3;cachehash={}
def sha(p):
 p=Path(p).resolve();s=p.stat();key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 if key not in cachehash:cachehash[key]=raw_sha(p)
 return cachehash[key]
f=D/'portfolio_execution_dev_01/R1_strict/round_002/feedback';old=f/'relaxed';ex=read(old/'execution.json');an=read(old/'analysis.json');assert an['passed'];assert all(sha(p)==h for p,h in ex['source_sha256'].items());assert all(sha(old/n)==h for n,h in ex['output_sha256'].items());assert all(sha(p)==h for p,h in an['source_sha256'].items());cone=read(f/'cone.json');state=Path(cone['source_state']);source=Path(read(state/'completion.json')['run']);m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);g=GraphAuditCache(graph,D/'rr_audit_cache_bnn_01');binary=next(Path(p) for p in ex['source_sha256'] if p.endswith('/graph.bin'));driver=D/'current_sta_relaxed_01/critical_capacity_driver';binding=read(binary.with_name('graph_binding.json'));assert binding['source_rrg_sha256']==g.receipt['graph_sha256'] and sha(binary)==binding['binary_graph_sha256'];assert ex['source_sha256'][str(driver)]==sha(driver)
base=read(old/'cases.json');oldanswers={(r['net'],r['pin']):r for r in an['results']};missing=[];roots={};answers={};reused=[]
for c in base:
 assert oldanswers[c['net'],c['pin']]['improvement_ns']==0 and oldanswers[c['net'],c['pin']]['stop']==0
 root=copy.deepcopy(c);root.update(retained=[c['root']],anchors={str(c['root']):0.},blocked=[]);roots[c['net'],c['pin']]=root
 if c['retained']==[c['root']] and c['anchors']==root['anchors']:
  r=oldanswers[c['net'],c['pin']];answers[c['net'],c['pin']]=dict(distance_s=r['physical_seconds'],lower_s=r['lower_seconds'],suffix_nodes=r['suffix_nodes'],suffix_switches=r['suffix_switches'],reused=True);reused.append([c['net'],c['pin']])
 else:missing.append(root)
files=[Path(__file__).resolve(),old/'analysis.json',old/'execution.json',old/'cases.json',f/'cone.json',state/'completion.json',state/'endpoint_vector.json',source/'routed.route',binary,binary.with_name('graph_binding.json'),driver,D/'rr_audit_cache_bnn_01/completion.json'];bound={str(p):sha(p) for p in files};write(b/'registration.json',dict(status='before_new_relaxation_query',input_state=str(state),source_sha256=bound,question='The current winning path has zero relaxed retained-tree gain: is this caused by frozen common prefixes, or do independent source-only paths also have no useful timing gap?',new_root_queries=len(missing),reused_root_queries=reused,native_calls=0,route_calls=0,limits=dict(query_seconds=900,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3),qualification='Source-only zero-RC directed path relaxation, independent connections without other-sink restoration or occupancy. This is not a jointly feasible routing reference, whole-CPD bound or algorithm result. Root-only old cases are reused; no old retained-anchor query repeated.'))
write(b/'cases.json',missing);write_cases(b/'cases.txt',missing);t=time.monotonic()
with (b/'query_stdout.log').open('w') as out,(b/'query_stderr.log').open('w') as err:r=subprocess.run([str(driver),str(binary),str(b/'cases.txt')],stdout=out,stderr=err,timeout=900)
elapsed=time.monotonic()-t;assert r.returncode==0;raw={};paths=collections.defaultdict(list)
for line in (b/'query_stdout.log').open():
 v=line.split();key=int(v[1]),int(v[2]);assert int(v[3])==0
 if v[0]=='RESULT':raw[key]=dict(stop=int(v[4]),distance_s=float(v[8]),lower_s=float(v[9]),query_seconds=float(v[10]))
 else:assert v[0]=='EDGE' and int(v[4])==len(paths[key]);paths[key].append((int(v[5]),int(v[6]),float(v[7])))
assert len(raw)==len(missing)
for key,r in raw.items():
 assert r['stop']==0 and r['distance_s']==r['lower_s'];edges=paths[key];c=roots[key];assert edges[0][0]==c['sink'] and edges[-1][0]==c['root'] and edges[-1][1]==g.n and edges[-1][2]==0.;assert all(x[1]==y[0] for x,y in zip(edges,edges[1:]));assert len({e[0] for e in edges})==len(edges);assert abs(sum(e[2] for e in edges)-r['distance_s'])<1e-23;switches=[]
 for dest,src,w in reversed(edges[:-1]):
  lo=np.uint64((src*g.n+dest)*g.stride);i,j=np.searchsorted(g.edges,[lo,lo+np.uint64(g.stride)]);choices=[int(x)%g.stride for x in g.edges[i:j] if g.switches[int(x)%g.stride]==w];assert choices;switches.append(min(choices))
 answers[key]=dict(distance_s=r['distance_s'],lower_s=r['lower_s'],suffix_nodes=[c['root']]+[e[0] for e in reversed(edges[:-1])],suffix_switches=switches,reused=False,query_seconds=r['query_seconds'])
rows=[]
for c in base:
 key=c['net'],c['pin'];r=answers[key];g.require_edges(zip(r['suffix_nodes'],r['suffix_nodes'][1:],r['suffix_switches']));assert abs(sum(g.switches[s] for s in r['suffix_switches'])-r['distance_s'])<1e-23;prior=oldanswers[key];gain=(c['current_physical_seconds']-r['distance_s'])*1e12;assert gain>=-1e-9
 rows.append(dict(net=key[0],pin=key[1],current_physical_s=c['current_physical_seconds'],retained_tree_relaxed_s=prior['physical_seconds'],source_only_relaxed_s=r['distance_s'],optimistic_gain_ps=gain,old_retained_nodes=len(c['retained']),other_sink_pins=c['other_sinks'],zero_capacity_nodes=[n for n in r['suffix_nodes'] if g.capacities[n]==0],**r))
write(b/'rows.json',rows);assert all(sha(p)==h for p,h in bound.items());write(b/'completion.json',dict(passed=True,input_state=str(state),connections=len(rows),new_queries=len(missing),reused_queries=len(reused),positive_source_only_gap_connections=sum(r['optimistic_gain_ps']>1e-9 for r in rows),sum_independent_optimistic_gain_ps=sum(r['optimistic_gain_ps'] for r in rows),query_process_seconds=elapsed,complete_offline_workflow_seconds=time.monotonic()-started,native_calls=0,route_calls=0,source_sha256=bound,artifact_sha256={n:sha(b/n) for n in ['cases.json','cases.txt','query_stdout.log','query_stderr.log','rows.json']},qualification='Independent path relaxation only. Sum is not a realizable CPD gain, global bound, joint feasibility claim or proof that FPGA routing is optimal. Native float32 STA, intracluster timing/pin synchronization, other endpoints, capacity competition, and restoring other sinks remain outside this reference. Zero-capacity usage explicitly reported; positive gap would motivate whole-net/private-prefix rebuilding with full native validation.'))
print([(r['net'],r['pin'],r['optimistic_gain_ps'],len(r['zero_capacity_nodes'])) for r in rows],flush=True)
