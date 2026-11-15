"""Exact timing progress with immutable resource and CPD envelopes."""
import math
from endpoint_timing_policy_streaming_v2 import decide as timing_decide


def decide(policy, before, after, new_resources, *, cpd_limit_s, resource_limits,
           native_valid, transaction_complete, already_visited=False):
    assert policy in ['strict', 'endpoint_vector']
    assert isinstance(cpd_limit_s,(int,float)) and math.isfinite(cpd_limit_s) and cpd_limit_s>=0
    assert set(resource_limits)==set(new_resources)=={'wirelength','SB_pairs','CB_sources'}
    assert all(type(v) is int and v>=0 for v in [*resource_limits.values(),*new_resources.values()])
    evidence=timing_decide(policy,before,after,native_valid and transaction_complete,already_visited)
    checks=dict(current_CPD_inside_original_envelope=before['cpd_s']<=cpd_limit_s,
        candidate_CPD_inside_original_envelope=after['cpd_s']<=cpd_limit_s,
        fixed_resource_limits=all(new_resources[k]<=v for k,v in resource_limits.items()),
        timing_transition=evidence['accepted'])
    if not checks['current_CPD_inside_original_envelope']:
        reason='Current state is outside the original CPD envelope'
    elif not checks['candidate_CPD_inside_original_envelope']:
        reason='Candidate exceeds the original full-precision CPD envelope'
    elif not checks['fixed_resource_limits']:
        reason='Candidate exceeds an immutable absolute resource limit'
    else:reason=evidence['reason']
    return dict(accepted=all(checks.values()),policy=policy+'_under_explicit_resources',reason=reason,
        checks=checks,timing_decision=evidence,cpd_limit_s=cpd_limit_s,
        fixed_resource_limits=dict(resource_limits),
        vector_definition='All fixed endpoint (timing node, atom pin, name, launch clock, capture clock) setup tags; exact native numbers. Hold violation components must not worsen. Positive hold margin may decrease without violating hold.',
        numerical_comparison='Exact <, <= and component comparisons; no epsilon, rounded report values, rolling budget or accumulated tolerance.')
