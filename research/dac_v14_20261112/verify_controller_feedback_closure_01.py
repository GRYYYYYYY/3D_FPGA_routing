"""Verify the terminal v5 trajectory and the final same-scope order control."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from seed_census_analysis_pool_v2 import process_identity
from run_native_scope_policy_v4 import run_dir

actor=D/'rejection_feedback_controller_dev_01/endpoint';q=actor.parent/'queue'
queue=read(q/'completion.json');closed=read(actor/'completion.json')
assert queue['passed'] and queue['returncode']==0 and closed['passed']
assert closed['operator_stop']=='no_admissible_candidate_in_current_portfolio'
for r in [read(q/'registration.json'),read(actor/'registration.json')]:
    live=process_identity(r['pid']);assert not live or live['state']=='Z' or live['start_ticks']!=r['start_ticks']
assert all(sha(f)==h for f,h in closed['source_sha256'].items())
attempts=read(actor/'attempts.json');steps=read(actor/'steps.json')
assert len(attempts)==13 and len(steps)==closed['accepted_steps']==1
assert steps[0]['proposal']=='same_source_rejection_feedback' and steps[0]['reused_native']
assert closed['final_state']==steps[0]['evaluation']
assert closed['final_CPD_s']==1.3599797732410934e-08
assert closed['final_resources']==dict(wirelength=2061253,SB_pairs=45,CB_sources=5060)
assert closed['native_transaction_coordinators_started']==7
assert sum(not a['reused_native'] for a in attempts)==7
following=[a for a in attempts if a['round']==1]
assert len(following)==6 and not any(a['accepted'] for a in following)
feedback=actor/'round_001/rejection_feedback/portfolio.json';f=read(feedback)
assert f['passed'] and f['proposals']==[] and f['reason']=='all_observed_improving_actions_excluded_by_donor_feedback'
assert all(sha(p)==h for p,h in f['source_sha256'].items())
pair=[next(a for a in following if a['proposal']==name) for name in ['critical_owner_exchange_000_target_first','critical_owner_exchange_000_owner_first']]
vectors=[read(Path(a['evaluation'])/'endpoint_vector.json') for a in pair]
same_vector=all(vectors[0][k]==vectors[1][k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
same_body=route_body(run_dir(Path(pair[0]['evaluation']))/'routed.route')==route_body(run_dir(Path(pair[1]['evaluation']))/'routed.route')
assert same_vector and same_body
files=[Path(__file__).resolve(),q/'completion.json',actor/'completion.json',actor/'attempts.json',actor/'steps.json',actor/'reuse_receipts.json',actor/'process_costs.json',feedback]
for a in pair:files+=[Path(a['evaluation'])/'endpoint_vector.json',run_dir(Path(a['evaluation']))/'routed.route']
write(D/'controller_feedback_closure_01.json',dict(passed=True,accepted_steps=1,attempted_proposals=13,
    native_coordinators=7,exact_native_reuses=6,new_current_state_candidates=6,new_current_state_accepts=0,
    final_CPD_s=closed['final_CPD_s'],final_resources=closed['final_resources'],
    imported_controller_seconds=closed['complete_imported_state_workflow_seconds'],
    summed_top_level_child_seconds=sum(r['complete_process_seconds'] for r in read(actor/'process_costs.json')),
    repeated_initial_primary_counted_seconds=sum(r['complete_process_seconds'] for r in read(D/'controller_feedback_transition_01.json')['repeated_primary']['actual_complete_child_costs']),
    final_exchange_order_control=dict(complete_endpoint_vector_exact=same_vector,ordered_route_body_exact=same_body),
    stop_reason=f['reason'],source_sha256={str(p):sha(p) for p in files},
    qualification='Terminal registered vector policy, known feedback result reproduced once and no second accepted transition. Seven actual native coordinators include the previously documented repeated initial primary. New-state quality alternatives are policy-rejected legal candidates. Current imported execution excludes historical creation and initial routing; no cold time or independent sample claim.'))
print(dict(passed=True,accepted=1,following_accepts=0,attempts=13,order_control_exact=True),flush=True)
