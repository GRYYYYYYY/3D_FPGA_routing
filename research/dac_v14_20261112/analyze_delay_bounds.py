#!/usr/bin/env python3
"""Reconcile selected-side bound events with measured-side coverage and audits."""
from pathlib import Path
import collections, hashlib, json, math, re, sys
B = Path(sys.argv[1]); reg = json.loads((B / 'registration.json').read_text())
assert json.loads((B / 'input_seal.json').read_text())['passed']
results = {}
for circuit in reg['circuits']:
    arms = {}
    for arm in reg['arms']:
        rd = B / 'runs' / f'{circuit}_{arm}'; m = json.loads((rd / 'manifest.json').read_text())
        if m['status'] != 'completed': arms[arm] = dict(status=m['status']); continue
        assert m['metrics']['native_full_check_passed']
        assert json.loads((rd / 'independent_audit.json').read_text())['audit']['passed']
        assert json.loads((rd / 'final_guide_audit.json').read_text())['passed']
        eq = rd / 'diagnostic_equivalence.json'
        if eq.exists(): assert json.loads(eq.read_text())['passed']
        lines = (rd / 'stdout.log').read_text().splitlines()
        parse = lambda line: dict(re.findall(r'(\w+)=([^ ]+)', line))
        summary = parse([x for x in lines if x.startswith('H3D_BOUND_SELECTED_SUMMARY ')][-1])
        coverage = parse([x for x in lines if x.startswith('H3D_SELECTED_DELAY ')][-1])
        events = [parse(x) for x in lines if x.startswith('H3D_BOUND_SELECTED ')]
        trace = m['environment'].get('VPR_H3D_TRACE_DELAY_BOUND') == '1'
        clamp = m['environment'].get('VPR_H3D_BOUND_CLAMP', '0') == '1'
        assert m['environment']['VPR_H3D_FEEDBACK'] == '0', 'This audit assumes one static selected event per net/pin/candidate/side'
        assert len(events) == int(summary['below_bound_sides'])
        assert len({(x['net'],x['pin'],x['candidate'],x['side']) for x in events}) == len(events)
        missing = int(coverage['source_only']) + int(coverage['sink_only']) + 2 * int(coverage['estimated'])
        assert int(summary['missing_sides']) == (missing if trace else 0)
        assert 0 <= len(events) <= int(summary['positive_bound_sides']) <= int(summary['missing_sides'])
        gaps = []
        for x in events:
            estimated, lower = float(x['estimate_units']), float(x['lower_units'])
            assert math.isfinite(estimated) and math.isfinite(lower) and 0 <= estimated < lower
            gaps.append(lower-estimated)
            if 'effective_units' in x:
                assert int(x['clamp']) == clamp
                assert float(x['effective_units']) == (max(estimated, lower) if clamp else estimated)
        assert math.isclose(sum(gaps), float(summary['sum_shortfall_units']), rel_tol=1e-12, abs_tol=1e-12)
        arms[arm] = dict(status='legal', trace=trace, clamp=clamp, summary=summary,
                         sides=dict(collections.Counter(x['side'] for x in events)), events=events,
                         metrics=m['metrics'], log_sha256=hashlib.sha256((rd/'stdout.log').read_bytes()).hexdigest())
    results[circuit] = arms
(B/'bound_mechanisms.json').write_text(json.dumps(dict(passed=True, circuits=results,
    scope='Selected raw calibrated missing-side estimates versus certified finite bounds. These are planning-proxy events, not final STA or proof of CPD causality. Under clamp, effective cost is bounded but raw shortfalls remain logged.',
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2)+'\n')
print(json.dumps({c:{a:{k:v for k,v in r.items() if k!='events'} for a,r in x.items()} for c,x in results.items()},indent=2))
