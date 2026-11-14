#!/usr/bin/env python3
"""Validate both native schedules and exact zero-headroom policy decisions."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_proposal_portfolio import request_text
from multiobjective_acceptance_v2 import decide
from run_native_scope_policy_v4 import run_dir
p=D/'current_exchange_portfolio_Tf_02/portfolio.json';x=read(p);assert x['passed'] and len(x['proposals'])==2
reg=read(D/'critical_owner_exchange_dev_01/registration.json');checks=[]
for item,reference in zip(x['proposals'],['000_expanded_free_weighted','000_expanded_owner_first_weighted']):
 role=reg['roles'][reference];plan=read(item['plan']);assert plan['source_state']==role['state'] and not role['fixed_target_paths'];assert request_text(plan)==Path(role['request']).read_text();assert item['request_sha256']==sha(role['request']);checks.append(dict(proposal=item['name'],reference=reference,request_equal=True))
root=D/'timing_cone_bnn_dev_01/Tf';start=Path(reg['roles']['000_expanded_free_weighted']['state']);vroot=read(root/'endpoint_vector.json');before=read(start/'endpoint_vector.json')
def res(state):
 r=read(run_dir(state)/'independent_audit.json')['physical_metrics'];return dict(wirelength=r['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=r['sb_pairs_used'],CB_sources=r['cb_crossing_output_sources_used'])
c=read(D/'critical_owner_exchange_dev_01/completion.json');assert c['passed'];expected={'000_expanded_free_weighted':(True,False),'000_expanded_owner_first_weighted':(False,True)};policy_rows=[]
for name,pair in expected.items():
 state=Path(c['roles'][name]['evaluation']);after=read(state/'endpoint_vector.json');actual=[]
 for mode in ['timing_under_resources','resources_under_timing']:
  decision=decide(mode,before,after,res(start),res(state),cpd_limit_s=vroot['cpd_s'],resource_limits=res(root),native_valid=True,transaction_complete=True,resource_objectives=('wirelength',));actual.append(decision['accepted'])
 assert tuple(actual)==pair;policy_rows.append(dict(role=name,zero_headroom_timing_accepted=actual[0],zero_headroom_resource_accepted=actual[1]))
out=D/'current_exchange_portfolio_validation_02.json';assert not out.exists();write(out,dict(passed=True,request_checks=checks,zero_headroom_policy_checks=policy_rows,native_calls=0,source_sha256={str(q):sha(q) for q in [Path(__file__).resolve(),D/'make_current_exchange_portfolio_v2.py',D/'current_proposal_portfolio.py',D/'multiobjective_acceptance_v2.py',p,D/'critical_owner_exchange_dev_01/registration.json',D/'critical_owner_exchange_dev_01/completion.json']},qualification='Both generic schedules exactly reproduce recorded native requests. Actual legal states verify fixed-root zero-resource/zero-timing-headroom arithmetic without rewriting registered decisions or treating intermediate wire growth as resource reduction. No new route/STA or complete algorithm timing claim.'))
print(dict(requests=2,zero_headroom_policy_checks=4))
