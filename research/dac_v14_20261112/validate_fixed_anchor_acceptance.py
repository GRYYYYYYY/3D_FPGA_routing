#!/usr/bin/env python3
"""Actual-state multi-round regression checks; no rerouting or new commits."""
import math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from fixed_anchor_acceptance import decisions
from run_native_scope_policy_v4 import run_dir
def resources(state):
 a=read(run_dir(state)/'independent_audit.json');assert a['audit']['passed'];p=a['physical_metrics']
 return dict(wirelength=p['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=p['sb_pairs_used'],CB_sources=p['cb_crossing_output_sources_used'])
b=D/'bnn_release_joint_dev_01';reg=read(b/'registration.json');root=D/'timing_cone_bnn_dev_01/Tf';initial=read(root/'endpoint_vector.json');anchor=reg['roles']['Tf_combined_weighted_soft']['original_budget'];checks=[];files=[Path(__file__).resolve(),D/'fixed_anchor_acceptance.py',D/'multiobjective_acceptance_v2.py',b/'registration.json',root/'endpoint_vector.json']
for name,role in reg['roles'].items():
 if not name.startswith('Tf_'):continue
 state=b/(name+'_evaluation');assert read(state/'completion.json')['passed'];after=read(state/'endpoint_vector.json');old=read(b/(name+'_decisions.json'))
 actual=decisions(initial,after,resources(root),resources(state),anchor)
 assert actual==old,name
 checks.append(dict(case=name,original_first_step_exactly_preserved=True))
 files += [state/'completion.json',state/'endpoint_vector.json',b/(name+'_decisions.json')]
current=b/'Tf_target_only_weighted_soft_evaluation';combined=b/'Tf_combined_weighted_soft_evaluation'
a,bv=read(current/'endpoint_vector.json'),read(combined/'endpoint_vector.json');ar,br=resources(current),resources(combined)
forward=decisions(a,bv,ar,br,anchor)
assert forward['timing_under_resources']['accepted'] and not forward['resources_under_timing']['accepted']
assert forward['resources_under_timing']['resource_delta']['wirelength']==8
checks.append(dict(case='target_only_to_combined',timing_accepted=True,resource_progress_rejected=True,wire_delta=8,reason='Below initial resource cap but above current wirelength; retain as a timing tradeoff, not resource progress.'))
reverse=decisions(bv,a,br,ar,anchor)
assert reverse['resources_under_timing']['accepted'] and not reverse['strict']['accepted'] and not reverse['timing_under_resources']['accepted']
assert forward['resources_under_timing']['cpd_limit_s']==reverse['resources_under_timing']['cpd_limit_s']==anchor['CPD_s']*1.01
checks.append(dict(case='combined_to_target_only',resource_progress_accepted=True,strict_timing_rejected=True,budget_constant_across_actual_states=True))
for valid,complete in [(False,True),(True,False)]:
 d=decisions(initial,bv,resources(root),br,anchor,native_valid=valid,transaction_complete=complete)
 assert not any(r['accepted'] for r in d.values())
 checks.append(dict(case='legality_transaction_gate',native_valid=valid,transaction_complete=complete,all_rejected=True))
out=D/'fixed_anchor_acceptance_validation_01.json';assert not out.exists()
write(out,dict(passed=True,checks=checks,forward=forward,reverse=reverse,source_sha256={str(p):sha(p) for p in files},new_native_calls=0,new_commits=0,
 qualification='Arithmetic replay and multi-round interface regression on actual independently legal states. No sequential algorithm trajectory or new accepted route is claimed. Original six experiments unchanged.'))
print(dict(passed=True,checks=len(checks),first_steps_preserved=6),flush=True)
