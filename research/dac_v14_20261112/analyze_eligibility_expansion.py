#!/usr/bin/env python3
"""Audit gate and prior-cause evidence for the registered eligibility transfer."""
from pathlib import Path
import collections, hashlib, json, math, re, struct, sys

B = Path(sys.argv[1])
reg = json.loads((B / 'registration.json').read_text())
assert json.loads((B / 'input_seal.json').read_text())['passed']
f32 = lambda value: struct.unpack('f', struct.pack('f', float(value)))[0]
results = {}
for circuit in reg['circuits']:
    rd = B / 'runs' / f'{circuit}_B'
    m = json.loads((rd / 'manifest.json').read_text())
    if m['status'] != 'completed':
        results[circuit] = dict(status=m['status'], quality_evidence=False)
        continue
    assert m['metrics']['native_full_check_passed']
    assert json.loads((rd / 'independent_audit.json').read_text())['audit']['passed']
    assert json.loads((rd / 'final_guide_audit.json').read_text())['passed']
    threshold = f32(m['environment']['VPR_H3D_MIN_CRITICALITY'])
    triggers, reasons, refreshes, totals = {}, {}, {}, []
    pins = collections.defaultdict(list)
    for line in (rd / 'stdout.log').read_text().splitlines():
        prefix = line.split(' ', 1)[0]
        if prefix not in ['H3D_REFRESH_TRIGGER', 'H3D_PRIOR_REASON', 'H3D_PRIOR_PIN', 'H3D_REFRESH', 'H3D_ELIGIBILITY_TRIGGER']:
            continue
        v = dict(re.findall(r'(\w+)=([^ ]+)', line))
        if prefix == 'H3D_ELIGIBILITY_TRIGGER':
            totals.append({k: int(x) for k, x in v.items()})
            continue
        key = int(v['net']), int(v['iter'])
        if prefix == 'H3D_PRIOR_PIN':
            assert v['reason'] == 'empty' and f32(v['new_criticality']) >= threshold
            assert int(v['newly_eligible']) == (f32(v['old_criticality']) < threshold)
            pins[key].append(v)
        else:
            dest = {'H3D_REFRESH_TRIGGER': triggers, 'H3D_PRIOR_REASON': reasons, 'H3D_REFRESH': refreshes}[prefix]
            assert key not in dest
            dest[key] = v
    assert totals and triggers.keys() == reasons.keys() == refreshes.keys()
    assert set(pins) <= reasons.keys()
    accepted_nonfinite, newly_only, extra, extra_accepted = 0, 0, 0, 0
    for key, t in triggers.items():
        t = {k: int(x) for k, x in t.items()}
        assert t['eligibility_enabled'] == 1 and t['iter'] - t['last_attempt'] >= 3
        assert t['extra_attempt'] == (not t['original_due'])
        if t['extra_attempt']:
            assert t['newly_missing'] > 0
            extra += 1
            extra_accepted += int(refreshes[key]['accepted'])
        r = {k: float(x) if k.endswith('_cost') else int(x) for k, x in reasons[key].items()}
        other = sum(r[k] for k in ['multiple', 'outside', 'branch_missing', 'branch_nonfinite', 'opening_nonfinite'])
        assert r['empty'] == r['empty_newly_eligible'] + r['empty_previously_eligible'] == len(pins[key])
        assert r['empty_newly_eligible'] == sum(int(p['newly_eligible']) for p in pins[key])
        assert r['accepted'] == int(refreshes[key]['accepted'])
        for name in ['old_cost', 'new_cost']:
            assert r[name] == float(refreshes[key][name])
        if r['table']:
            assert r['leaves'] == r['pairs'] + r['empty'] + r['multiple'] + r['outside']
            assert r['branch_missing'] + r['branch_nonfinite'] <= r['pairs']
            assert r['opening_nonfinite'] <= r['pairs']
            assert (not math.isfinite(r['old_cost'])) == bool(r['empty'] + other)
        if r['accepted'] and not r['clear'] and not math.isfinite(r['old_cost']):
            accepted_nonfinite += 1
            newly_only += bool(r['empty_newly_eligible']) and r['empty_previously_eligible'] == 0 and other == 0
    assert totals[-1]['extra_attempts'] == totals[-1]['opportunities_after_cooldown'] == extra
    assert all(t['enabled'] == 1 for t in totals)
    for a, b in zip(totals, totals[1:]):
        assert all(b[k] >= a[k] for k in ['checks_newly_missing', 'extra_attempts', 'opportunities_after_cooldown'])
    bound = [rd / f for f in ['stdout.log', 'manifest.json', 'independent_audit.json', 'final_guide_audit.json']]
    results[circuit] = dict(status='legal', attempts=len(triggers), counters=totals[-1],
                            extra_accepted=extra_accepted, accepted_nonfinite=accepted_nonfinite,
                            nonfinite_explained_only_by_new_eligibility=newly_only,
                            source_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in bound})
result = dict(passed=True, circuits=results,
              scope='Native-selected reroute gates, cooldown and prior-cause accounting; cumulative checks are not unique nets. No CPD causality inferred from event count. Failed runs retained without legal QoR interpretation.',
              script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              seal_sha256=hashlib.sha256((B / 'input_seal.json').read_bytes()).hexdigest())
(B / 'eligibility_mechanisms.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({c: {k: v for k, v in x.items() if k != 'source_sha256'} for c, x in results.items()}, indent=2))
