#!/usr/bin/env python3
"""Reconcile actual selective-trigger receipts with native refreshes and guards."""
from pathlib import Path
import hashlib, json, re, sys

B = Path(sys.argv[1])
assert json.loads((B / 'input_seal.json').read_text())['passed']
summaries = {}
for arm in ['V', 'B']:
    rd = B / 'runs' / f'eltwise_layer_{arm}'
    manifest = json.loads((rd / 'manifest.json').read_text())
    assert manifest['metrics']['native_full_check_passed']
    assert json.loads((rd / 'independent_audit.json').read_text())['audit']['passed']
    assert json.loads((rd / 'final_guide_audit.json').read_text())['passed']
    if arm == 'V':
        assert json.loads((rd / 'optimization_equivalence.json').read_text())['passed']
    cooldown = 3  # Immutable candidate's internal setting; not an environment option.
    triggers, refreshes, counters = {}, {}, []
    for line in (rd / 'stdout.log').read_text().splitlines():
        prefix = line.split(' ', 1)[0]
        if prefix not in ['H3D_REFRESH_TRIGGER', 'H3D_REFRESH', 'H3D_ELIGIBILITY_TRIGGER']:
            continue
        values = dict(re.findall(r'(\w+)=([^ ]+)', line))
        if prefix == 'H3D_ELIGIBILITY_TRIGGER':
            counters.append({k: int(v) for k, v in values.items()})
            continue
        key = int(values['net']), int(values['iter'])
        target = triggers if prefix == 'H3D_REFRESH_TRIGGER' else refreshes
        assert key not in target
        target[key] = values
    assert triggers.keys() == refreshes.keys() and counters
    for old, new in zip(counters, counters[1:]):
        assert old['enabled'] == new['enabled']
        assert all(new[k] >= old[k] for k in ['checks_newly_missing', 'opportunities_after_cooldown', 'extra_attempts'])
    extra = []
    for key, values in triggers.items():
        v = {k: int(x) for k, x in values.items()}
        assert v['iter'] - v['last_attempt'] >= cooldown
        assert v['eligibility_enabled'] == (arm == 'B')
        assert v['extra_attempt'] == (not v['original_due'])
        if v['extra_attempt']:
            assert v['newly_missing'] > 0 and v['eligibility_enabled']
            extra.append(dict(**v, accepted=int(refreshes[key]['accepted'])))
    c = counters[-1]  # Cumulative statistics are emitted after every iteration.
    assert c['enabled'] == (arm == 'B')
    assert c['extra_attempts'] == len(extra)
    assert c['opportunities_after_cooldown'] >= len(extra)
    if arm == 'B':
        assert c['opportunities_after_cooldown'] == len(extra)
    summaries[arm] = dict(counters=c, refresh_attempts=len(triggers),
                          extra_attempts=extra,
                          log_sha256=hashlib.sha256((rd / 'stdout.log').read_bytes()).hexdigest())
result = dict(passed=True, arms=summaries,
              scope='Actual refresh events obey registered cooldown and gate. V reproduces old U. Opportunity counts are repeated native-reroute checks, not unique pins. Does not establish global quality benefit.',
              verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(B / 'trigger_validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({a: x['counters'] for a, x in summaries.items()}, indent=2))
