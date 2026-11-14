#!/usr/bin/env python3
"""Consume the completed current cone and latest audited reverse-distance cache."""
import os
import resource
import shutil
import subprocess
from pathlib import Path
import time
import numpy as np
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from run_native_scope_policy_v4 import run_dir
from run_native_frontier_queries import fingerprint,groups,write_cases
from immutable_rr_audit_cache import GraphAuditCache

started=time.monotonic();prior=D/'low_resource_timing_headroom_02'
observation=prior/'full_observation';assert read(observation/'completion.json')['passed']
assert read(prior/'cone.json')['passed']
write(prior/'failure.json',dict(passed=False,status='obsolete_unsealed_reference_cache_selected',
    native_FULL_STA_passed=True,current_cone_passed=True,native_analysis_calls=1,native_route_search_calls=0,
    reason='Reference selection used incomplete full_root_timing_potential_01; latest audited cache is02 and documents reverse/virtual-anchor semantics.',
    observation='full_observation/completion.json',recovery='low_resource_timing_headroom_03',
    repeat_native_or_distance_queries_required=False))
write(prior/'status.json',dict(status='diagnostic_failed_obsolete_cache_native_and_cone_preserved'))
b=D/'low_resource_timing_headroom_04';b.mkdir(exist_ok=False)
reg=read(prior/'registration.json');initial=Path(reg['source_state']);cases=read(prior/'cases.json')
reference=D/'full_root_timing_potential_02';ref=read(reference/'completion.json');assert ref['passed']
assert all(sha(reference/n)==h for n,h in ref['artifact_sha256'].items())
assert all(sha(path)==h for path,h in ref['source_sha256'].items())
reference_reg=read(reference/'registration.json')
driver=D/'current_sta_relaxed_01/critical_capacity_driver';binary=D/'bnn_physical_query_graph_01/graph.bin'
assert reference_reg['source_sha256'][str(driver)]==sha(driver)
assert reference_reg['source_sha256'][str(binary)]==sha(binary)
files=[Path(__file__).resolve(),prior/'registration.json',prior/'failure.json',prior/'cone.json',
    prior/'cases.json',D/'low_resource_timing_headroom_03/failure.json',driver,binary,observation/'completion.json',observation/'endpoint_vector.json',
    initial/'completion.json',initial/'endpoint_vector.json',reference/'registration.json',reference/'completion.json',
    reference/'cases.json',reference/'query_stdout.log',D/'audit_full_root_timing_potential_v2.py']
bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_state=str(initial),observation_state=str(observation),source_sha256=bindings,
    question='Use the actually completed full-precision current cone and latest audited root-distance reference to assess timing potential after45SB release, with no repeated native or distance calls.',
    private_prefix_diagnostic=True,prior_segments=['low_resource_timing_headroom_01','low_resource_timing_headroom_02'],
    native_analysis_calls=0,native_route_search_calls=0,offline_distance_queries='only unmatched current source-root distances',
    qualification='Recovery of read-only evidence selection/audit only. Prior successful observations, failure reasons and segment times retained. Not a final algorithm point or native global optimum.'))
origin,observed=read(initial/'endpoint_vector.json'),read(observation/'endpoint_vector.json')
checks={k:origin[k]==observed[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']};assert all(checks.values())
source=run_dir(initial);m=read(source/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
cache=GraphAuditCache(graph,D/'rr_audit_cache_bnn_01');assert m['shared_inputs'][str(graph)]['sha256']==cache.receipt['graph_sha256']
lookup={fingerprint(c,0):c for c in read(reference/'cases.json')};answers=groups(reference/'query_stdout.log')
missing=[case for case in cases if fingerprint(case,0) not in lookup]
query_seconds=0.
if missing:
    assert shutil.disk_usage(D).free>=80*1024**3
    write_cases(b/'missing_cases.txt',missing)
    t=time.monotonic()
    with (b/'new_queries.log').open('w') as out,(b/'query_stderr.log').open('w') as err:
        result=subprocess.run(['prlimit','--as='+str(24*1024**3),'--',str(driver),str(binary),str(b/'missing_cases.txt')],stdout=out,stderr=err,timeout=900)
    query_seconds=time.monotonic()-t
    write(b/'query_process.json',dict(returncode=result.returncode,seconds=query_seconds,queries=len(missing)))
    assert result.returncode==0
    answers.update(groups(b/'new_queries.log'))
rows=[];receipts=[]
for case in cases:
    fp=fingerprint(case,0)
    reused=fp in lookup
    old=lookup[fp] if reused else case
    assert case['root']==old['root'] and case['sink']==old['sink']
    block=answers[(old['net'],old['pin'],0)];result=block[0].split()
    assert int(result[4])==0 and float(result[8])==float(result[9])
    path=[line.split() for line in block[1:]];assert len(path)==int(result[11])
    assert tuple(map(int,path[-1][5:7]))==(case['root'],cache.n) and float(path[-1][7])==0.
    cursor=case['root'];visited={cursor};total=0.;witness=[]
    for line in reversed(path[:-1]):
        u,v,w=int(line[6]),int(line[5]),float(line[7]);assert cursor==u and v not in visited
        valid=[]
        for sw,delay in cache.switches.items():
            if delay!=w:continue
            key=(u*cache.n+v)*cache.stride+sw;pos=np.searchsorted(cache.edges,np.uint64(key))
            if pos<len(cache.edges) and int(cache.edges[pos])==key:valid.append(sw)
        assert valid,'Reverse witness lacks a real forward physical RR edge'
        cursor=v;visited.add(v);total+=w;witness.append([u,v,valid[0],w])
    distance=float(result[8]);assert cursor==case['sink'] and abs(total-distance)<=max(1e-24,abs(distance)*1e-14)
    rows.append(dict(net=case['net'],pin=case['pin'],root=case['root'],sink=case['sink'],
        current_switch_distance_s=case['current_physical_seconds'],current_native_net_delay_s=case['current_native_net_delay_s'],
        optimistic_source_distance_s=distance,potential_ns=(case['current_physical_seconds']-distance)*1e9,
        status='exact_optimistic_static_distance',actual_directed_witness=witness))
    receipts.append(dict(net=case['net'],pin=case['pin'],fingerprint=fp,source=str(reference/'query_stdout.log') if reused else str(b/'new_queries.log'),reused=reused))
assert all(sha(path)==h for path,h in bindings.items())
write(b/'reuse_receipts.json',receipts)
cone=read(prior/'cone.json')
write(b/'completion.json',dict(passed=True,source_state=str(initial),observation_state=str(observation),
    source_CPD_ns=observed['cpd_s']*1e9,source_physical_metrics=read(source/'independent_audit.json')['physical_metrics'],
    source_FULL_STA_vector_checks=checks,selected_endpoints=cone['selected_endpoints'],critical_connections=len(cases),rows=rows,
    reused_queries=sum(r['reused'] for r in receipts),new_queries=len(missing),new_offline_query_process_seconds=query_seconds,native_analysis_calls_this_segment=0,native_route_search_calls=0,
    prior_successful_native_analysis_segments=[dict(directory=str(D/name),
        complete_observation_seconds=read(D/name/'full_observation/completion.json')['timing']['complete_evaluation_seconds'])
        for name in ['low_resource_timing_headroom_01','low_resource_timing_headroom_02']],
    complete_this_segment_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None,
    source_sha256=bindings,artifact_sha256={'reuse_receipts.json':sha(b/'reuse_receipts.json')},
    qualification='Current winning-cone references reused only after graph/driver/source/sink/anchor equality and forward physical witness validation. Distances relax occupancy/whole-net sharing/preserved branches; no feasible repair or strict native-STA CPD bound claimed. Original actor remains live and private. No acceptance tolerance, repeated successful queries or assembled cold time.'))
write(b/'status.json',dict(status='passed'))
print(dict(passed=True,reused=sum(r['reused'] for r in receipts),new_queries=len(missing),
           potential=[(r['net'],r['pin'],r['potential_ns']) for r in rows]),flush=True)
