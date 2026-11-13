#!/usr/bin/env python3
"""Audit decision-neutral local-margin traces; never interpret them as DP min-marginals."""
from pathlib import Path
import collections
import hashlib
import json
import math
import re
import statistics
import sys

B = Path(sys.argv[1]).resolve()
assert json.loads((B/'input_seal.json').read_text())['passed']
reg = json.loads((B/'registration.json').read_text())
results = {}
bindings = {}

def read(path):
    data = path.read_bytes()
    bindings[str(path)] = hashlib.sha256(data).hexdigest()
    return json.loads(data)

def counters(lines):
    out = {}
    for prefix in ['H3D_PLAN ', 'H3D_DELAY ', 'H3D_FEEDBACK ', 'H3D_UPDATE_PINS_SUMMARY ', 'H3D_FINAL ']:
        records = [dict(re.findall(r'(\w+)=(\S+)', line)) for line in lines if line.startswith(prefix)]
        assert records
        out[prefix.strip()] = {k: v for k, v in records[-1].items() if not k.endswith('_seconds')}
    return out

def summarize(rows):
    finite = [r for r in rows if r['alternative'] is not None]
    margins = [(r['alternative']-r['chosen'])/max(1., abs(r['chosen']), abs(r['alternative'])) for r in finite]
    return dict(events=len(rows), distinct_net_pins=len({(r['net'], r['pin']) for r in rows}),
                finite_alternative=len(finite), no_alternative=len(rows)-len(finite),
                local_worse=sum(v < -1e-12 for v in margins), local_tie=sum(abs(v) <= 1e-12 for v in margins),
                local_better=sum(v > 1e-12 for v in margins),
                normalized_margin_median=statistics.median(margins) if margins else None,
                positive_margin_at_most_5pct=sum(1e-12 < v <= .05 for v in margins),
                both_measured=sum(r['source_measured'] and r['sink_measured'] for r in rows),
                coassigned_multiple=sum(r['users'] > 1 for r in rows))

for circuit in reg['circuits']:
    refs = read(B/f'{circuit}_references.json')
    for arm in reg['arms']:
        rd = B/'runs'/f'{circuit}_{arm}'
        m = read(rd/'manifest.json')
        if m['status'] != 'completed':
            results[f'{circuit}_{arm}'] = dict(status=m['status'])
            continue
        prior = Path(refs['Tf1' if arm == 'T2' else 'W1']['path'])
        assert read(prior.parent.parent/'input_seal.json')['passed']
        assert m['metrics']['native_full_check_passed']
        assert read(rd/'independent_audit.json')['audit']['passed']
        assert read(rd/'final_guide_audit.json')['passed']
        assert read(rd/'margin_trace_equivalence.json')['passed']
        assert m['environment']['VPR_H3D_TRACE_GUIDE_MARGIN'] == '1'
        assert m['environment']['VPR_H3D_MISS_WEIGHT'] == ('2' if arm == 'T2' else '1')
        lines = (rd/'stdout.log').read_text().splitlines()
        bindings[str(rd/'stdout.log')] = hashlib.sha256((rd/'stdout.log').read_bytes()).hexdigest()
        assert counters(lines) == counters((prior/'stdout.log').read_text().splitlines())
        rows = []
        for line in lines:
            if not line.startswith('H3D_GUIDE_MARGIN '): continue
            r = dict(re.findall(r'(\w+)=(\S+)', line))
            for k in ['net','pin','refresh','independent','candidate','users','alternatives','source_measured','sink_measured']:
                r[k] = int(r[k])
            for k in ['opening','branch','chosen','alternative','criticality']: r[k] = float(r[k])
            assert math.isfinite(r['chosen']) and math.isclose(r['opening']+r['branch'], r['chosen'], rel_tol=1e-12, abs_tol=1e-12)
            assert (r['alternatives'] > 0) == math.isfinite(r['alternative'])
            assert r['users'] >= 1 and r['independent'] == 0
            assert r['refresh'] in [0,1] and r['source_measured'] in [0,1] and r['sink_measured'] in [0,1]
            if not math.isfinite(r['alternative']): r['alternative'] = None
            rows.append(r)
        assert rows
        results[f'{circuit}_{arm}'] = dict(status='legal_exact_reproduction', reference=str(prior),
                 all=summarize(rows), initial=summarize([r for r in rows if not r['refresh']]),
                 accepted_refresh=summarize([r for r in rows if r['refresh']]),
                 single_user=summarize([r for r in rows if r['users'] == 1]),
                 coassigned=summarize([r for r in rows if r['users'] > 1]), rows=rows)

out = dict(passed=all(r['status']=='legal_exact_reproduction' for r in results.values()),
           scope='Repeated initial/accepted finite-table assignment events, not independent samples. '
           'Leaf-local opening+branch cost compares selected with best other finite table candidate; '
           'it is not a shared-DP min-marginal or calibrated physical-delay confidence. Coassignment '
           'does not identify DP group or actual sharing. Highfanout bypass and rejected proposals '
           'not covered. All original non-time final counters and complete decisions/routes reproduced.',
           results=results, input_sha256=bindings, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(B/'guide_margin_mechanisms.json').write_text(json.dumps(out, indent=2, allow_nan=False)+'\n')
print(json.dumps({k:{a:b for a,b in v.items() if a!='rows'} for k,v in results.items()}, indent=2))
