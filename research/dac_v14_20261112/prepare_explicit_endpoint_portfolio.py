#!/usr/bin/env python3
"""Independent current-STA actor with an explicitly resource-bounded vector mode."""
from pathlib import Path
from retained_prefix_workflow import D,read,sha,write

source=D/'run_independent_critical_portfolio_v3.py'
target=D/'run_independent_critical_portfolio_v4.py';assert not target.exists()
proof=D/'explicit_envelope_timing_policy_validation_01.json';assert read(proof)['passed']
t=source.read_text()
def rep(old,new):
    global t
    assert t.count(old)==1,old[:100]
    t=t.replace(old,new)
rep('from multiobjective_acceptance_v2 import decide as budget_decide',
    'from multiobjective_acceptance_v2 import decide as budget_decide\nfrom explicit_envelope_timing_policy import decide as envelope_decide')
rep("choices=['strict','endpoint_vector','timing_under_resources','resources_under_timing']",
    "choices=['strict','endpoint_vector','timing_under_resources','resources_under_timing','endpoint_under_resources']")
rep("else:assert a.fixed_limits is None\nanchor=", "else:assert a.fixed_limits is None\nif a.policy=='endpoint_under_resources':assert a.budget_mode=='explicit_absolute', 'Vector envelope policy requires explicit original absolute limits'\nanchor=")
rep("files += [a.fixed_limits.resolve()] if a.fixed_limits else []",
    "assert read(D/'explicit_envelope_timing_policy_validation_01.json')['passed']\nfiles += [D/'explicit_envelope_timing_policy.py',D/'endpoint_timing_policy_streaming_v2.py',D/'explicit_envelope_timing_policy_validation_01.json']\nfiles += [a.fixed_limits.resolve()] if a.fixed_limits else []")
rep("objective='weighted_soft',native_mode=a.native_mode,anchor=anchor,source_sha256=bindings,",
    "objective='weighted_soft',native_mode=a.native_mode,anchor=anchor,source_sha256=bindings,explicit_endpoint_policy='All fixed endpoint/launch/capture setup components nonworse, at least one improves; CPD nonworse at full precision; no increased hold violation; immutable absolute resource and original CPD caps. No tolerance.',")
rep("  write(directory/'policy_decisions.json',d);allowed=",
    "  if a.budget_mode=='explicit_absolute':\n   d['endpoint_under_resources']=envelope_decide('endpoint_vector',before,after,resources(evaluation),cpd_limit_s=anchor['CPD_s'],resource_limits=fixed_limits,native_valid=True,transaction_complete=True)\n  write(directory/'policy_decisions.json',d);allowed=")
compile(t,str(target),'exec');target.write_text(t)
write(D/'explicit_endpoint_portfolio_preparation_01.json',dict(passed=True,
    source=str(source),source_sha256=sha(source),target=str(target),target_sha256=sha(target),
    validation=str(proof),native_calls=0,route_calls=0,actual_integrated_result_pending=True,
    strict_reference_policy='timing_under_resources under explicit_absolute',
    secondary_policy='endpoint_under_resources under same explicit_absolute',
    unchanged_target_selection_native_scope_and_menu=True,
    qualification='Independent actor adds bounded vector acceptance; existing strict fixed-resource rule unchanged. Each divergent trajectory reselects on its own STA. Pure policy validation is not automatic trajectory proof.'))
print(dict(prepared=str(target),actual_integration_pending=True),flush=True)
