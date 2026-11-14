#!/usr/bin/env python3
"""Reconstruct the exact virtual occupancy before a delayed native target."""
import collections,copy,resource,subprocess,sys,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from coordinated_repair_tree import from_trace,nodes,prune_sinks
from immutable_rr_audit_cache import GraphAuditCache,KINDS
from current_query_case_cache import make_case_fast,saturated_nodes
from run_native_frontier_queries import write_cases
sys.path.insert(0,str(D.parents[1]/'scripts'));from check_route import read_trace
start=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));b=D/'A0_target_order_diagnosis_01';b.mkdir(exist_ok=False)
batch=D/'bnn_strong_release_joint_dev_01';name='A0_target_only_physical_capacity';role=read(batch/'registration.json')['roles'][name];source=Path(role['source']);native=Path(read(batch/name/'completion.json')['run']);audit=read(batch/(name+'_audit/analysis.json'));assert audit['passed']
m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);g=GraphAuditCache(graph,D/'rr_audit_cache_bnn_01');binary=D/'bnn_physical_query_graph_01/graph.bin';assert sha(binary)==read(binary.with_name('graph_binding.json'))['binary_graph_sha256'] and g.receipt['graph_sha256']==read(binary.with_name('graph_binding.json'))['source_rrg_sha256']
driver=D/'current_sta_queries_01/critical_capacity_driver';assert sha(driver)==read(driver.parent/'execution.json')['output_sha256']['critical_capacity_driver']
files=[Path(__file__).resolve(),batch/'registration.json',batch/(name+'_audit/analysis.json'),native/'joint_native.log',source/'routed.route',source/'manifest.json',D/'rr_audit_cache_bnn_01/completion.json',binary,driver]
write(b/'registration.json',dict(status='registered_before_diagnostic_query',target=[73897,1],question='After earlier target reroutes but before73897p1, is its original short path blocked and is the observed178.187ps delay increase a conditional shortest-path consequence?',source_sha256={str(p):sha(p) for p in files},native_calls=0))
traces=read_trace(source/'routed.route');owners=collections.defaultdict(set)
for net,t in traces.items():
 for node in {x.inode for x in t['trace']}:owners[node].add(net)
pruned={};new=collections.defaultdict(set)
for line in (native/'joint_native.log').open():
 v=line.split()
 if v[0]=='NODE':new[int(v[1])].add(int(v[2]))
for net,pins in role['removed_pins'].items():
 net=int(net);original=from_trace(traces[net]['trace'],g.switches);pruned[net]=prune_sinks(original,pins)
 for node in nodes(original):owners[node].remove(net)
 for node in nodes(pruned[net]):owners[node].add(net)
earlier=[]
for q in role['queries']:
 if (q['net'],q['pin'])==(73897,1):break
 net=q['net'];assert net not in earlier,'This diagnosis assumes one requested target per net'
 for node in nodes(pruned[net]):owners[node].remove(net)
 for node in new[net]:owners[node].add(net)
 earlier.append(net)
assert all(len(ns)<=g.capacities[n] for n,ns in owners.items())
source_tree=from_trace(traces[73897]['trace'],g.switches);path=[];node=source_tree['sinks'][1]
while True:
 path.append(node)
 if node==source_tree['root']:break
 node=source_tree['edges'][node][0]
hits=[dict(node=n,capacity=int(g.capacities[n]),earlier_owners=sorted(owners[n]&set(earlier))) for n in path if owners[n]&set(earlier)]
caps=list(map(int,g.capacities));kinds=[KINDS[int(k)] for k in g.nodes[:,1]];saturated=saturated_nodes(owners,caps)
c=make_case_fast(dict(net=73897,pin=1,sink=source_tree['sinks'][1]),traces,kinds,g.switches,owners,caps,saturated)
# The target branch has already been pruned. Credit only nodes it currently
# owns, rather than all nodes on its original path, some now used by others.
c['blocked']=sorted(saturated-{n for n in nodes(pruned[73897]) if len(owners[n])-1<caps[n]});assert not set(c['retained'])&set(c['blocked'])
write(b/'case.json',c);write_cases(b/'case.txt',[c]);t=time.monotonic()
with (b/'stdout.log').open('w') as out,(b/'stderr.log').open('w') as err:r=subprocess.run([str(driver),str(binary),str(b/'case.txt'),'capacity'],stdout=out,stderr=err,timeout=900)
assert r.returncode==0;query_seconds=time.monotonic()-t;edges=[];result=None
for line in (b/'stdout.log').open():
 v=line.split()
 if v[0]=='RESULT':result=dict(stop=int(v[4]),distance_s=float(v[8]),lower_s=float(v[9]))
 else:assert v[0]=='EDGE';edges.append((int(v[5]),int(v[6]),float(v[7])))
assert result and result['stop']==0 and result['distance_s']==result['lower_s'];assert edges[0][0]==c['sink'] and edges[-1][1]==g.n
assert all(a[1]==z[0] for a,z in zip(edges,edges[1:]));assert not {e[0] for e in edges[:-1]}&set(c['retained']);assert not {e[0] for e in edges}&set(c['blocked'])
assert str(edges[-1][0]) in c['anchors'] and edges[-1][2]==c['anchors'][str(edges[-1][0])]
assert abs(sum(e[2] for e in edges)-result['distance_s'])<1e-23
for dest,src,w in edges[:-1]:
 lo=np.uint64((src*g.n+dest)*g.stride);i,j=np.searchsorted(g.edges,[lo,lo+np.uint64(g.stride)]);assert any(g.switches[int(x)%g.stride]==w for x in g.edges[i:j])
native_change=next(r for r in audit['changed_delays'] if r['net']==73897 and r['pin']==1)
write(b/'completion.json',dict(passed=True,earlier_targets=earlier,original_path_resources_taken=hits,original_delay_s=native_change['before_s'],native_candidate_delay_s=native_change['after_s'],conditional_exact_query=result,native_gap_to_conditional_ns=(native_change['after_s']-result['distance_s'])*1e9,
 source_sha256={str(p):sha(p) for p in files},query_process_seconds=query_seconds,complete_process_seconds=time.monotonic()-start,native_calls=0,
 qualification='Virtual occupancy reconstructed from original trees, registered pruning and completed earlier native trees. Exact conditional driver graph/anchors/filter audited. Matches only this temporary stage; not a new legal final route or general proof about greedy search.'))
print(dict(taken=hits,conditional=result,native_after_s=native_change['after_s']),flush=True)
