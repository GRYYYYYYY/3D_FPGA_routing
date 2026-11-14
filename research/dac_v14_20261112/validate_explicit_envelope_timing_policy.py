#!/usr/bin/env python3
"""Actual recorded timing/vector cases and non-accumulating numerical controls."""
import copy
import math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from explicit_envelope_timing_policy import decide
from multiobjective_acceptance_v2 import decide as resource_decide
from run_native_scope_policy_v4 import run_dir

out=D/'explicit_envelope_timing_policy_validation_01.json';assert not out.exists()
terminal=read(D/'resource_first_timing_terminal_summary_01.json');assert terminal['passed']
limits=read(D/'resource_first_timing_dev_01/absolute_limits.json')
files=[Path(__file__).resolve(),D/'explicit_envelope_timing_policy.py',
       D/'endpoint_timing_policy_streaming_v2.py',D/'resource_first_timing_terminal_summary_01.json',
       D/'resource_first_timing_dev_01/absolute_limits.json']
records=[]
for row in terminal['steps']:
    before_state,after_state=Path(row['before_state']),Path(row['evaluation'])
    before,after=read(before_state/'endpoint_vector.json'),read(after_state/'endpoint_vector.json')
    for mode in ['strict','endpoint_vector']:
        result=decide(mode,before,after,row['after_resources'],cpd_limit_s=terminal['CPD_before_ns']*1e-9,
            resource_limits=limits,native_valid=True,transaction_complete=True)
        if mode=='strict':
            prior=resource_decide('timing_under_resources',before,after,row['before_resources'],row['after_resources'],
                cpd_limit_s=terminal['CPD_before_ns']*1e-9,resource_limits=limits,
                native_valid=True,transaction_complete=True,resource_objectives=('wirelength',))
            assert result['accepted']==prior['accepted'] is True
        records.append(dict(before_state=str(before_state),after_state=str(after_state),policy=mode,
                            accepted=result['accepted'],reason=result['reason']))
    files.extend([before_state/'endpoint_vector.json',after_state/'endpoint_vector.json'])
native=read(D/'BNN_extended_native_menu_01.json');after_state=Path(native['final_state'])
root=D/'native_extra_opportunity_bnn_01/A0_observation'
before,after=read(root/'endpoint_vector.json'),read(after_state/'endpoint_vector.json')
axes=native['resources'];caps=dict(wirelength=2061627,SB_pairs=94,CB_sources=5062)
strict=decide('strict',before,after,axes,cpd_limit_s=before['cpd_s'],resource_limits=caps,native_valid=True,transaction_complete=True)
secondary=decide('endpoint_vector',before,after,axes,cpd_limit_s=before['cpd_s'],resource_limits=caps,native_valid=True,transaction_complete=True)
assert not strict['accepted'] and secondary['accepted']
records.append(dict(before_state=str(root),after_state=str(after_state),
    strict_rejected_secondary_accepted=True,comparison=secondary['timing_decision']['comparison'],
    qualification='Existing legal multi-connection trajectory endpoint, not a new automatic single-step selector result or proof that these flat accepts enable later CPD gain.'))
files.extend([D/'BNN_extended_native_menu_01.json',root/'endpoint_vector.json',after_state/'endpoint_vector.json'])
vector=dict(cpd_s=1e-8,endpoint_ids=[[1,2,'A'],[3,4,'B']],constraints_sha256='fixed',
    setup={'A':-1e-8,'B':-8e-9},hold={'A':1e-9,'B':1e-9})
axes=dict(wirelength=100,SB_pairs=2,CB_sources=3);negative=[]
for kind in ['one_ulp_CPD_regression','wire_over_cap','changed_constraints','changed_endpoint_set',
             'setup_component_regression','hold_violation','native_not_valid','incomplete_transaction','already_visited']:
    candidate=copy.deepcopy(vector);candidate['setup']['B']+=1e-10;res=dict(axes)
    native_ok=complete=True;visited=False
    if kind=='one_ulp_CPD_regression':candidate['cpd_s']=math.nextafter(vector['cpd_s'],math.inf)
    elif kind=='wire_over_cap':res['wirelength']+=1
    elif kind=='changed_constraints':candidate['constraints_sha256']='different'
    elif kind=='changed_endpoint_set':candidate['endpoint_ids'].pop()
    elif kind=='setup_component_regression':candidate['setup']['A']=math.nextafter(vector['setup']['A'],-math.inf)
    elif kind=='hold_violation':candidate['hold']['A']=-1e-20
    elif kind=='native_not_valid':native_ok=False
    elif kind=='incomplete_transaction':complete=False
    elif kind=='already_visited':visited=True
    result=decide('endpoint_vector',vector,candidate,res,cpd_limit_s=vector['cpd_s'],resource_limits=axes,
        native_valid=native_ok,transaction_complete=complete,already_visited=visited)
    assert not result['accepted'],kind
    negative.append(kind)
write(out,dict(passed=True,actual_recorded_cases=records,negative_controls=negative,
    strict_rule_matches_existing_fixed_resource_strict_acceptance=True,
    flat_native_endpoint_rejected_by_strict_accepted_by_secondary=True,
    native_calls=0,route_calls=0,source_sha256={str(p):sha(p) for p in files},
    qualification='Exact policy validation on existing legal states, not a new route experiment or automatic low-resource timing result. Fixed endpoint/clock-domain/SDC and full-precision comparisons; no rolling tolerance.'))
print(dict(passed=True,actual_cases=len(records),negative_controls=negative),flush=True)
