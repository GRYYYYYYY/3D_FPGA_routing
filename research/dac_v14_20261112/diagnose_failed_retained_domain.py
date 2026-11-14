#!/usr/bin/env python3
"""Distinguish topological domain failure from capacity/search failure, no native rerun."""
import collections,json,resource,subprocess,time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from immutable_rr_audit_cache import GraphAuditCache
b=D/'domain_reachability_diagnostic_01';started=time.monotonic();resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));binary=b/'reachability';fixture=b/'oracle';fixture.mkdir(exist_ok=False);rng=np.random.default_rng(31767);checks=[]
for i in range(64):
 n=8+i%17;layers=rng.integers(0,2,n);adj=rng.random((n,n))<.045;np.fill_diagonal(adj,False);u,v=np.where(adj);nodes=np.zeros((n,9),dtype=np.int64);nodes[:,4]=nodes[:,7]=layers;edges=np.sort((u.astype(np.uint64)*n+v.astype(np.uint64)));np.save(fixture/'nodes.npy',nodes);np.save(fixture/'edges.npy',edges);seeds=list(map(int,rng.choice(n,size=1+i%3,replace=False)));allowed=set(map(int,np.where(rng.random(n)<.3)[0]));target=int(rng.integers(0,n));mask=(layers[:,None]==layers[None,:])|np.array([x in allowed for x in range(n)])[:,None];reach=adj&mask;np.fill_diagonal(reach,True)
 for k in range(n):reach|=reach[:,k,None]&reach[None,k,:]
 case=fixture/'case.txt';case.write_text(f'{n} {len(edges)} 1 {target} {len(seeds)}\n'+' '.join(map(str,seeds))+'\n'+str(len(allowed))+'\n'+' '.join(map(str,sorted(allowed)))+'\n');r=subprocess.run([str(binary),str(fixture/'nodes.npy'),str(fixture/'edges.npy'),str(case)],capture_output=True,text=True,timeout=60,check=True);observed=json.loads(r.stdout);expected=any(reach[x,target]for x in seeds);assert observed['reachable']==expected
 if expected:assert observed['path'][0]in seeds and observed['path'][-1]==target and all(adj[x,y]and(mask[x,y])for x,y in zip(observed['path'],observed['path'][1:]))
 checks.append(bool(expected))
assert 0<sum(checks)<len(checks);write(b/'oracle.json',dict(passed=True,cases=len(checks),positive=sum(checks),negative=len(checks)-sum(checks),reference='Independent Boolean Floyd transitive closure and explicit path verification; source bitmap domain edge predicate.',native_calls=0))
tx=D/'native_resource_bundle_dev_01/R1_fast_bundle8/round_001/candidate_00';role=read(tx/'registration.json')['roles']['reuse_on'];native=tx/'reuse_on/runs/state';source=Path(role['source']);log=(native/'joint_native.log').read_text().splitlines();failed=next(l.split()for l in log if l.startswith('FAIL_TARGET '));net,pin,target=map(int,failed[1:4]);seeds=[int(l.split()[2])for l in log if l.startswith(f'KEEP {net} ')];allow=next(l.split()for l in(native/'vertical_domain.log').read_text().splitlines()if l.startswith(f'ALLOW {net} {pin} '));allowed=list(map(int,allow[4:]));assert len(allowed)==int(allow[3])and seeds;manifest=read(source/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1]);cache=D/'rr_audit_cache_bnn_01';g=GraphAuditCache(graph,cache);assert np.all(g.nodes[:,4]==g.nodes[:,7]),'Layer predicate requires single-layer nodes';case=b/'real_case.txt';case.write_text(f'{g.n} {len(g.edges)} {g.stride} {target} {len(seeds)}\n'+' '.join(map(str,seeds))+'\n'+str(len(allowed))+'\n'+' '.join(map(str,allowed))+'\n');rows={}
for name,args in [('domain_relaxed_capacity',[]),('unrestricted_relaxed_capacity',['--unrestricted'])]:
 result=subprocess.run([str(binary),str(cache/'nodes.npy'),str(cache/'edges.npy'),str(case),*args],capture_output=True,text=True,timeout=1800,check=True);r=json.loads(result.stdout)
 if r['reachable']:
  path=r['path'];assert path[0]in seeds and path[-1]==target;wanted=[]
  for u,v in zip(path,path[1:]):
   key=(u*g.n+v)*g.stride;pos=int(np.searchsorted(g.edges,key));assert pos<len(g.edges)and int(g.edges[pos])<key+g.stride;wanted.append((u,v,int(g.edges[pos])%g.stride))
   if not args:assert int(g.nodes[u,4])==int(g.nodes[v,4])or u in allowed
  g.require_edges(wanted);r['path_edges']=wanted
 rows[name]=r
files=[Path(__file__).resolve(),b/'reachability.cpp',binary,b/'oracle.json',case,tx/'registration.json',tx/'reuse_on_audit/analysis.json',native/'joint_native.log',native/'vertical_domain.log',cache/'completion.json'];write(b/'completion.json',dict(passed=True,net=net,pin=pin,target_rr=target,retained_seed_count=len(seeds),allowed_crossing_sources=allowed,rows=rows,topological_domain_disconnection_proven=not rows['domain_relaxed_capacity']['reachable'],capacity_feasibility_proven=False,native_calls=0,route_calls=0,complete_diagnostic_seconds=time.monotonic()-started,source_sha256={str(p):sha(p)for p in files},qualification='Capacity-free directed reachability from every retained tree node, permitting additional native-illegal transit and ignoring congestion. A negative result certifies no path even in this relaxation; a positive witness does not prove native-expandable or capacity-legal routing. Existing failed/accepted transactions and running jobs unchanged; no candidate is committed by this diagnostic.'))
print(dict(net=net,pin=pin,domain_reachable=rows['domain_relaxed_capacity']['reachable'],unrestricted_reachable=rows['unrestricted_relaxed_capacity']['reachable'],seconds=time.monotonic()-started),flush=True)
