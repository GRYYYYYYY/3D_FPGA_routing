#!/usr/bin/env python3
"""Use the native failure's actual transient occupancy, not a stale input route."""
import json,resource,subprocess,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from immutable_rr_audit_cache import GraphAuditCache
b=D/'domain_capacity_diagnostic_01';b.mkdir(exist_ok=False);started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));prior=D/'domain_reachability_diagnostic_01';assert read(prior/'completion.json')['passed'];binary=prior/'reachability_capacity';f=b/'oracle';f.mkdir();rng=np.random.default_rng(317671);checks=[]
for i in range(64):
 n=8+i%17;z=rng.integers(0,2,n);adj=rng.random((n,n))<.06;np.fill_diagonal(adj,False);u,v=np.where(adj);nodes=np.zeros((n,9),dtype=np.int64);nodes[:,0]=2;nodes[:,4]=nodes[:,7]=z;occ=rng.integers(0,3,n,dtype=np.int64);edges=np.sort(u.astype(np.uint64)*n+v.astype(np.uint64));np.save(f/'nodes.npy',nodes);np.save(f/'edges.npy',edges);np.save(f/'occ.npy',occ);seeds=list(map(int,rng.choice(n,size=1+i%3,replace=False)));allowed=set(map(int,np.where(rng.random(n)<.3)[0]));target=int(rng.integers(0,n));domain=(z[:,None]==z[None,:])|np.array([x in allowed for x in range(n)])[:,None];available=occ<nodes[:,0];available[seeds]=True;reach=adj&domain&available[None,:];np.fill_diagonal(reach,True)
 for k in range(n):reach|=reach[:,k,None]&reach[None,k,:]
 case=f/'case.txt';case.write_text(f'{n} {len(edges)} 1 {target} {len(seeds)}\n'+' '.join(map(str,seeds))+'\n'+str(len(allowed))+'\n'+' '.join(map(str,allowed))+'\n');result=subprocess.run([str(binary),str(f/'nodes.npy'),str(f/'edges.npy'),str(case),'--capacity',str(f/'occ.npy')],capture_output=True,text=True,timeout=60,check=True);r=json.loads(result.stdout);expected=any(reach[s,target]for s in seeds);assert r['reachable']==expected
 if expected:assert r['path'][0]in seeds and r['path'][-1]==target and all(adj[u,v]and domain[u,v]and available[v]for u,v in zip(r['path'],r['path'][1:]))
 checks.append(bool(expected))
write(b/'oracle.json',dict(passed=True,cases=len(checks),positive=sum(checks),negative=len(checks)-sum(checks),reference='Independent Boolean Floyd with domain/available-node mask and retained-node seeds; path verification.',native_calls=0))
tx=D/'native_resource_bundle_dev_01/R1_fast_bundle8/round_001/candidate_00';role=read(tx/'registration.json')['roles']['reuse_on'];rd=tx/'reuse_on/runs/state';m=read(Path(role['source'])/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);cache=D/'rr_audit_cache_bnn_01';g=GraphAuditCache(graph,cache);occ=np.zeros(g.n,dtype=np.int64);counts=0
for line in(rd/'joint_native.log').open():
 if line.startswith('OCC '):
  _,node,value=line.split();node,value=int(node),int(value);assert value>0 and occ[node]==0;occ[node]=value;counts+=1
assert counts and np.all(occ<=g.capacities);np.save(b/'failure_occupancy.npy',occ);rows={};case=prior/'real_case.txt';values=case.read_text().split();k=int(values[4]);seeds=set(map(int,values[5:5+k]));allowed=set(map(int,read(prior/'completion.json')['allowed_crossing_sources']))
for name,args in[('domain_capacity',[]),('unrestricted_capacity',['--unrestricted'])]:
 result=subprocess.run([str(binary),str(cache/'nodes.npy'),str(cache/'edges.npy'),str(case),'--capacity',str(b/'failure_occupancy.npy'),*args],capture_output=True,text=True,timeout=1800,check=True);r=json.loads(result.stdout)
 if r['reachable']:
  path=r['path'];assert path[0]in seeds and all(occ[v]<g.capacities[v]or v in seeds for v in path);wanted=[]
  for u,v in zip(path,path[1:]):
   if not args:assert int(g.nodes[u,4])==int(g.nodes[v,4])or u in allowed
   key=(u*g.n+v)*g.stride;pos=int(np.searchsorted(g.edges,key));assert pos<len(g.edges)and int(g.edges[pos])<key+g.stride;wanted.append((u,v,int(g.edges[pos])%g.stride))
  g.require_edges(wanted);r['path_edges']=wanted
 rows[name]=r
files=[Path(__file__).resolve(),binary,prior/'reachability_capacity.cpp',prior/'completion.json',case,b/'oracle.json',b/'failure_occupancy.npy',rd/'joint_native.log',rd/'vertical_domain.log',tx/'registration.json',cache/'completion.json'];write(b/'completion.json',dict(passed=True,net=31767,pin=1,occupied_resource_records=counts,uses_actual_failure_transient_occupancy=True,rows=rows,native_calls=0,route_calls=0,complete_diagnostic_seconds=time.monotonic()-started,source_sha256={str(p):sha(p)for p in files},qualification='All retained tree nodes are optimistic seeds; actual OCC is captured after5 successful repairs and before failed query cleanup, not rebuilt from the old original source route. Hard occupancy mask adds no capacity for the same retained nodes. Native re-expansion restrictions, timing costs and forced nonconfigurable closures are relaxed: negative implies no path even in this larger space; positive witness is not a final legal native route or accepted candidate.'))
print(dict(domain=rows['domain_capacity']['reachable'],unrestricted=rows['unrestricted_capacity']['reachable'],seconds=time.monotonic()-started),flush=True)
