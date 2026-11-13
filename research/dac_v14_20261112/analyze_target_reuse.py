#!/usr/bin/env python3
"""Summarize audited target reuse without equating cache size with selected coverage."""
from pathlib import Path
import hashlib, json, re, sys

B = Path(sys.argv[1])
reg = json.loads((B / 'registration.json').read_text())
assert json.loads((B / 'input_seal.json').read_text())['passed']
observations = json.loads((B / 'observations.json').read_text())
results = {}
for circuit in reg['circuits']:
    arms = {}
    for arm in ['Q', 'E']:
        rd = B / 'runs' / f'{circuit}_{arm}'
        m = json.loads((rd / 'manifest.json').read_text())
        if m['status'] != 'completed':
            arms[arm] = dict(status=m['status'])
            continue
        assert m['metrics']['native_full_check_passed']
        assert json.loads((rd / 'independent_audit.json').read_text())['audit']['passed']
        assert json.loads((rd / 'final_guide_audit.json').read_text())['passed']
        env = m['environment']
        assert env['VPR_H3D_TARGET_REUSE'] == ('1' if arm == 'E' else '0')
        assert env['VPR_H3D_DELAY_BUDGET'] == '4096' and env['VPR_H3D_TARGET_QUOTA'] == '256'
        assert env['VPR_H3D_FEEDBACK'] == env['VPR_H3D_TIMING_GUIDE'] == '0'
        lines = (rd / 'stdout.log').read_text().splitlines()
        counters = {}
        for prefix in ['H3D_TARGET_REUSE ', 'H3D_TARGET_DELAY ', 'H3D_SELECTED_DELAY ']:
            matched = [x for x in lines if x.startswith(prefix)]
            assert matched
            counters[prefix.strip()] = {k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', matched[-1])}
        selected = counters['H3D_SELECTED_DELAY']
        assert selected['pins'] == sum(selected[k] for k in ['both', 'source_only', 'sink_only', 'estimated'])
        assert selected['informed_pins'] == selected['pins'] - selected['estimated']
        assert counters['H3D_TARGET_REUSE']['enabled'] == (arm == 'E')
        if arm == 'Q':
            assert counters['H3D_TARGET_REUSE']['inserted'] == 0
        row = next(x for x in observations if x['circuit'] == circuit and x['arm'] == arm)
        arms[arm] = dict(status='legal', counters=counters, metrics=m['metrics'],
                         physical_metrics=row['physical_metrics'], process_seconds=m['wall_seconds'],
                         planning_seconds=float(re.findall(r'planning_seconds=([0-9.]+)', '\n'.join(x for x in lines if x.startswith('H3D_PLAN ')))[-1]),
                         stdout_sha256=hashlib.sha256((rd / 'stdout.log').read_bytes()).hexdigest())
    results[circuit] = arms
output = dict(circuits=results, passed=True,
              scope='Q/E matched quality parameters, endpoint work cap unchanged. Extra cached measurements and work savings do not imply improved selected coverage or CPD. Bidirectional bounds certify reusable costs; this is not a frontier-resumption or adaptive-priority implementation. Development timing only.',
              script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              seal_sha256=hashlib.sha256((B / 'input_seal.json').read_bytes()).hexdigest())
(B / 'query_reuse_mechanisms.json').write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps(results, indent=2))
