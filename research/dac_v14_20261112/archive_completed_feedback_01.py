"""Extend the sealed archive with the actual five-connection feedback outcome."""
import collections
import copy
import csv
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from run_native_scope_policy_v4 import run_dir
from native_problem_identity import problem_identity
from endpoint_timing_policy_streaming_v2 import compare
from pareto_archive_dimensions import annotate

parent = D/'multiobjective_complete_resource_timing_01'
out = D/'multiobjective_completed_feedback_01'
pc = read(parent/'completion.json')
assert pc['passed']
assert all(sha(parent/n) == h for n, h in pc['artifact_sha256'].items())
points = read(parent/'points.json')
receipt = D/'vector_feedback_subset_native_recovery_01/queue/completion.json'
feedback = read(receipt)
assert feedback['passed']
assert all(sha(p) == h for p, h in feedback['source_sha256'].items())
result = feedback['result']
state = Path(result['state'])
source = Path(read(D/'vector_feedback_subset_01/plan.json')['source_state'])
rd = run_dir(state)
m = read(rd/'manifest.json')
assert read(state/'completion.json')['passed'] and read(state/'input_seal.json')['passed']
assert m['metrics']['native_full_check_passed']
for name in ['packed.net', 'placed.place', 'routed.route']:
    assert sha(rd/name) == m['outputs'][name]['sha256']
physical = read(rd/'independent_audit.json')
assert physical['audit']['passed']
axes = physical['physical_metrics']
resources = dict(wirelength=axes['planar_wirelength_excluding_sb_half_nodes'],
                 SB_pairs=axes['sb_pairs_used'], CB_sources=axes['cb_crossing_output_sources_used'])
vector = read(state/'endpoint_vector.json')
delta = compare(read(source/'endpoint_vector.json'), vector)
assert resources == result['resources'] and vector['cpd_s'] == result['CPD_s']
assert delta['compatible'] and delta['setup_improved'] == 10 and delta['setup_regressed'] == 0
assert delta['hold_violation_regressions'] == 0 and delta['cpd_strictly_better']
assert all(d['accepted'] for d in result['decisions'].values())
origin = next(p for p in points if (p.get('state') or '').endswith('native_extra_opportunity_bnn_01/A0_observation'))
assert problem_identity(rd) == problem_identity(run_dir(Path(origin['state'])))
assert problem_identity(rd) == problem_identity(run_dir(source))
row = {k: copy.deepcopy(origin[k]) for k in ['circuit', 'physical_identity', 'quality_cohort', 'initial_routing_convergence']}
row.update(id=str(rd.relative_to(D)), arm='same_source_five_connection_vector_feedback',
    batch='vector_feedback_subset_native_recovery_01', batch_full_path=str(state.parent.parent),
    state=str(state), source_state=str(source), status='legal',
    record_kind='sealed_actual_feedback_transaction_from_independent_45SB_input',
    run_manifest=str(rd/'manifest.json'), binary_sha256=sha(m['command'][0]),
    final_STA_binary_sha256=sha(m['command'][0]), route_sha256=sha(rd/'routed.route'),
    route_body_sha256=route_body(rd/'routed.route'), command=m['command'], environment=m.get('environment'),
    convergence='one_registered_failure_feedback_intervention',
    opportunity='Two current tied-path targets and three donors, selected from same-source rejected aggregate feedback; strict and full-vector gates unchanged. Independent 45SB source, not the complete 43SB resource endpoint.',
    CPD_ns=vector['cpd_s']*1e9, CPD_interval_ns=[vector['cpd_s']*1e9]*2,
    CPD_precision='Full-precision native endpoint vector', **resources,
    SB_net_occupancy=axes['sb_pair_net_occupancy'], CB_net_occupancy=axes['cb_crossing_output_source_net_occupancy'],
    iterations=None, initial_router_iterations=origin.get('iterations'),
    complete_single_configuration_seconds=None, timing_cohort=None,
    analysis_only_native_seconds=read(state/'completion.json')['timing']['native_process_seconds'],
    intervention_workflow_seconds=feedback['complete_intervention_workflow_seconds'],
    audit_provenance=str(rd/'independent_audit.json'), input_seal=str(state/'input_seal.json'),
    acceptance=result['decisions'], source_constraints_sha256=vector['constraints_sha256'],
    unknowns=['Complete cold route-plus-repair time; general controller transfer and independent frozen-policy confirmation.'])
assert not any(p['id'] == row['id'] for p in points)
points.append(row)
# Close the existing 43SB trajectory without changing its physical state or timing.
closed_path = D/'completed_resource_timing_recovery_01/paired/completion.json'
closed = read(closed_path)
assert closed['passed'] and closed['operator_stop'] == 'no_admissible_candidate_in_current_portfolio'
paired = next(p for p in points if p.get('state') == closed['final_state'])
assert paired['SB_pairs'] == 43 and paired['CPD_ns'] == closed['final_CPD_s']*1e9
paired.update(timing_phase_complete=True, timing_phase_closure_receipt=str(closed_path),
    recovery_segment_seconds=closed['complete_current_segment_seconds'],
    unknowns=['Complete cold single-configuration route-plus-repair time and original interrupted elapsed time. Recovery segment is reported separately.'])
annotate(points)
summary = dict(passed=True, feedback_state=row['id'], feedback_quality_status=row['quality_status'],
    feedback_CPD_ns=row['CPD_ns'], feedback_resources=resources,
    feedback_source_state=str(source), feedback_endpoint_comparison=delta,
    feedback_CPD_gain_ps=(delta['cpd_before_s']-delta['cpd_after_s'])*1e12,
    feedback_workflow_seconds=feedback['complete_intervention_workflow_seconds'],
    complete_resource_timing=read(parent/'composition_summary.json'),
    paired_43SB_timing_trajectory_terminal=True, paired_recovery_segment_seconds=closed['complete_current_segment_seconds'],
    complete_single_configuration_seconds=None,
    qualification='Feedback is a matched-source mechanism result, not a new four-axis frontier gain if dominated. The 43SB complete-resource trajectory and independent 45SB feedback input remain distinct. No cold time or independent-sample inference.')
out.mkdir(exist_ok=False)
write(out/'points.json', points)
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','candidate_retention','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:p.get(k) for k in fields} for p in points)
write(out/'composition_summary.json', summary)
files=[Path(__file__).resolve(),parent/'completion.json',parent/'points.json',receipt,closed_path,
       state/'completion.json',state/'input_seal.json',state/'endpoint_vector.json',
       source/'endpoint_vector.json',rd/'manifest.json',rd/'independent_audit.json',D/'pareto_archive_dimensions.py']
write(out/'completion.json', dict(passed=True,parent=str(parent),records=len(points),added=[row['id']],
    native_calls=0,route_calls=0,quality_counts=dict(collections.Counter(p['quality_status'] for p in points)),
    retention_counts=dict(collections.Counter(p['candidate_retention'] for p in points)),
    source_sha256={str(p):sha(p) for p in files},
    artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','composition_summary.json']}))
print(dict(records=len(points),feedback_gain_ps=summary['feedback_CPD_gain_ps'],feedback_quality_status=row['quality_status']),flush=True)
