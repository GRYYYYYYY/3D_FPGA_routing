#!/usr/bin/env python3
"""Exercise actual native-count states with nonempty candidate menus."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from full_route_graph_cache import FullRouteGraphCache
from current_crossing_share_selector_v2 import select as old_select
from current_crossing_share_selector_v3 import select as new_select
from run_native_scope_policy_v4 import run_dir

b=D/'native_resource_nonempty_selection_01';b.mkdir(exist_ok=False)
prior=D/'native_census_state_evaluator_validation_01';assert read(prior/'completion.json')['passed']
sources=dict(canonical=D/'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8/round_000/candidate_00/reuse_on_evaluation',
             native=D/'fused_resource_development_01/eltwise_A0_feedback_K8/round_000/candidate_00/reuse_on_evaluation')
root=run_dir(sources['canonical']);m=read(root/'manifest.json');g=Path(m['command'][m['command'].index('--read_rr_graph')+1])
cache=FullRouteGraphCache(g,D/'full_route_graph_cache_e695_01');results=[]
for label,reference in sources.items():
    native=prior/(label+'_source')
    expected=old_select(reference,cache,b/(label+'_independent'))
    actual=new_select(native,cache,b/(label+'_native'))
    assert expected==actual and len(actual)>0,'Native interface changed a nonempty candidate menu'
    evidence=read(b/(label+'_native/completion.json'))['resource_assurance']
    assert evidence['kind']=='native_actual_route_tree_census' and evidence['independent_physical_audit'] is False
    results.append(dict(case=label,passed=True,candidates=len(actual),
                        source_native_state=str(native),reference_state=str(reference)))
write(b/'completion.json',dict(passed=True,cases=results,native_calls=0,route_calls=0,
    source_sha256={str(path):sha(path) for path in [Path(__file__).resolve(),D/'current_crossing_share_selector_v3.py',
        D/'state_resource_assurance.py',prior/'completion.json']},
    qualification='Nonempty native-source menus match the actual independently audited source reference, supplementing the empty terminal-candidate menu tests. No new route/query calls or integrated full-algorithm claim.'))
q=D/'native_census_resource_equivalence_01/queue'
write(q/'additional_validation_binding.json',dict(passed=True,proof=str(b/'completion.json'),proof_sha256=sha(b/'completion.json'),
    original_registration_unchanged=True,qualification='Additional passed input-state nonempty-menu validation; original queued actor code, inputs and acceptance unchanged.'))
print(dict(passed=True,cases=results,native_calls=0),flush=True)
