"""Rebuild the actual index-flow event set and verify output-specific time/memory."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from state_resource_assurance import require_publication_proof
from run_native_scope_policy_v4 import run_dir

root=D/'multiobjective_joint_index_closed_01';receipt=read(root/'completion.json')
assert receipt['passed'] and receipt['records']==658 and len(receipt['added'])==13
assert all(sha(root/n)==h for n,h in receipt['artifact_sha256'].items())
assert all(sha(p)==h for p,h in receipt['source_sha256'].items())
points=read(root/'points.json');byid={p['id']:p for p in points};assert len(byid)==len(points)
parent=Path(receipt['parent']);oldpoints=read(parent/'points.json')
derived={'quality_dominated_by','nominal_quality_dominated_by','matched_time_dominated_by','quality_projection_retained','quality_status','candidate_retention','archive_retained','record_preserved','five_dimensional_comparison_count','retention_qualification'}
assert all({k:v for k,v in p.items() if k not in derived}=={k:v for k,v in byid[p['id']].items() if k not in derived} for p in oldpoints)
added=[byid[i] for i in receipt['added']]
assert len(added)==13 and sum(p['actor_final_selected'] for p in added)==1
case=D/'complete_BNN_joint_index_flow_01/bnn_native_joint_indexes';flow=case/'flow'
complete=read(case/'completion.json');done=read(flow/'completion.json')
measurement=read(case/'measurement/completion.json')
assert complete['passed'] and complete['complete_configuration_verified'] and measurement['passed']
expected={complete['initial_state'],done['timing_initial_state']}
for attempt in read(flow/'resource_flow/repair/attempts.json'):
    for result in read(Path(attempt['transaction'])/'progress.json').values():
        if result['status']=='legal_evaluated':expected.add(result['evaluation'])
for attempt in read(flow/'timing/attempts.json'):
    if attempt.get('evaluation'):expected.add(attempt['evaluation'])
assert expected=={p['state'] for p in added}
for point in added:
    state=Path(point['state']);proof=require_publication_proof(state)
    assert read(state/'completion.json')['passed'] and proof['passed']
    assert sha(run_dir(state)/'routed.route')==point['route_sha256']
    assert {k:point[k] for k in ['wirelength','SB_pairs','CB_sources']}==proof['resource_axes']
    assert point['CPD_ns']==read(state/'endpoint_vector.json')['cpd_s']*1e9
    assert point['timing_cohort'] is None
    if not point['actor_final_selected']:
        assert point['complete_single_configuration_seconds'] is None and point['memory_observation'] is None
final=next(p for p in added if p['actor_final_selected'])
assert final['state']==complete['final_state'] and final['CPD_ns']==complete['CPD_ns']
assert {k:final[k] for k in ['wirelength','SB_pairs','CB_sources']}==complete['resources']
assert final['complete_single_configuration_seconds']==complete['complete_wall_seconds']==measurement['complete_command_wall_seconds']
assert all(v==complete[k]==measurement[k] for k,v in final['memory_observation'].items())
old=next(p for p in points if p['arm']=='complete_resource_native_then_current_STA_native')
assert old['id'] in final['quality_dominated_by'] and old['complete_single_configuration_seconds'] is None
assert final['wirelength']==old['wirelength']+4
comparison=D/'complete_BNN_joint_index_flow_01/comparison.json';cmp=read(comparison)
assert cmp['passed'] and cmp['same_downstream_execution'] and all(r['byte_exact'] for r in cmp['graph_payloads'])
assert final['complete_single_configuration_seconds']==cmp['actual_complete_seconds']
baseline=next(p for p in points if p['arm']=='cold_full_native_resource_then_current_STA')
assert baseline['complete_single_configuration_seconds']==cmp['reference_complete_seconds']
assert receipt['complete_measured_configurations_total']==29 and receipt['complete_known_circuits']==5
write(root/'verification.json',dict(passed=True,records=658,added=13,actual_event_set_complete=True,
    parent_non_derived_fields_exact=True,only_actual_final_carries_own_whole_cost_and_memory=True,
    complete_measured_configurations_total=29,complete_known_circuits=5,complete_vertical_families=3,
    old_quality_cost_not_spliced=True,matched_execution_proof=str(comparison),native_calls_new=0,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),root/'completion.json',parent/'points.json',case/'completion.json',case/'measurement/completion.json',comparison]}))
print(dict(passed=True,records=658,added=13,complete_configurations=29,whole_seconds=final['complete_single_configuration_seconds']),flush=True)
