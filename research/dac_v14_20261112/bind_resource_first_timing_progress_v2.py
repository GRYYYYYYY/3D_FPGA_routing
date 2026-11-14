#!/usr/bin/env python3
"""Immutable first-two-commit evidence from the still independently running trajectory."""
import math
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from run_native_scope_policy_v4 import run_dir
from endpoint_timing_policy_streaming_v2 import compare
from pareto_archive_dimensions import dominates

out = D / 'resource_first_timing_prefix_02.json'
assert not out.exists()
source = D / 'resource_first_timing_resume_01/timing'
steps = [row for row in read(source / 'steps.json') if row['accepted']][:2]
assert len(steps) == 2
limits = read(D / 'resource_first_timing_dev_01/absolute_limits.json')
files = [Path(__file__).resolve(), D / 'endpoint_timing_policy_streaming_v2.py',
         D / 'resource_first_timing_dev_01/absolute_limits.json']
records = []
for step in steps:
    before, after = Path(step['before_state']), Path(step['evaluation'])
    tx = after.parent
    for state in [before, after]:
        assert read(state / 'completion.json')['passed']
        assert read(run_dir(state) / 'independent_audit.json')['audit']['passed']
        files += [state / 'completion.json', state / 'endpoint_vector.json', run_dir(state) / 'manifest.json', run_dir(state) / 'independent_audit.json']
    assert read(after / 'input_seal.json')['passed']
    manifest = read(run_dir(after) / 'manifest.json')
    assert manifest['metrics']['native_full_check_passed']
    av, bv = read(before / 'endpoint_vector.json'), read(after / 'endpoint_vector.json')
    comparison = compare(av, bv)
    assert comparison['compatible'] and comparison['cpd_strictly_better'] and comparison['hold_violation_regressions'] == 0
    assert all(step['after_resources'][key] <= value for key, value in limits.items())
    current = read(tx / 'current_group_successor_cone.json')
    assert Path(current['source_state']) == after
    files += [tx / 'registration.json', tx / 'current_group_audit/analysis.json',
              tx / 'current_group_decisions.json', tx / 'current_group_successor_cone.json', after / 'input_seal.json']
    prior_files = list(before.parent.glob('*_successor_cone.json'))
    prior = next((read(path) for path in prior_files if Path(read(path)['source_state']) == before), None)
    if prior is None:
        path = D / 'resource_first_timing_dev_01/timing/round_000/feedback/cone.json'
        prior = read(path)
        assert Path(prior['source_state']) == before
        files.append(path)
    else:
        files.extend(path for path in prior_files if Path(read(path)['source_state']) == before)
    identities = lambda cone: [r['identity'] for r in cone['selected_endpoints']]
    connections = lambda cone: {(r['net'], r['pin']) for r in cone['routed_connections']}
    finite = {k: v for k, v in av['setup'].items() if isinstance(v, (int, float)) and math.isfinite(v)}
    worst = min(finite.values())
    near = {k for k, v in finite.items() if v <= worst + .05 * av['cpd_s']}
    records.append(dict(accepted_record=step, comparison=comparison,
        selected_endpoint_before=identities(prior), selected_endpoint_after=identities(current),
        critical_connections_before=sorted(connections(prior)), critical_connections_after=sorted(connections(current)),
        connections_added=sorted(connections(current) - connections(prior)),
        connections_removed=sorted(connections(prior) - connections(current)),
        transaction_queries=read(tx / 'registration.json')['roles']['current_group']['queries'],
        fixed_source_near_band=dict(rule='Source slack <= source worst slack +0.05*sourceCPD; diagnostic only',
            components=len(near), improved=sum(bv['setup'][k] > av['setup'][k] for k in near),
            regressed=sum(bv['setup'][k] < av['setup'][k] for k in near))))
archive = read(D / 'multiobjective_archive_47/points.json')
origin = next(p for p in archive if p.get('state') == steps[0]['before_state'])
new = dict(origin, CPD_ns=steps[-1]['after_CPD_s'] * 1e9, CPD_interval_ns=[steps[-1]['after_CPD_s'] * 1e9] * 2,
           **steps[-1]['after_resources'], route_body_sha256='new_observation_no_same_route_shortcut', binary_sha256=sha(manifest['command'][0]))
strong = [p['id'] for p in archive if p['arm'] in ['A0', 'R1'] and p['quality_cohort'] == origin['quality_cohort'] and dominates(p, new)]
files += [D / 'multiobjective_archive_47/points.json', D / 'pareto_archive_dimensions.py']
write(out, dict(passed=True, immutable_accepted_prefix_only=True, completed_trajectory_claim=False,
    accepted_steps=2, records=records, CPD_initial_ns=steps[0]['before_CPD_s'] * 1e9,
    CPD_latest_ns=steps[-1]['after_CPD_s'] * 1e9, actual_resources=steps[-1]['after_resources'],
    fixed_absolute_resources=limits, strong_A0_R1_quality_dominated_by=strong,
    complete_single_configuration_algorithm_seconds=None, native_calls=0, route_calls=0,
    source_sha256={str(path): sha(path) for path in files},
    qualification='Two real legal current-STA timing accepts under preserved absolute caps, including independently sealed failed/recovery provenance. Second commit improves11setup components with0regressions and reduces wire4. No full trajectory or phase-order commutation claim. No historical time is attached. Full archive may have other dominating repair states; absence of strong-baseline domination is not algorithm superiority.'))
print(dict(CPD_ns=new['CPD_ns'], resources=steps[-1]['after_resources'],
           endpoint_changes=[r['selected_endpoint_before'] != r['selected_endpoint_after'] for r in records],
           connections=[(len(r['critical_connections_before']), len(r['critical_connections_after'])) for r in records],
           baseline_dominators=len(strong)), flush=True)
