#!/usr/bin/env python3
"""Check the certificate against independent shortest paths on random DAGs."""
import copy,heapq,random
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from conditional_distance_certificate import certify

def shortest(graph,case):
    dist={int(k):v for k,v in case['anchors'].items()};heap=[(v,k,[k],[]) for k,v in dist.items()];heapq.heapify(heap)
    while heap:
        d,node,path,switches=heapq.heappop(heap)
        if dist[node]!=d:continue
        if node==case['sink']:return d,path,switches
        for dest,switch,w in graph.get(node,[]):
            if dest in case['blocked'] or dest in case['retained']:continue
            value=d+w
            if value<dist.get(dest,float('inf')):
                dist[dest]=value;heapq.heappush(heap,(value,dest,path+[dest],switches+[switch]))
    return None

counts=dict(generated=96,relaxed_reachable=0,certified=0,witness_blocked_miss=0,negative_controls=0)
for seed in range(96):
    rng=random.Random(seed);n=11;graph={};weights={};switch=0
    for u in range(n-1):
        for v in range(max(u+1,2),n):
            if rng.random()<.32 or (u==0 and v==n-1):
                w=rng.randrange(1,13)/8;weights[switch]=w;graph.setdefault(u,[]).append((v,switch,w));switch+=1
    old=dict(net=17,pin=2,sink=n-1,retained=[0,1],anchors={'0':0.,'1':.25},blocked=sorted(i for i in range(2,n-1) if rng.random()<.2))
    ref=shortest(graph,old)
    if ref is None:continue
    counts['relaxed_reachable']+=1;value,path,switches=ref;answer=dict(stop=0,distance_s=value,lower_s=value,suffix_nodes=path,suffix_switches=switches)
    new=copy.deepcopy(old);new['blocked']=sorted(set(old['blocked'])|{i for i in range(2,n-1) if rng.random()<.25});actual=shortest(graph,new);certificate=certify(old,new,answer,weights)
    if certificate['certified']:
        counts['certified']+=1;assert actual is not None and actual[0]==value==certificate['distance_s'] and certificate['new_queries']==0
    else:
        counts['witness_blocked_miss']+=1;assert set(path)&set(new['blocked'])
    changed=copy.deepcopy(new);changed['anchors']['0']=.125;assert not certify(old,changed,answer,weights)['certified'];counts['negative_controls']+=1
    unknown=copy.deepcopy(answer);unknown.update(stop=3,lower_s=0.);assert not certify(old,new,unknown,weights)['certified'];counts['negative_controls']+=1
    changed=copy.deepcopy(new);changed['sink']-=1;assert not certify(old,changed,answer,weights)['certified'];counts['negative_controls']+=1
    if old['blocked']:
        changed=copy.deepcopy(old);changed['blocked']=old['blocked'][1:];assert not certify(old,changed,answer,weights)['certified'];counts['negative_controls']+=1
assert counts['certified']>0 and counts['witness_blocked_miss']>0
out=D/'conditional_distance_certificate_validation_01.json';assert not out.exists();write(out,dict(passed=True,counts=counts,native_calls=0,new_solver_queries=0,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'conditional_distance_certificate.py']},qualification='Independent reference shortest-path agreement on random DAGs and incompatible-domain controls. Tests the conditional path certificate, not FPGA legality, STA or joint transaction feasibility.'))
print(counts)
