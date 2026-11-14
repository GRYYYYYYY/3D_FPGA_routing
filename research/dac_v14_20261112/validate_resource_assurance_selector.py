#!/usr/bin/env python3
"""Validate equal selection through independent/native evidence, with zero VPR."""
import os
from pathlib import Path
import resource
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from full_route_graph_cache import FullRouteGraphCache
from current_crossing_share_selector_v2 import select as old_select
from current_crossing_share_selector_v3 import select as new_select
from run_native_scope_policy_v4 import run_dir

b=D/'resource_assurance_selector_validation_01';b.mkdir(exist_ok=False)
prior=D/'native_census_state_evaluator_validation_01';owner=read(prior/'registration.json')
files=[Path(__file__).resolve(),D/'current_crossing_share_selector_v2.py',D/'current_crossing_share_selector_v3.py',
    D/'state_resource_assurance.py',prior/'registration.json']
bindings={str(p):sha(p) for p in files}
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bindings,prerequisite_owner=dict(pid=owner['pid'],start_ticks=owner['start_ticks']),
    question='Does changing only explicit independent/native resource evidence preserve all candidate ranking/cuts and the complete streamed current resource census?',
    native_calls=0,route_calls=0,qualification='Engineering selector replay on actual saved states; phase B waits for real native-count state validation. No route experiments or entire-configuration speed claims.'))
resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));started=time.monotonic()
root=D/'native_endpoint_vector_dev_01/A0';manifest=read(run_dir(root)/'manifest.json')
graph=Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
cache=FullRouteGraphCache(graph,D/'full_route_graph_cache_e695_01');results=[]
states=[('pristine',root),('resource_prefix',D/'fused_resource_development_01/eltwise_A0_feedback_K8/round_000/candidate_00/reuse_on_evaluation')]
for label,state in states:
    write(b/'status.json',dict(status='independent_interface_selection',case=label))
    old=old_select(state,cache,b/(label+'_old'));new=new_select(state,cache,b/(label+'_new'))
    assert old==new
    results.append(dict(case=label,passed=True,candidates=len(new),assurance='independent_physical_audit'))
    write(b/'results.json',results)
write(b/'independent_phase.json',dict(passed=True,cases=results,native_calls=0))
write(b/'status.json',dict(status='waiting_for_actual_native_census_state_validation'))
while True:
    p=process_identity(owner['pid'])
    if not p or p['state']=='Z' or p['start_ticks']!=owner['start_ticks']:break
    time.sleep(15)
if not (prior/'completion.json').exists() or not read(prior/'completion.json')['passed']:
    write(b/'completion.json',dict(passed=False,status='native_state_prerequisite_not_passed',
        independent_phase_passed=True,native_calls=0,source_sha256=bindings));raise SystemExit(1)
for label in ['canonical','native']:
    independent=prior/(label+'_independent');native=prior/(label+'_native')
    old=old_select(independent,cache,b/(label+'_old'));new=new_select(native,cache,b/(label+'_new'))
    assert old==new
    assert read(b/(label+'_new/completion.json'))['resource_assurance']['kind']=='native_actual_route_tree_census'
    results.append(dict(case=label,passed=True,candidates=len(new),assurance='native_actual_route_tree_census'))
    write(b/'results.json',results)
assert all(sha(path)==h for path,h in bindings.items())
write(b/'completion.json',dict(passed=True,cases=results,native_calls=0,route_calls=0,
    source_sha256={str(path):sha(path) for path in [b/'registration.json',b/'results.json',prior/'completion.json']},
    qualification='All source candidate/ranking and streamed wire/SB/CB/net-occupancy results match across evidence interfaces. Actual stateful native-count acceptance actor still requires separate evaluation. Waiting time is not selector/algorithm runtime.',
    complete_component_and_dependency_wait_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None))
write(b/'status.json',dict(status='passed'));print(dict(passed=True,cases=len(results),native_calls=0),flush=True)
