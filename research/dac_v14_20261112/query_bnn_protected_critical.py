#!/usr/bin/env python3
"""Seek capacity-relaxed witnesses while preserving current critical nets."""
import collections,copy,resource,shutil,signal,subprocess,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from immutable_rr_audit_cache import GraphAuditCache
from current_sta_selector import select
from run_native_frontier_queries import write_cases

start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800)
b=D/'bnn_slack_release_screen_01/protected_critical';b.mkdir(exist_ok=False);assert shutil.disk_usage(D).free>=80*1024**3
q=D/'bnn_slack_release_screen_01/Tf_capacity';op=read(D/'bnn_slack_release_screen_01/owner_slack/completion.json');assert op['passed']
proof=read(q/'analysis.json');ex=read(q/'execution.json');assert proof['passed']
assert all(sha(p)==h for p,h in proof['source_sha256'].items())
assert sha(q/'occupancy_owners.json')==ex['output_sha256']['occupancy_owners.json']
source=Path(read(q/'execution_registration.json')['input_run']);m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
g=GraphAuditCache(graph,D/'rr_audit_cache_bnn_01');binary=D/'bnn_physical_query_graph_01/graph.bin';binding=read(binary.with_name('graph_binding.json'));driver=D/'current_sta_queries_01/critical_capacity_driver'
assert sha(binary)==binding['binary_graph_sha256'] and g.receipt['graph_sha256']==binding['source_rrg_sha256']
critical=select(source/'native_sta_frontier.jsonl');protected={r['net'] for r in critical['targets']}
owners={int(k):v for k,v in read(q/'occupancy_owners.json').items()};protected_counts={n:len(set(nets)&protected) for n,nets in owners.items() if set(nets)&protected}
zero=set(map(int,np.flatnonzero(g.capacities==0)));targets={tuple(r['target']) for r in op['rows']};cases=[]
for old in read(q/'cases.json'):
 if (old['net'],old['pin']) not in targets:continue
 c=copy.deepcopy(old);owned=set(c['original_nodes']);c['blocked']=sorted(zero|{n for n,count in protected_counts.items() if count-int(c['net'] in protected and n in owned)>=g.capacities[n]})
 assert not set(c['retained'])&set(c['blocked']);cases.append(c)
files=[Path(__file__).resolve(),D/'current_sta_selector.py',q/'analysis.json',q/'execution.json',q/'occupancy_owners.json',q/'cases.json',D/'bnn_slack_release_screen_01/owner_slack/completion.json',source/'native_sta_frontier.jsonl',D/'rr_audit_cache_bnn_01/completion.json',binary,binary.with_name('graph_binding.json'),driver]
bound={str(p):sha(p) for p in files}
write(b/'registration.json',dict(status='registered_before_query',input_run=str(source),protected_nets=sorted(protected),selector=critical,
 question='Can an equal or shorter useful target witness avoid displacing any currently critical net, rather than treating the first relaxed path as mandatory?',
 domain='Preserve complete current trees of every near-tied current critical net; retain each target other branches. Relax noncritical background occupancy only. This is an optimistic screening problem, not a complete replacement.',
 source_sha256=bound,native_calls=0,limits=dict(query_seconds=900,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3)))
write(b/'cases.json',cases);write_cases(b/'cases.txt',cases);t=time.monotonic()
with (b/'stdout.log').open('w') as out,(b/'stderr.log').open('w') as err:r=subprocess.run([str(driver),str(binary),str(b/'cases.txt'),'capacity'],stdout=out,stderr=err,timeout=900)
query_seconds=time.monotonic()-t;assert r.returncode==0
answers={};paths=collections.defaultdict(list)
for line in (b/'stdout.log').open():
 v=line.split();key=int(v[1]),int(v[2]);assert int(v[3])==1
 if v[0]=='RESULT':answers[key]=dict(stop=int(v[4]),distance_s=float(v[8]),lower_s=float(v[9]),query_seconds=float(v[10]))
 else:assert v[0]=='EDGE' and int(v[4])==len(paths[key]);paths[key].append((int(v[5]),int(v[6]),float(v[7])))
rows=[];checked=0
for c in cases:
 key=c['net'],c['pin'];r=answers[key];path=paths[key];assert r['stop']==0 and r['distance_s']==r['lower_s']
 assert path[0][0]==c['sink'] and path[-1][1]==g.n
 assert all(a[1]==z[0] for a,z in zip(path,path[1:])) and len({x[0] for x in path})==len(path)
 assert not {x[0] for x in path[:-1]}&set(c['retained']) and not {x[0] for x in path}&set(c['blocked'])
 assert str(path[-1][0]) in c['anchors'] and path[-1][2]==c['anchors'][str(path[-1][0])]
 assert abs(sum(x[2] for x in path)-r['distance_s'])<1e-23
 switches=[]
 for dest,src,w in reversed(path[:-1]):
  lo=np.uint64((src*g.n+dest)*g.stride);hi=lo+np.uint64(g.stride);i,j=np.searchsorted(g.edges,[lo,hi]);choices=[int(x)%g.stride for x in g.edges[i:j] if g.switches[int(x)%g.stride]==w];assert choices
  switches.append(min(choices));checked+=1
 conflicts=[]
 for node in set(c['retained'])|{x[0] for x in path}:
  other=[n for n in owners.get(node,[]) if n!=c['net']];need=len(other)+1-int(g.capacities[node])
  if need<=0:continue
  allowed=sorted(n for n in other if n not in protected);assert len(allowed)>=need
  conflicts.append(dict(node=node,capacity=int(g.capacities[node]),other_nets=other,protected_owners=sorted(set(other)&protected),required_releases=need,releasable_noncritical_owners=allowed))
 rows.append(dict(target=list(key),current_s=c['current_physical_seconds'],distance_s=r['distance_s'],gain_ns=(c['current_physical_seconds']-r['distance_s'])*1e9,
  conflicts=conflicts,suffix_nodes=[path[-1][0]]+[x[0] for x in reversed(path[:-1])],suffix_switches=switches))
write(b/'completion.json',dict(passed=True,rows=rows,protected_nets=sorted(protected),actual_XML_bound_edges_checked=checked,query_process_seconds=query_seconds,
 complete_process_seconds=time.monotonic()-start,source_sha256=bound,native_calls=0,
 qualification='All witnesses preserve protected-net occupancy, but other selected owners still need legal timing-budgeted replacement. Protection of whole critical nets is conservative; no-gain here is not a global impossibility certificate. Source is immutable pristineTf, not a later accepted state.'))
print([(r['target'],r['gain_ns'],len(r['conflicts'])) for r in rows],flush=True)
