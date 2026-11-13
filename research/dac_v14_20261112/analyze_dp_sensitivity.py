#!/usr/bin/env python3
"""Join exact finite-DP exclusion margins with the neutral local-margin diagnostic."""
from pathlib import Path
import collections
import hashlib
import json
import math
import re
import statistics
import sys

B = Path(sys.argv[1]).resolve()
D = B.parent
assert json.loads((B/'input_seal.json').read_text())['passed']
assert json.loads((B/'guide_margin_mechanisms.json').read_text())['passed']
reg = json.loads((B/'registration.json').read_text())
results = {}
bindings = {}
def bind(p):
    bindings[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return p.read_text()
def parse(line): return dict(re.findall(r'(\w+)=(\S+)', line))
def key(row): return tuple(int(row[k]) for k in ['net','pin','refresh','candidate'])
def summarize(rows):
    finite = [r for r in rows if r['exclusion'] is not None]
    gaps = [r['delta']/max(1., abs(r['base'])) for r in finite]
    return dict(events=len(rows), distinct_net_pins=len({(r['net'],r['pin']) for r in rows}),
                unavailable_alternative=len(rows)-len(finite), finite_alternative=len(finite),
                tied=sum(abs(g)<=1e-12 for g in gaps), positive=sum(g>1e-12 for g in gaps),
                normalized_margin_median=statistics.median(gaps) if gaps else None,
                local_worse=sum(r['local_alternative'] < r['local_chosen']-1e-12*max(1.,abs(r['local_chosen'])) for r in rows),
                local_worse_but_positive_dp_margin=sum(r['local_alternative'] < r['local_chosen']-1e-12*max(1.,abs(r['local_chosen'])) and (r['delta'] is None or r['delta']>1e-12*max(1.,abs(r['base']))) for r in rows))

for c in reg['circuits']:
    for arm in reg['arms']:
        rd = B/'runs'/f'{c}_{arm}'
        m = json.loads(bind(rd/'manifest.json'))
        if m['status'] != 'completed':
            results[f'{c}_{arm}'] = dict(status=m['status']); continue
        assert m['environment']['VPR_H3D_TRACE_DP_SENSITIVITY']=='1'
        lines = bind(rd/'stdout.log').splitlines()
        prior = D/'guide_margin_dev_01/runs'/f'{c}_{arm}'
        oldlines = bind(prior/'stdout.log').splitlines()
        assert [l for l in lines if l.startswith('H3D_GUIDE_MARGIN ')] == [l for l in oldlines if l.startswith('H3D_GUIDE_MARGIN ')]
        assert json.loads(bind(prior.parent.parent/'input_seal.json'))['passed']
        locals_by_key = collections.defaultdict(collections.deque)
        for line in lines:
            if line.startswith('H3D_GUIDE_MARGIN '):
                r = parse(line); locals_by_key[key(r)].append(r)
        rows = []
        times = []
        for line in lines:
            if line.startswith('H3D_DP_SENSITIVITY_TIME '):
                r = parse(line); times.append(dict(seconds=float(r['seconds']), requests=int(r['requests']), leaves=int(r['leaves'])))
            if not line.startswith('H3D_DP_MARGIN '): continue
            r = parse(line); k = key(r); local = locals_by_key[k].popleft()
            r = {n:int(r[n]) for n in ['net','pin','refresh','candidate']} | {n:float(r[n]) for n in ['base','exclusion','delta']}
            assert math.isfinite(r['base']) and r['base'] >= 0.
            if math.isfinite(r['exclusion']):
                assert r['exclusion']+1e-10*max(1.,r['base']) >= r['base']
                assert math.isclose(r['delta'],r['exclusion']-r['base'],rel_tol=1e-10,abs_tol=1e-10)
            else:
                assert r['exclusion']==r['delta']==math.inf
                r['exclusion']=r['delta']=None
            r.update(local_chosen=float(local['chosen']),local_alternative=float(local['alternative']),users=int(local['users']))
            # Current reference tables all have local alternatives; preserve a
            # hard gate rather than emit non-standard JSON infinity silently.
            assert math.isfinite(r['local_alternative'])
            rows.append(r)
        assert rows and all(not q for q in locals_by_key.values())
        assert len(rows)==sum(t['requests'] for t in times)
        assert all(t['seconds']>=0 and t['requests']==t['leaves'] for t in times)
        results[f'{c}_{arm}'] = dict(status='legal_exact_reproduction', all=summarize(rows),
            initial=summarize([r for r in rows if not r['refresh']]),
            accepted_refresh=summarize([r for r in rows if r['refresh']]),
            diagnostic_summary_build_and_exclusion_seconds=sum(t['seconds'] for t in times),
            finite_plan_events=len(times),rows=rows)

out = dict(passed=all(r['status']=='legal_exact_reproduction' for r in results.values()),
    scope='Exact finite shared/split hierarchy sensitivities, with local trace and all original decisions/counters/routes reproduced. '
          'Repeated events are not independent samples. Unavailable alternatives refer only to this finite table. '
          'Diagnostic seconds include summary reconstruction/exclusion evaluation, exclude logging and are not formal speedup. '
          'Neither these surrogate margins nor local gaps are calibrated physical delay confidence; no reliability policy enabled.',
    results=results,input_sha256=bindings,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(B/'dp_sensitivity_mechanisms.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:{a:b for a,b in v.items() if a!='rows'} for k,v in results.items()},indent=2))
