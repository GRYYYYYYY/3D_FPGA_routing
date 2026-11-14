#!/usr/bin/env python3
"""Freeze subsequent native portfolio trajectories from strong pristine starts."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'portfolio_execution_dev_01';b.mkdir(exist_ok=False)
for path in [D/'current_portfolio_validation_01/completion.json',D/'current_exchange_portfolio_validation_02.json']:
 assert read(path)['passed'] and all(sha(p)==h for p,h in read(path)['source_sha256'].items())
common_history=[D/'bnn_release_joint_dev_01',D/'bnn_strong_release_joint_dev_01',D/'bnn_cover_selected_dev_01',D/'critical_owner_exchange_dev_01',D/'bnn_automatic_trajectories_dev_02/A0_strict/step_001/transaction']
query_history=[D/'bnn_baseline_capacity_screens_01/A0',D/'bnn_baseline_capacity_screens_01/R1',D/'bnn_slack_release_screen_01/Tf_capacity',D/'bnn_automatic_trajectories_dev_02/Tf_strict/step_001/feedback/capacity',D/'bnn_automatic_trajectories_dev_02/A0_strict/step_001/feedback/capacity']
roles={}
for name,policy,arm in [('A0_endpoint','endpoint_vector','A0'),('A0_strict','strict','A0'),('R1_strict','strict','R1')]:
 plans=[D/f'automatic_group_plan_{arm}_01/plan.json'];portfolios=[]
 if arm=='A0':
  plans+=list((D/'bnn_automatic_trajectories_dev_02/A0_strict').glob('step_*/feedback/proposal/plan.json'))+[D/'portfolio_endpoint_replay_dev_01/round_001/feedback/proposal/plan.json'];portfolios=[D/'current_portfolio_A0_01/portfolio.json',D/'portfolio_endpoint_replay_dev_01/round_001/portfolio/portfolio.json']
 else:plans+=[D/'automatic_R1_replay_diagnostic_01/step_001/feedback/proposal/plan.json']
 roles[name]=dict(initial_state=str(D/f'timing_cone_bnn_dev_02/{arm}'),policy=policy,budget_mode='legacy',plans=list(map(str,plans)),portfolios=list(map(str,portfolios)),native_history=list(map(str,common_history)),query_history=list(map(str,query_history)),resume_from=None)
resource=D/'portfolio_Tf_zero_resource_replay_dev_01';r=read(resource/'completion.json');assert r['passed'] and r['operator_stop']=='uncached_native_proposal_not_submitted'
roles['Tf_zero_resources']=dict(initial_state=str(D/'timing_cone_bnn_dev_01/Tf'),policy='resources_under_timing',budget_mode='zero_headroom',plans=[],portfolios=[],native_history=list(map(str,common_history)),query_history=list(map(str,query_history)),resume_from=str(resource))
files=[Path(__file__).resolve(),D/'run_automatic_portfolio_repair_v3.py',D/'current_proposal_portfolio.py',D/'make_current_proposal_portfolio.py',D/'make_current_exchange_portfolio_v2.py',D/'current_portfolio_validation_01/completion.json',D/'current_exchange_portfolio_validation_02.json',D/'current_group_feedback.py',D/'current_native_reuse_v2.py',D/'fixed_anchor_acceptance.py',D/'multiobjective_acceptance_v2.py',D/'query_critical_owner_exchange.py',D/'expand_critical_owner_scope.py',D/'conditional_distance_certificate.py',resource/'completion.json',resource/'registration.json',D/'portfolio_Tf_zero_timing_replay_dev_01/completion.json']
for role in roles.values():
 files += [Path(role['initial_state'])/'completion.json',Path(role['initial_state'])/'endpoint_vector.json']+[Path(p) for p in role['plans']+role['portfolios']]
write(b/'registration.json',dict(status='registered_before_native',roles=roles,source_sha256={str(p):sha(p) for p in files},fraction=.9,objective='weighted_soft',
 question='Can a fixed two-tier portfolio (action alternatives then critical-owner free-native schedules) improve timing/vector/resource tradeoffs from pristine strong A0/R1 and continue the fixed-timing resource path without oracle-selected repairs?',
 controls='A0 strict and endpoint share the same pristine initial route, ordered candidate generation, native kernel/domain/tree opportunities and exact acceptance definitions; policies diverge only after their own accepted states. R1 starts from its own strong native state. Resource continuation preserves v3 zero-headroom policy and completed work.',
 limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
 qualifications=['No fixed trajectory round count or total research deadline. Each native/STA child retains its own safeguards.', 'Budget limits are root-specific in this development cohort; cross-start fixed absolute-resource superiority is not claimed. A shared design envelope across strong starts is subsequent work.', 'Exact requests/current-state query plans and complete native quality can be reused; old creation costs are excluded, full cold single-configuration runtime remains unknown.', 'The Tf zero-resource timing trajectory already completed with two exact reused acceptances; do not rerun it merely to fill a matrix.', 'Existing native cohorts remain untouched; new execution begins only after their final native owner is terminal.']))
print('Registered four independent subsequent native actors')
