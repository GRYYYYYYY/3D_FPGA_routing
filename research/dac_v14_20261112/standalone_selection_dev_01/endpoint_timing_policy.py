"""Full-precision fixed-endpoint timing vectors and non-accumulating acceptance."""
import json
import math
from pathlib import Path
from retained_prefix_workflow import sha


def load(path):
    path = Path(path)
    records = [json.loads(line) for line in path.open()]
    assert records[-1]['type'] == 'complete'
    endpoints = [r for r in records if r['type'] == 'endpoint']
    assert len(endpoints) == records[-1]['endpoint_rows']
    metrics = [r for r in records if r['type'] == 'timing_metrics']
    assert len(metrics) == 1
    result = dict(cpd_s=metrics[0]['least_slack_CPD_s'], metrics=metrics[0], endpoint_ids=[], setup={}, hold={},
                  constraints_sha256=sha(str(path) + '.constraints.echo'), trace_sha256=sha(path))
    for row in endpoints:
        identity = (row['node'], row['atom_pin'], row['name'])
        result['endpoint_ids'].append(identity)
        for kind in ['setup', 'hold']:
            for tag in row[kind + '_tags']:
                key = json.dumps([*identity, tag['launch'], tag['capture']], separators=(',', ':'))
                value = tag['slack_s']
                if key in result[kind]:
                    previous = result[kind][key]
                    assert isinstance(value, (int, float)) and isinstance(previous, (int, float))
                    value = min(value, previous)
                result[kind][key] = value
    assert len(result['endpoint_ids']) == len(set(result['endpoint_ids']))
    result['endpoint_ids'].sort(key=lambda key: key[0])
    assert isinstance(result['cpd_s'], (int, float)) and math.isfinite(result['cpd_s'])
    return result


def compare(before, after):
    """Exact native-number comparisons; no epsilon is permitted for acceptance."""
    compatible = ([tuple(x) for x in before['endpoint_ids']] == [tuple(x) for x in after['endpoint_ids']]
                  and before['constraints_sha256'] == after['constraints_sha256']
                  and before['setup'].keys() == after['setup'].keys()
                  and before['hold'].keys() == after['hold'].keys())
    if not compatible:
        return dict(compatible=False, reason='Endpoint/domain/constraint identity changed')
    changed, setup_better, setup_worse, hold_worse = [], 0, 0, 0
    for kind in ['setup', 'hold']:
        for key, old in before[kind].items():
            new = after[kind][key]
            if not isinstance(old, (int, float)) or not isinstance(new, (int, float)):
                if old != new or old == 'nan':
                    return dict(compatible=False, reason='Nonfinite or unconstrained status changed/unknown', key=key)
                continue
            assert math.isfinite(old) and math.isfinite(new)
            if old != new:
                changed.append(dict(kind=kind, endpoint_domain=key, before_s=old, after_s=new, delta_s=new-old))
            if kind == 'setup':
                setup_better += new > old
                setup_worse += new < old
            else:
                # Positive hold margin may decrease without violating hold.
                hold_worse += min(new, 0.) < min(old, 0.)
    return dict(compatible=True, cpd_before_s=before['cpd_s'], cpd_after_s=after['cpd_s'],
                cpd_strictly_better=after['cpd_s'] < before['cpd_s'], cpd_nonworse=after['cpd_s'] <= before['cpd_s'],
                setup_improved=setup_better, setup_regressed=setup_worse, hold_violation_regressions=hold_worse,
                setup_components=len(before['setup']), hold_components=len(before['hold']), changes=changed)


def decide(policy, before, after, native_valid, already_visited=False):
    """Separate strict-CPD and setup-vector Pareto policies with hold guards."""
    assert policy in ['strict', 'endpoint_vector']
    evidence = compare(before, after)
    if not native_valid:
        reason = 'Native FULL/physical checks incomplete or failed'
    elif already_visited:
        reason = 'Candidate state already evaluated; no repeated transition'
    elif not evidence['compatible']:
        reason = evidence['reason']
    elif evidence['hold_violation_regressions']:
        reason = 'Increased endpoint/domain hold violation'
    elif policy == 'strict' and not evidence['cpd_strictly_better']:
        reason = 'No full-precision strict CPD improvement'
    elif policy == 'endpoint_vector' and not evidence['cpd_nonworse']:
        reason = 'Full-precision CPD regression'
    elif policy == 'endpoint_vector' and evidence['setup_regressed']:
        reason = 'Setup endpoint/domain vector has regressions'
    elif policy == 'endpoint_vector' and not evidence['setup_improved']:
        reason = 'Setup endpoint/domain vector unchanged'
    else:
        return dict(accepted=True, policy=policy, reason='Exact policy conditions satisfied', comparison=evidence)
    return dict(accepted=False, policy=policy, reason=reason, comparison=evidence)
