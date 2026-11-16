"""Exercise accounting rejection with real configurations and negative fixtures."""
import copy
from retained_prefix_workflow import D,read,write,sha
from BNN_interleaved_timing_v1 import ORDER,aggregate,validate_configs

root=D/'BNN_interleaved_timing_01'
n,d=[read(root/'configs'/f'{r}.json') for r in ['native','domain']]
validate_configs(n,d)
checks=['actual_configs_only_domain_treatment_differs']
for field,value in [('timing_fraction',.8),('terminal_resource_policy','wire'),('input_sha256',{})]:
    altered=copy.deepcopy(d);altered[field]=value
    try:validate_configs(n,altered)
    except AssertionError:checks.append('reject_asymmetric_'+field)
    else:raise AssertionError(field)
rows={r:dict(complete_verified=True,same_role_exact=True,measurement_complete=True,environment_signature_consistent=True,complete_seconds=100 if r.startswith('native') else 120) for r in ORDER}
pairs=[dict(matched_initial_state=True,endpoint_comparison_available=True) for _ in range(2)]
good=aggregate(rows,pairs);assert good['pair_domain_over_native_ratios']==[1.2,1.2]
assert not good['statistical_speedup_established'] and not good['research_complete'];checks.append('balanced_ratio_arithmetic_not_statistical_claim')
for key in ['complete_verified','same_role_exact','measurement_complete','environment_signature_consistent']:
    bad=copy.deepcopy(rows);bad['domain_1'][key]=False
    got=aggregate(bad,pairs);assert not got['paired_cost_observation_available'] and got['pair_domain_over_native_ratios'] is None
    checks.append('reject_'+key)
for key in ['matched_initial_state','endpoint_comparison_available']:
    bad=copy.deepcopy(pairs);bad[1][key]=False
    assert not aggregate(rows,bad)['paired_cost_observation_available'];checks.append('reject_'+key)
old=read(D/'orphaned_BNN_engineering_comparison_01/completion.json')
assert not old['original_observer_measurement_available']
bad=copy.deepcopy(rows);bad['native_0']['measurement_complete']=old['original_observer_measurement_available']
assert not aggregate(bad,pairs)['paired_cost_observation_available'];checks.append('actual_old_observer_loss_cannot_supply_new_pair')
receipt=root/'validation.json';assert not receipt.exists()
write(receipt,dict(passed=True,checks=checks,native_calls=0,qualification='Configuration and reporting gates only; no native repetition, timing benefit, independent input or full queue outcome validated.',
    source_sha256={str(p):sha(p) for p in [D/'BNN_interleaved_timing_v1.py',D/'validate_BNN_interleaved_timing_01.py',root/'plan.json',root/'configs/native.json',root/'configs/domain.json']}))
print(dict(passed=True,checks=len(checks),native_calls=0))
