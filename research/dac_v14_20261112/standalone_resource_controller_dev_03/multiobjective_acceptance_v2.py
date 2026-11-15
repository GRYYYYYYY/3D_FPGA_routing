"""Exact fixed-budget policies for subsequent independent repair batches.

Budgets are immutable design parameters anchored at batch registration, never
updated after a transition. Intermediate transaction steps do not call commit.
"""
import math
from endpoint_timing_policy import compare

RESOURCE_KEYS = ('wirelength', 'SB_pairs', 'CB_sources')


def decide(mode, before_vector, after_vector, before_resources, after_resources,
           *, cpd_limit_s, resource_limits, native_valid, transaction_complete,
           already_visited=False, resource_objectives=RESOURCE_KEYS):
    assert mode in ('timing_under_resources', 'resources_under_timing')
    assert math.isfinite(cpd_limit_s) and cpd_limit_s > 0
    assert set(resource_limits) == set(RESOURCE_KEYS)
    for values in (before_resources, after_resources, resource_limits):
        assert all(isinstance(values[k], int) and not isinstance(values[k], bool) and values[k] >= 0
                   for k in RESOURCE_KEYS)
    assert resource_objectives and set(resource_objectives) <= set(RESOURCE_KEYS)
    evidence = compare(before_vector, after_vector)
    reason = None
    if not transaction_complete:
        reason = 'Intermediate transaction only; final candidate not ready for commit'
    elif not native_valid:
        reason = 'Complete native FULL/STA and physical checks required'
    elif already_visited:
        reason = 'Identical state already evaluated'
    elif not evidence['compatible']:
        reason = evidence['reason']
    elif evidence['hold_violation_regressions']:
        reason = 'Increased hold violation'
    elif after_vector['cpd_s'] > cpd_limit_s:
        reason = 'Fixed registered CPD budget exceeded; no tolerance or rolling anchor'
    elif any(after_resources[k] > resource_limits[k] for k in RESOURCE_KEYS):
        reason = 'Fixed registered resource budget exceeded'
    elif mode == 'timing_under_resources' and not evidence['cpd_strictly_better']:
        reason = 'No exact CPD reduction within resource limits'
    elif mode == 'resources_under_timing' and (
            any(after_resources[k] > before_resources[k] for k in resource_objectives)
            or not any(after_resources[k] < before_resources[k] for k in resource_objectives)):
        reason = 'No resource Pareto improvement within fixed CPD budget'
    return dict(accepted=reason is None, reason=reason or 'Exact fixed-budget conditions satisfied',
                mode=mode, resource_objectives=list(resource_objectives), cpd_limit_s=cpd_limit_s, resource_limits=resource_limits,
                endpoint_comparison=evidence,
                resource_delta={k:after_resources[k]-before_resources[k] for k in RESOURCE_KEYS},
                qualification='This transition policy is separate from final multiobjective archive retention. '
                'A final non-dominated tradeoff may be archived even when this particular resource-Pareto transition rejects it. '
                'No endpoint-vector non-regression requirement is inferred beyond configured CPD and hold bounds.')
