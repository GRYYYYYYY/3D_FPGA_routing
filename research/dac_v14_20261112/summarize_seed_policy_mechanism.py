#!/usr/bin/env python3
"""Interpret native cost labels, invariance and timing/resource acceptance separately."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import compare,decide as timing_decide
from multiobjective_acceptance_v2 import decide
from run_native_scope_policy_v4 import run_dir

out=D/'repair_seed_order_mechanism_01.json'
assert not out.exists()
experiment=D/'repair_seed_order_eltwise_01'
c=read(experiment/'completion.json');assert c['passed']
results=read(experiment/'results.json')
old=results['native_canonical'];native=results['native_native'];stable=results['delay_rr_id_native']
rows=[]
for a,b in zip(old['native_costs'],native['native_costs']):
    if a!=b:rows.append(dict(canonical=a,native=b))
before=read(Path(native['independent_candidate_state'])/'endpoint_vector.json')
after=read(Path(stable['independent_candidate_state'])/'endpoint_vector.json')
source=D/'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8/round_000/candidate_00/reuse_on_evaluation'
source_vector=read(source/'endpoint_vector.json')
anchor=read(D/'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8/registration.json')['anchor']
def resources(state):
    p=read(run_dir(state)/'independent_audit.json')['physical_metrics']
    return dict(wirelength=p['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=p['sb_pairs_used'],CB_sources=p['cb_crossing_output_sources_used'])
source_decision=decide('resources_under_timing',source_vector,after,resources(source),stable['resources'],
    cpd_limit_s=anchor['CPD_s'],resource_limits=anchor['resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
files=[Path(__file__).resolve(),experiment/'completion.json',experiment/'results.json',
    Path(native['independent_candidate_state'])/'endpoint_vector.json',Path(stable['independent_candidate_state'])/'endpoint_vector.json',
    source/'endpoint_vector.json',D/'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8/registration.json',
    D/'repair_seed_order_tiny_01/completion.json',D/'fused_preset_tiny_01/completion.json']
write(out,dict(passed=True,source_representation_invariance=c['invariance'],
    actual_resources={key:row['resources'] for key,row in results.items()},
    native_representation_cost_row_differences=rows,
    real_cost_interpretation='All recorded A* factors are0; actual sink labels are finite and read before reset. Three later native source-representation cost rows differ, including pressure retries, so the entire23wire difference must not be called a proven equal-cost heap tie. Primary formulas remain fixed; earlier different route choices change later seed states/competition.',
    delay_policy_vs_preserved_native_vector=compare(before,after),
    delay_policy_vs_preserved_native_wire_delta=stable['resources']['wirelength']-native['resources']['wirelength'],
    delay_policy_vs_canonical_native_wire_delta=stable['resources']['wirelength']-old['resources']['wirelength'],
    single_source_resource_policy=source_decision,
    strict_timing_control=timing_decide('strict',source_vector,after,True),
    endpoint_vector_control=timing_decide('endpoint_vector',source_vector,after,True),
    source_sha256={str(path):sha(path) for path in files},native_calls=0,
    qualification='One fixed post-first-repair source and exact source-representation intervention. Stable policies remove the observed ambiguity; delay/RR-ID reaches217183wire/24SB/965CB at unchanged6.018101ns and passes the stated source/root resource policy only as recorded. This is a legal development candidate, not automatic pristine-root transfer, broad algorithm superiority, a per-circuit configuration policy, or whole cold speed. Global fixed-policy A0/R1/Tf transfer is separately registered.'))
print(dict(passed=True,invariance={k:v['actual_candidate_topology_same']for k,v in c['invariance'].items()},
    cost_differences=len(rows),wire_delta_to_preserved_native=stable['resources']['wirelength']-native['resources']['wirelength'],
    resource_policy_accepts=source_decision['accepted']),flush=True)
