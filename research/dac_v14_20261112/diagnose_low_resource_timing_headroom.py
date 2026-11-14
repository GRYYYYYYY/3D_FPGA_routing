#!/usr/bin/env python3
"""Current winning-cone potential after automatic release; no native route search."""
import copy
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time
import numpy as np

from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from run_native_scope_policy_v4 import run_dir
from run_native_frontier_queries import fingerprint,groups,write_cases
from current_sta_arrival_cone_compact import select
from coordinated_repair_tree import from_trace,prefixes
from resource_opportunity_census import stream_trace
from immutable_rr_audit_cache import GraphAuditCache

b=D/'low_resource_timing_headroom_01';b.mkdir(exist_ok=False)
resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3))
assert shutil.disk_usage(D).free>=80*1024**3
started=time.monotonic()
actor=D/'fused_resource_development_01/bnn_A0_feedback_K8'
steps=read(actor/'steps.json');selected=copy.deepcopy(steps[-1]);initial=Path(selected['committed_evaluation'])
assert read(initial/'completion.json')['passed']
source=run_dir(initial);assert read(source/'independent_audit.json')['audit']['passed']
driver=D/'current_sta_relaxed_01/critical_capacity_driver'
binary=D/'bnn_physical_query_graph_01/graph.bin';gb=read(binary.with_name('graph_binding.json'))
assert gb['passed'] and 'all node/switch RC zero checked' in gb['format']
assert sha(binary)==gb['binary_graph_sha256']
assert sha(driver)==read(driver.parent/'execution.json')['output_sha256']['critical_capacity_driver']
manifest=read(source/'manifest.json');graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
assert manifest['shared_inputs'][str(graph)]['sha256']==gb['source_rrg_sha256']
files=[Path(__file__).resolve(),D/'run_native_census_analysis.py',D/'current_sta_arrival_cone_compact.py',
       D/'compact_timing_cone.py',D/'run_native_frontier_queries.py',initial/'completion.json',
       initial/'endpoint_vector.json',source/'routed.route',source/'manifest.json',source/'independent_audit.json',
       actor/'registration.json',driver,binary,binary.with_name('graph_binding.json')]
bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    selected_automatic_resource_prefix=selected,source_state=str(initial),source_sha256=bindings,
    actor_terminal_claim=False,question='Does the latest legal automatic low-SB state still have source-root timing potential on its own exact current winning cone, or has this intervention position reached its static-delay reference?',
    inputs='One immutable accepted prefix selected as latest at registration; not a final method configuration or manually injected repair.',
    modification='One analysis-only FULL/STA observation exports the missing full timing graph, then current exact max-arrival tracing and source-only occupancy-relaxed distances. Exact old solver inputs are reused; only absent distances are queried.',
    limits=dict(native_VPR_this_chain=1,combined_native_VPR_maximum=3,native_seconds=1800,
                offline_query_seconds=900,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
    qualification='Diagnostic only; no native route search, acceptance or candidate score. Optimistic independent static-switch paths relax occupancy/sharing/mandatory retained branches and are not feasible repairs or a strict native-STA CPD bound. Original live actor untouched.'))

def invoke(command,logpath,phase,timeout):
    t=time.monotonic()
    with logpath.open('w') as log:
        proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write(b/'status.json',dict(status=phase,pid=proc.pid,start_ticks=process_identity(proc.pid)['start_ticks'],command=command))
        try:code=proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM)
            try:code=proc.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
            write(b/'failure.json',dict(passed=False,status='per_process_timeout',phase=phase,returncode=code))
            raise
    assert code==0,(phase,code)
    return time.monotonic()-t

analysis=b/'full_observation'
observation_seconds=invoke([sys.executable,str(D/'run_native_census_analysis.py'),'--source',str(source),
    '--batch',str(analysis),'--native-census'],b/'native_analysis.log','analysis_only_FULL_STA',1860)
assert read(analysis/'completion.json')['passed']
original,observed=read(initial/'endpoint_vector.json'),read(analysis/'endpoint_vector.json')
vector_checks={k:original[k]==observed[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']}
assert all(vector_checks.values()),'Analysis changed exact source timing; diagnose before interpreting potential'
cone_started=time.monotonic();cone=select(analysis,0.);assert cone['passed'];write(b/'cone.json',cone)
cone_seconds=time.monotonic()-cone_started
cache=GraphAuditCache(graph,D/'rr_audit_cache_bnn_01')
needed={r['net'] for r in cone['routed_connections']}
trees={r['net']:from_trace(r['trace'],cache.switches) for r in stream_trace(source/'routed.route') if r['net'] in needed}
assert set(trees)==needed
cases=[]
for connection in cone['routed_connections']:
    net,pin=connection['net'],connection['pin'];tree=trees[net];sink=tree['sinks'][pin];root=tree['root']
    cases.append(dict(net=net,pin=pin,sink=sink,root=root,retained=[root],anchors={str(root):0.},blocked=[],
        current_physical_seconds=prefixes(tree)[sink],current_native_net_delay_s=connection['native_net_delay_s'],
        domain='Full device directed zero-RC switch-delay graph; source only, occupancy/other branches relaxed.'))
assert len({(c['net'],c['pin']) for c in cases})==len(cases)
write(b/'cases.json',cases);write_cases(b/'cases.txt',cases)
references={};reused=[];answers={}
histories=[D/'full_root_timing_potential_01']
for root in [D/'strong_A0_timing_trajectories_01/strict',D/'resource_first_timing_dev_01/timing',D/'resource_first_timing_resume_01/timing']:
    histories.extend(p.parent for p in root.glob('round_*/feedback/relaxed/cases.json'))
wanted={fingerprint(c,0) for c in cases}
for history in histories:
    if not (history/'cases.json').exists():continue
    old_cases=read(history/'cases.json')
    relevant=[c for c in old_cases if fingerprint(c,0) in wanted]
    if not relevant:continue
    if history.name=='full_root_timing_potential_01':
        c=read(history/'completion.json');assert c['passed']
        assert c['source_sha256'][str(driver)]==sha(driver) and c['source_sha256'][str(binary)]==gb['binary_graph_sha256']
        assert all(sha(history/p)==h for p,h in c['artifact_sha256'].items())
    else:
        ex=read(history/'execution.json');assert read(history/'analysis.json')['passed']
        assert ex['source_sha256'][str(driver)]==sha(driver) and ex['source_sha256'][str(binary)]==gb['binary_graph_sha256']
        assert all(sha(history/p)==h for p,h in ex['output_sha256'].items())
    blocks=groups(history/'query_stdout.log')
    for case in relevant:
        key=(case['net'],case['pin'],0)
        if key not in blocks:continue
        block=blocks[key];result=block[0].split()
        if int(result[4])!=0 or float(result[8])!=float(result[9]):continue
        fp=fingerprint(case,0)
        if fp in references:
            assert float(references[fp]['block'][0].split()[8])==float(result[8]),'Conflicting exact static distances'
        else:references[fp]=dict(block=block,source=str(history),query_fingerprint=fp)
    for name in ['cases.json','query_stdout.log']:
        bindings[str(history/name)]=sha(history/name)
missing=[]
for case in cases:
    fp=fingerprint(case,0)
    if fp in references:
        ref=references[fp];answers[(case['net'],case['pin'],0)]=ref['block']
        reused.append(dict(net=case['net'],pin=case['pin'],source=ref['source'],query_fingerprint=fp))
    else:missing.append(case)
query_seconds=0.
if missing:
    write_cases(b/'missing_cases.txt',missing)
    query_seconds=invoke(['prlimit','--as='+str(24*1024**3),'--',str(driver),str(binary),str(b/'missing_cases.txt')],
        b/'missing_queries.log','missing_static_source_only_distances',900)
    answers.update(groups(b/'missing_queries.log'))
with (b/'query_stdout.log').open('w') as out:
    for case in cases:out.writelines(answers[(case['net'],case['pin'],0)])
rows=[]
for case in cases:
    block=answers[(case['net'],case['pin'],0)];result=block[0].split()
    if int(result[4])!=0 or float(result[8])!=float(result[9]):
        rows.append(dict(net=case['net'],pin=case['pin'],status='unknown_not_exact',stop=int(result[4])));continue
    edges=[r.split() for r in block[1:]];assert len(edges)==int(result[11])
    node=case['root'];visited={node};total=0.
    for row in edges:
        u,v,w=int(row[5]),int(row[6]),float(row[7]);assert u==node and v not in visited
        visited.add(v);possible=[s for s,delay in cache.switches.items() if delay==w]
        valid=[]
        for sw in possible:
            key=(u*cache.n+v)*cache.stride+sw;pos=np.searchsorted(cache.edges,np.uint64(key))
            if pos<len(cache.edges) and int(cache.edges[pos])==key:valid.append(sw)
        assert valid,'Witness is not a real directed RR edge with the stated physical switch delay'
        node=v;total+=w
    distance=float(result[8]);assert node==case['sink'] and abs(total-distance)<=max(1e-24,abs(distance)*1e-14)
    rows.append(dict(net=case['net'],pin=case['pin'],root=case['root'],sink=case['sink'],status='exact_relaxed_static_distance',
        current_switch_distance_s=case['current_physical_seconds'],current_native_net_delay_s=case['current_native_net_delay_s'],
        optimistic_source_distance_s=distance,potential_ns=(case['current_physical_seconds']-distance)*1e9,
        witness_edges=len(edges)))
assert all(sha(path)==h for path,h in bindings.items())
write(b/'reuse_receipts.json',reused)
write(b/'completion.json',dict(passed=True,source_state=str(initial),diagnostic_only_private_prefix=True,
    source_CPD_ns=observed['cpd_s']*1e9,source_physical_metrics=read(source/'independent_audit.json')['physical_metrics'],
    source_FULL_STA_vector_checks=vector_checks,selected_endpoints=cone['selected_endpoints'],
    critical_connections=len(cases),rows=rows,reused_queries=len(reused),new_queries=len(missing),
    native_analysis_calls=1,native_route_search_calls=0,complete_single_configuration_algorithm_seconds=None,
    timing=dict(analysis_and_materialization_seconds=observation_seconds,exact_current_cone_seconds=cone_seconds,
                new_offline_distance_process_seconds=query_seconds,complete_diagnostic_seconds=time.monotonic()-started),
    source_sha256=bindings,artifact_sha256={n:sha(b/n) for n in ['registration.json','cone.json','cases.json','cases.txt','query_stdout.log','reuse_receipts.json']},
    qualification='Current winning-cone empirical headroom against exact optimistic static-switch paths. Relaxed references are not legal multi-net replacements or strict native-STA CPD bounds. No acceptance tolerance or cross-version time assembly. Does not seal the running resource actor or conclude the overall research.'))
write(b/'status.json',dict(status='passed'))
print(dict(passed=True,CPD_ns=observed['cpd_s']*1e9,reused=len(reused),new=len(missing),
    potential=[(r['net'],r['pin'],r.get('potential_ns')) for r in rows]),flush=True)
