"""Read-only actual-case/archive/cost binding, without substituting old quality."""
from pathlib import Path
from retained_prefix_workflow import D,read,sha
from state_resource_assurance import require_publication_proof
from run_native_scope_policy_v4 import run_dir

root=D/'multiobjective_complete_BNN_native_cold_01';receipt=read(root/'completion.json')
assert receipt['passed'] and receipt['records']==554 and len(receipt['added'])==13
assert all(sha(root/n)==h for n,h in receipt['artifact_sha256'].items())
assert all(sha(p)==h for p,h in receipt['source_sha256'].items())
points=read(root/'points.json');added=[p for p in points if p['id'] in receipt['added']]
assert len(added)==13 and len([p for p in added if p['actor_final_selected']])==1
case=D/'complete_resource_timing_full_flow_01/bnn_native';complete=read(case/'completion.json')
assert complete['passed'] and complete['complete_configuration_verified']
for point in added:
 state=Path(point['state']);assert read(state/'completion.json')['passed'] and require_publication_proof(state)['passed']
 assert sha(run_dir(state)/'routed.route')==point['route_sha256']
 if not point['actor_final_selected']:
  assert point['complete_single_configuration_seconds'] is None and point['timing_cohort'] is None
final=next(p for p in added if p['actor_final_selected'])
assert final['state']==complete['final_state'] and final['CPD_ns']==complete['CPD_ns']
assert {k:final[k] for k in ['wirelength','SB_pairs','CB_sources']}==complete['resources']
assert final['complete_single_configuration_seconds']==complete['complete_wall_seconds']
assert final['memory_observation']['sampled_tree_PSS_peak_kib']==complete['sampled_tree_PSS_peak_kib']
old=next(p for p in points if p['arm']=='complete_resource_native_then_current_STA_native')
assert final['quality_status']=='dominated' and old['id'] in final['quality_dominated_by']
assert old['complete_single_configuration_seconds'] is None and final['wirelength']==old['wirelength']+4
cost=D/'complete_BNN_native_cost_analysis_01';bound=read(cost/'completion.json');summary=read(cost/'summary.json')
assert bound['passed'] and summary['passed']
assert all(sha(cost/n)==h for n,h in bound['artifact_sha256'].items())
assert all(sha(p)==h for p,h in summary['source_sha256'].items())
assert summary['complete_wall_seconds']==complete['complete_wall_seconds']
assert abs(sum(summary['disjoint_category_seconds'].values())-summary['complete_wall_seconds'])<1e-8
assert summary['nested_diagnostics_not_added_to_wall']['native_search_workers']==11
assert summary['nested_diagnostics_not_added_to_wall']['actual_candidate_LOADs']==11
assert receipt['complete_measured_configurations_total']==23 and receipt['complete_known_circuits']==4
print(dict(passed=True,records=554,actual_case_final_wire=final['wirelength'],whole_seconds=final['complete_single_configuration_seconds'],
 only_final_carries_whole_time=True,old_quality_time_not_spliced=True,complete_configurations=23,native_calls_new=0),flush=True)
