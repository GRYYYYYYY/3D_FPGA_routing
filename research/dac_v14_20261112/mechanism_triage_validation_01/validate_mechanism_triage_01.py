"""Exercise triage with actual metadata and objective/state-boundary counterexamples."""
import copy
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from recommend_current_mechanisms_v1 import recommend

root=D/'mechanism_triage_validation_01';assert not root.exists();root.mkdir()
matrix=D/'mechanism_selection_evidence_01';rows=read(matrix/'pairs.json');summaries=[]
for r in rows:
    f=r['native'];state=dict(objective='resources_under_timing',legal_root=True,
        fixed_envelope=dict(CPD_limit_s=f['fixed_CPD_limit_s'],resource_limits=f['fixed_resource_limits']),
        sharing_scopes=f['initial_STA_eligible_sharing_scopes'],eligible_owner_groups=f['initial_observed_eligible_owner_groups'])
    answer=recommend(state)
    if state['sharing_scopes']>0:assert answer['next_mechanism']=='evaluate_matched_sharing_group'
    assert answer['expected_gain'] is None and not answer['installed_in_frozen_controller']
    summaries.append(dict(label=r['label'],input=state,output=answer))
strict=next(x for x in summaries if x['label']=='Eltwise SB');relaxed=next(x for x in summaries if x['label']=='Eltwise SB 102%')
assert strict['output']['next_mechanism']==relaxed['output']['next_mechanism']
assert strict['output']['fixed_envelope']['CPD_limit_s']!=relaxed['output']['fixed_envelope']['CPD_limit_s']
conv=copy.deepcopy(next(x['input'] for x in summaries if x['label']=='Conv-hls CP1r2'));conv['objective']='timing_under_resources'
proof=D/'cp1r2_cross_circuit_cohort_01/conv_hls_native_evidence_01/no_op_mechanism.json';q=read(proof)['query_observations']['relaxed']
assert q['queries']==18 and q['positive_improvements']==0 and q['capacity_conflicting_witnesses']==7
conv['timing_queries']=dict(complete=True,count=18,positive_gain_count=0,capacity_conflicting_count=7,positive_gain_capacity_conflicts=0)
assert recommend(conv)['next_mechanism']=='advance_selected_timing_menu'
robot=copy.deepcopy(next(x['input'] for x in summaries if x['label']=='Robot'));robot['sharing_menu_closed']=True
owner=D/'robot_current_owner_screen_01/completion.json';o=read(owner);assert o['passed'] and o['eligible_joint_groups']==16
robot['eligible_owner_groups']=16;assert recommend(robot)['next_mechanism']=='evaluate_resource_owner_group'
# Same zero-delay evidence cannot exclude a resource-owner proposal.
robot['timing_queries']=conv['timing_queries'];assert recommend(robot)['next_mechanism']=='evaluate_resource_owner_group'
timing=copy.deepcopy(robot);timing['objective']='timing_under_resources';assert recommend(timing)['next_mechanism']=='advance_selected_timing_menu'
timing['timing_queries']=dict(complete=True,count=2,positive_gain_count=1,capacity_conflicting_count=1,positive_gain_capacity_conflicts=0)
assert recommend(timing)['next_mechanism']=='evaluate_timing_target_group'
timing['timing_queries']['positive_gain_capacity_conflicts']=1;assert recommend(timing)['next_mechanism']=='evaluate_timing_owner_group'
# Real release event: select only the failed net; other nets remain guided.
release=D/'complete_serial_additional_circuits_01/robot_rl_domain/flow/repair/round_000/candidate_00/reuse_on_domain_audit.json';actual=read(release)
failed=actual['released_queries'][0][0];active=actual['initial_domain_nets'];assert failed in active
private=copy.deepcopy(robot);private.update(private_transaction_active=True,active_domain_nets=active,already_released_nets=[],
    guided_failure=dict(net=failed,operational_search_failed=True))
answer=recommend(private);assert answer['released_net']==failed and set(answer['remaining_guided_nets'])==set(active)-{failed}
private['already_released_nets']=[failed]
try:recommend(private)
except AssertionError:pass
else:raise AssertionError('Repeated per-net release was accepted')
for r in read(matrix/'no_legal_root_attempts.json'):
    failed=dict(objective='resources_under_timing',legal_root=False,sharing_scopes=None,eligible_owner_groups=None)
    assert recommend(failed)['next_mechanism']=='retain_initial_outcome'
write(root/'recommendations.json',summaries)
files=[Path(__file__).resolve(),D/'recommend_current_mechanisms_v1.py',matrix/'completion.json',matrix/'pairs.json',matrix/'no_legal_root_attempts.json',proof,owner,release]
write(root/'completion.json',dict(passed=True,actual_complete_configuration_contexts=10,actual_initial_failure_contexts=10,
    same_scope_timing_envelope_counterexample_retained=True,resource_and_timing_owner_triggers_separated=True,
    marginal_conflicts_not_assumed_positive_conflicting_witness=True,release_is_actual_failure_and_per_net=True,
    repeated_release_rejected=True,new_native_calls=0,new_independent_inputs=0,controller_modified=False,
    complete_method_gain_or_cost_established=False,source_sha256={str(f):sha(f) for f in files},
    qualification='Pure development triage exercised on existing metadata and explicit state-boundary counterexamples. It is not installed in any frozen release or registered flow, predicts no QoR and has no measured savings. Future integrated version and prospective matched controls are required.'))
print(dict(passed=True,complete_contexts=10,failure_contexts=10,controller_modified=False,new_native_calls=0))
