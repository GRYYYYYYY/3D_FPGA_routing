#!/usr/bin/env python3
"""Create an independent automatic actor; never rewrite a registered controller."""
from retained_prefix_workflow import D, read, write, sha

base = D / 'run_pooled_feedback_bundle_repair.py'
target = D / 'run_fused_resource_bundle_repair.py'
assert not target.exists()
s = base.read_text()
def replace(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)

replace('from native_feedback_analysis_pool import NativeAnalysisPool', 'from export_policy_analysis_pool import NativeAnalysisPool')
replace('from pool_state_evaluator_v2 import PoolStateEvaluator', 'from pool_state_evaluator_v7 import PoolStateEvaluator')
replace('from endpoint_timing_policy import compare,decide as timing_decide', 'from endpoint_timing_policy_streaming_v2 import compare,decide as timing_decide\nfrom actual_route_tree_identity import same_actual_trees')
replace("a=p.parse_args();assert a.bundle_size>0;", "p.add_argument('--graph-echo',choices=['full','compact'],default='compact');p.add_argument('--accepted-steps',type=int,default=2);p.add_argument('--rank-windows',type=int,default=3);a=p.parse_args();assert a.bundle_size>0 and a.accepted_steps>=0 and a.rank_windows>0;echo=a.graph_echo=='full';")
s = s.replace("D/'domain_failure_release_stage_01", "D/'export_policy_stage_01")
s = s.replace("D/'native_feedback_analysis_pool.py'", "D/'export_policy_analysis_pool.py'")
s = s.replace("D/'pool_state_evaluator_v2.py'", "D/'pool_state_evaluator_v7.py'")
s = s.replace("D/'endpoint_timing_policy.py'", "D/'endpoint_timing_policy_streaming_v2.py'")
replace("bindings={str(p):sha(p) for p in files}", "files += [D/'actual_route_tree_identity.py',D/'actual_route_tree_identity_validation_01.json',D/'export_policy_tiny_01/completion.json',D/'export_policy_timing_01/completion.json',D/'export_policy_resource_01/completion.json'];assert all(read(D/n)['passed'] for n in ['actual_route_tree_identity_validation_01.json','export_policy_tiny_01/completion.json','export_policy_timing_01/completion.json','export_policy_resource_01/completion.json']);bindings={str(p):sha(p) for p in files}")
replace("local_probe=dict(accepted_steps=2,ranked_candidates_per_state=3)", "local_probe=dict(accepted_steps=a.accepted_steps,ranked_candidates_per_state=a.rank_windows),graph_echo=a.graph_echo,candidate_native_observation='actual_installed_candidate_fused_FULL_freshSTA',unchanged_selection_and_acceptance=True")
replace("initial_observation_started=time.monotonic();first=evaluator.evaluate(source/'routed.route',b/'initial',physical_reference=initial);", "initial_observation_started=time.monotonic();initial_worker=pool.analyze(source/'routed.route',echo=echo);first=evaluator.evaluate(source/'routed.route',b/'initial',physical_reference=initial,native_observation=initial_worker);")
replace("while len(steps)<2:", "while a.accepted_steps==0 or len(steps)<a.accepted_steps:")
replace("range(min(3,len(candidates)))", "range(min(a.rank_windows,len(candidates)))")
replace("domain_failure_release=role['domain_failure_release']);write", "domain_failure_release=role['domain_failure_release'],echo=echo,candidate_full_sta=True);write")
replace("state=tx/(name+'_evaluation');t=time.monotonic();result=evaluator.evaluate(audit['candidate_route'],state);", "view=evaluator.candidate_observation(worker);write(tx/(name+'_actual_candidate_view.json'),view);actual=Path(view['native_directory'])/'routed.route';t=time.monotonic();assert same_actual_trees(actual,audit['candidate_route']);costs.append(dict(tag=f'{len(steps):03d}_{ci:02d}_{name}_actual_vs_reconstructed_tree_check',status='completed',complete_process_seconds=time.monotonic()-t));state=tx/(name+'_evaluation');t=time.monotonic();result=evaluator.evaluate(actual,state,native_observation=view);")
replace("reason='no_admissible_move_in_current_three_scope_integration_probe'", "reason='no_admissible_move_in_registered_current_rank_windows'")
replace("reason='two_accepted_resource_steps_integration_probe_terminal'", "reason='registered_local_accepted_prefix_complete'")
replace("selection='Uniform current-state rank; at most first three rank windows, distinct-net cuts within each bundle; fresh own STA after every final accepted transaction.'", "selection='Uniform current-state rank and registered rank-window count, distinct-net cuts within each bundle; fresh own STA after every final accepted transaction. Zero local accepted-step cap continues until no admissible move in this menu; no global research stop.'")
with target.open('x') as out:
    out.write(s)
write(D / 'fused_resource_actor_preparation_01.json', dict(passed=True, native_calls=0,
    base=str(base), target=str(target), source_sha256={str(path): sha(path) for path in [base, target, D/'pool_state_evaluator_v7.py', D/'export_policy_analysis_pool.py']},
    qualification='Independent unexecuted actor. Actual native candidate replaces redundant separate candidate LOAD; source/actual candidate/rollback native gates, full scope/capacity/physical audits and full-precision policy remain. Large full/compact proofs and tree identity validation are execution prerequisites. Compact omits full graph text only. Same deterministic selector/bundle/anchor; no cold full timing claim. Original controllers remain unchanged.'))
print(target, flush=True)
