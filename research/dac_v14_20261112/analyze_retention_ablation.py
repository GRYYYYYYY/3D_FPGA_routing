#!/usr/bin/env python3
"""Verify discard accounting and isolate retention under one terminal graph."""
from pathlib import Path
import hashlib, json, re, sys
B = Path(sys.argv[1]); D = B.parent
assert json.loads((B / 'input_seal.json').read_text())['passed']
reg = json.loads((B / 'registration.json').read_text()); result = {}
def body(p): return hashlib.sha256(p.read_text().split('Net ', 1)[1].encode()).hexdigest()
for circuit in reg['circuits']:
    arms = {}
    for arm in ['P', 'Z']:
        rd = B / 'runs' / f'{circuit}_{arm}'
        m = json.loads((rd / 'manifest.json').read_text())
        assert m['status'] == 'completed' and m['metrics']['native_full_check_passed']
        assert json.loads((rd / 'independent_audit.json').read_text())['audit']['passed']
        assert json.loads((rd / 'final_guide_audit.json').read_text())['passed']
        if arm == 'P': assert json.loads((rd / 'retention_equivalence.json').read_text())['passed']
        lines = (rd / 'stdout.log').read_text().splitlines(); counters = {}
        for prefix in ['H3D_PERSISTENT_DELAY ', 'H3D_TARGET_DELAY ', 'H3D_SELECTED_DELAY ']:
            last = [x for x in lines if x.startswith(prefix)][-1]
            counters[prefix.strip()] = {k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', last)}
        p, q = counters['H3D_PERSISTENT_DELAY'], counters['H3D_TARGET_DELAY']
        assert p['enabled'] and p['retain'] == (arm == 'P')
        assert p['forward_settled'] + p['reverse_settled'] == q['settled'] <= p['ledger_endpoints'] * 4096
        assert q['endpoint_budget'] == 4096 and q['candidate_quota'] == 256
        assert p['restarts'] <= p['evictions'] + p['discards']
        if arm == 'Z':
            assert p['discards'] == q['queries'] and p['live_states'] == 0 and p['peak_states'] <= 1 and p['evictions'] == 0
        else: assert p['discards'] == 0
        arms[arm] = dict(metrics=m['metrics'], counters=counters, process_seconds=m['wall_seconds'],
                         planning_seconds=float(re.findall(r'planning_seconds=([0-9.]+)', '\n'.join(x for x in lines if x.startswith('H3D_PLAN ')))[-1]),
                         body_sha256=body(rd / 'routed.route'), stdout_sha256=hashlib.sha256((rd / 'stdout.log').read_bytes()).hexdigest())
    old = D / 'target_reuse_dev_01/runs' / f'{circuit}_E/routed.route'
    result[circuit] = dict(arms=arms, Z_matches_prior_E_route=arms['Z']['body_sha256'] == body(old), prior_E_body_sha256=body(old))
(B / 'retention_mechanisms.json').write_text(json.dumps(dict(passed=True, circuits=result,
    scope='Same universal-terminal graph, exact cache, work ledger and all quality parameters; Z discards only frontier per target. Terminal events may repeat. Runtime is not proportional to settlement count; no formal speedup claim.',
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2) + '\n')
print(json.dumps(result, indent=2))
