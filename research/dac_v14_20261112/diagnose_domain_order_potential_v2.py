#!/usr/bin/env python3
"""Recover minimum transaction occupancy from native KEEP/NODE/OCC, no rerouting."""
import collections,json,resource,subprocess,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from immutable_rr_audit_cache import GraphAuditCache
b=D/'domain_order_potential_02';b.mkdir(exist_ok=False);started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));prior=D/'domain_capacity_diagnostic_01';assert read(prior/'completion.json')['passed'];tx=D/'native_resource_bundle_dev_01/R1_fast_bundle8/round_001/candidate_00';rd=tx/'reuse_on/runs/state';role=read(tx/'registration.json')['roles']['reuse_on'];m=read(Path(role['source'])/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);cache=D/'rr_audit_cache_bnn_01';g=GraphAuditCache(graph,cache);failure=np.load(prior/'failure_occupancy.npy');initial=failure.copy();kept=collections.defaultdict(collections.Counter);final=collections.defaultdict(collections.Counter)
for line in(rd/'joint_native.log').open():
 if line.startswith('KEEP '):v=line.split();kept[int(v[1])][int(v[2])]+=1
 elif line.startswith('NODE '):v=line.split();final[int(v[1])][int(v[2])]+=1
assert set(kept)==set(final)==set(map(int,role['removed_pins']));assert all(not(kept[n]-final[n])for n in kept),'Restorations must only add to fixed retained trees'
for net,counts in final.items():
 for node,count in counts.items():initial[node]-=count
for net,counts in kept.items():
 for node,count in counts.items():initial[node]+=count
assert np.all(initial>=0)and np.all(initial<=failure)and np.all(initial<=g.capacities);assert kept[31767]==final[31767];np.save(b/'initial_partial_occupancy.npy',initial);binary=D/'domain_reachability_diagnostic_01/reachability_capacity';case=D/'domain_reachability_diagnostic_01/real_case.txt';result=subprocess.run([str(binary),str(cache/'nodes.npy'),str(cache/'edges.npy'),str(case),'--capacity',str(b/'initial_partial_occupancy.npy')],capture_output=True,text=True,timeout=1800,check=True);r=json.loads(result.stdout);known=read(prior/'completion.json');freepath=known['rows']['unrestricted_capacity']['path'];seeds=set(kept[31767]);assert all(initial[v]<g.capacities[v]or v in seeds for v in freepath)
if r['reachable']:
 assert r['path'][0]in seeds and r['path'][-1]==known['rows']['unrestricted_capacity']['path'][-1];assert all(initial[v]<g.capacities[v]or v in seeds for v in r['path'])
files=[Path(__file__).resolve(),prior/'completion.json',prior/'failure_occupancy.npy',rd/'joint_native.log',tx/'registration.json',b/'initial_partial_occupancy.npy',binary];write(b/'completion.json',dict(passed=True,net=31767,pin=1,initial_domain_capacity_reachable=r['reachable'],failure_domain_capacity_reachable=known['rows']['domain_capacity']['reachable'],initial_unrestricted_capacity_reachable_by_prior_witness=True,initial_reconstruction='actual_failure_OCC - sum(current_partial_NODE_multiset) + sum(initial_KEEP_multiset)',restoration_adds_only=True,earlier_five_resource_additions=int(np.sum(failure-initial)),initial_domain_query=r,ordering_cannot_fix_same_fixed_domain_bundle=not r['reachable'],native_calls=0,route_calls=0,complete_diagnostic_seconds=time.monotonic()-started,source_sha256={str(p):sha(p)for p in files},qualification='Every retained node is an optimistic seed and nonconfigurable closure/re-expansion are relaxed. If domain path is absent before any restoration, add-only later restorations cannot create one under this exact fixed pruned scope/domain; this excludes pure ordering/search-budget fixes for this bundle, not scope expansion or domain relaxation. If present, ordering is only a candidate explanation, not a complete legal eight-connection solution. No source route/actual occupancy was mutated.'))
print(dict(initial_domain=r['reachable'],failure_domain=known['rows']['domain_capacity']['reachable'],ordering_alone_excluded=not r['reachable']),flush=True)
