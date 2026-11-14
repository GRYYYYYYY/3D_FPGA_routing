#!/usr/bin/env python3
"""Bind immutable accepted steps while the own-current timing controller continues."""
import math
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from run_native_scope_policy_v4 import run_dir
from endpoint_timing_policy import compare

b = D / 'resource_first_timing_dev_01'
actor = b / 'timing'
registration = read(actor / 'registration.json')
assert all(sha(p) == h for p, h in registration['source_sha256'].items())
steps = read(actor / 'steps.json')
assert steps
first = steps[0]
before = Path(first['before_state'])
after = Path(first['evaluation'])
assert first['accepted'] and first['policy_accepted']
assert read(after / 'completion.json')['passed']
assert read(run_dir(after) / 'manifest.json')['metrics']['native_full_check_passed']
assert read(run_dir(after) / 'independent_audit.json')['audit']['passed']
limits = read(b / 'absolute_limits.json')
assert all(first['after_resources'][key] <= value for key, value in limits.items())
av, bv = read(before / 'endpoint_vector.json'), read(after / 'endpoint_vector.json')
comparison = compare(av, bv)
assert comparison['compatible'] and comparison['cpd_strictly_better'] and comparison['hold_violation_regressions'] == 0
old_cone = read(actor / 'round_000/feedback/cone.json')
new_cone = read(actor / 'round_001/feedback/cone.json')
assert old_cone['source_state'] == str(before) and new_cone['source_state'] == str(after)
ids = lambda cone: {(r['net'], r['pin']) for r in cone['routed_connections']}
finite = {k: v for k, v in av['setup'].items() if isinstance(v, (int, float)) and math.isfinite(v)}
worst = min(finite.values())
near = {k for k, v in finite.items() if v <= worst + .05 * av['cpd_s']}
files = [Path(__file__).resolve(), actor / 'registration.json', before / 'completion.json', before / 'endpoint_vector.json',
         after / 'completion.json', after / 'endpoint_vector.json', run_dir(after) / 'manifest.json',
         run_dir(after) / 'independent_audit.json', b / 'absolute_limits.json',
         actor / 'round_000/feedback/cone.json', actor / 'round_001/feedback/cone.json']
write(D / 'resource_first_timing_prefix_01.json', dict(passed=True, immutable_accepted_prefix_only=True,
      controller_still_active_not_trajectory_completion=True, accepted_step=first,
      CPD_before_ns=av['cpd_s'] * 1e9, CPD_after_ns=bv['cpd_s'] * 1e9, comparison=comparison,
      fixed_absolute_resources=limits, actual_resources=first['after_resources'],
      selected_endpoint_identities_unchanged=[r['identity'] for r in old_cone['selected_endpoints']] == [r['identity'] for r in new_cone['selected_endpoints']],
      old_critical_connections=sorted(ids(old_cone)), new_critical_connections=sorted(ids(new_cone)),
      critical_connections_added=sorted(ids(new_cone) - ids(old_cone)), critical_connections_removed=sorted(ids(old_cone) - ids(new_cone)),
      fixed_source_near_band=dict(rule='Source setup slack <= source worst slack +0.05*source CPD; diagnostic only',
          components=len(near), improved=sum(bv['setup'][k] > av['setup'][k] for k in near), regressed=sum(bv['setup'][k] < av['setup'][k] for k in near)),
      native_calls=0, route_calls=0, source_sha256={str(p): sha(p) for p in files},
      qualification='A real accepted legal timing step under tighter post-resource79SB/5061CB and original-root wire envelope, using its own refreshed current STA. Worst endpoint identity stays the same while tied critical structure expands; no endpoint-migration or final phase-commutation claim. This intermediate route is not a new global quality-frontier point, and full algorithm/cold timing remains unknown.'))
print(dict(CPD_before_ns=av['cpd_s'] * 1e9, CPD_after_ns=bv['cpd_s'] * 1e9,
           resources=first['after_resources'], critical_connections_added=sorted(ids(new_cone) - ids(old_cone))), flush=True)
