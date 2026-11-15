"""Re-evaluate one real legal window under a separately declared fixed requirement."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from multiobjective_acceptance_v2 import decide
old=read(D/'lazy_real_fallback_validation_01/completion.json');assert old['passed'];assert all(sha(f)==h for f,h in old['source_sha256'].items())
actor=D/'complete_serial_architecture_transfer_01/sb_domain/flow/repair';initial=Path(read(actor/'registration.json')['initial_state']);initialv=read(initial/'endpoint_vector.json')
source=Path(old['source_state']);before=read(source/'endpoint_vector.json');tx=Path(old['transaction']);reg=read(tx/'registration.json')
cap=(initialv['cpd_s']*102)/100;results={};files=[Path(__file__).resolve(),D/'multiobjective_acceptance_v2.py',D/'lazy_real_fallback_validation_01/completion.json',D/'complete_serial_timing_budget_01/plan.json',actor/'registration.json',initial/'endpoint_vector.json',source/'endpoint_vector.json',tx/'registration.json']
def resources(state):
 a=read(run_dir(state)/'independent_audit.json');assert a['audit']['passed'];m=a['physical_metrics'];return dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=m['sb_pairs_used'],CB_sources=m['cb_crossing_output_sources_used'])
for name in ['reuse_on','reuse_off']:
 state=Path(old['outcomes'][name]['evaluation']);after=read(state/'endpoint_vector.json');role=reg['roles'][name];assert role['original_budget']['CPD_s']==initialv['cpd_s']
 assert read(state/'completion.json')['passed'];r=resources(state)
 original=decide('resources_under_timing',before,after,resources(source),r,cpd_limit_s=initialv['cpd_s'],resource_limits=role['fixed_resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
 declared=decide('resources_under_timing',before,after,resources(source),r,cpd_limit_s=cap,resource_limits=role['fixed_resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
 assert original['accepted']==old['outcomes'][name]['accepted']
 results[name]=dict(original_accepted=original['accepted'],new_requirement_accepted=declared['accepted'],CPD_ns=after['cpd_s']*1e9,resources=r,new_requirement_decision=declared)
 files += [state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'independent_audit.json']
assert results['reuse_on']['new_requirement_accepted'] and results['reuse_off']['new_requirement_accepted']
assert not results['reuse_on']['original_accepted']
assert results['reuse_on']['resources']['SB_pairs']==996 and results['reuse_off']['resources']['SB_pairs']==999
out=D/'SB_fixed_timing_budget_replay_01';out.mkdir(exist_ok=False)
write(out/'completion.json',dict(passed=True,native_calls_new=0,actual_original_root_CPD_ns=initialv['cpd_s']*1e9,fixed_CPD_budget_percent=102,fixed_CPD_limit_ns=cap*1e9,actual_window_source=str(source),outcomes=results,
    hypothetical_preferred_role_at_this_same_source='reuse_on',original_actual_preferred_role='reuse_off',original_routes_and_decisions_unchanged=True,source_sha256={str(f):sha(f) for f in files},qualification='Counterfactual acceptance replay of two already actual legal FULL/STA/independently audited candidates under a separately declared102 percent root timing requirement. Exact source and original root identities retained, no rolling tolerance. This does not execute/commit a new candidate, skip the historically executed OFF, predict later opportunities/final quality/time, or establish a new independent sample. The registered fresh-route native/domain full trajectories are required to test the algorithm under that new requirement. Budget choice follows observed development evidence and is not held-out confirmation.'))
print(dict(passed=True,original_CPD_ns=initialv['cpd_s']*1e9,new_fixed_cap_ns=cap*1e9,ON_now_accepted=True,all_original_decisions_unchanged=True),flush=True)
