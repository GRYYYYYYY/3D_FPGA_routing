#!/usr/bin/env python3
"""Check actual proposal requests against sealed independent native controls."""
import hashlib
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_proposal_portfolio import request_text,generate
out=D/'current_portfolio_validation_01';out.mkdir(exist_ok=False);p=D/'current_portfolio_A0_01/portfolio.json';menu=read(p);assert menu['passed'];checks=[]
old=read(D/'bnn_strong_release_joint_dev_01/registration.json')['roles'];selected=read(D/'bnn_cover_selected_dev_01/registration.json')['roles']
matching={'primary':selected['A0_cover90_weighted_soft'],'all_positive_combined':old['A0_combined_weighted_soft'],'all_positive_target_only':old['A0_target_only_weighted_soft'],'all_positive_owner_only':old['A0_release_only_weighted_soft']}
for item in menu['proposals']:
 plan=read(item['plan']);role=matching[item['name']];body=request_text(plan);assert body==Path(role['request']).read_text();assert hashlib.sha256(body.encode()).hexdigest()==item['request_sha256'];checks.append(dict(proposal=item['name'],connections=len(plan['repair_pins']),exact_historical_request=role['request']))
assert len(checks)==4
# An accepted state's certified empty action class creates no fake fallback.
empty=D/'bnn_automatic_trajectories_dev_02/Tf_strict/step_001/feedback/proposal/plan.json';result=generate(empty,out/'empty');assert not result['proposals']
# Repeated combinations within a real menu must not request duplicate execution.
assert len({x['request_sha256'] for x in menu['proposals']})==len(menu['proposals'])
write(out/'completion.json',dict(passed=True,checks=checks,empty_current_action_class=True,no_duplicate_native_requests=True,native_calls=0,route_commits=0,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'current_proposal_portfolio.py',p,D/'bnn_strong_release_joint_dev_01/registration.json',D/'bnn_cover_selected_dev_01/registration.json',empty]},qualification='Actual A0 native request-byte equality for four independently derived alternatives and an actual accepted-state empty class. No new native/STA run or claim that this portfolio covers every resource/vector opportunity.'))
print(dict(passed=True,request_controls=len(checks),empty_class=True))
