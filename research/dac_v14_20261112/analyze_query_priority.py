#!/usr/bin/env python3
"""Check criticality query order while retaining P budgets and final legality."""
from pathlib import Path
import hashlib, json, re, sys

B = Path(sys.argv[1])
reg = json.loads((B / 'registration.json').read_text())
assert json.loads((B / 'input_seal.json').read_text())['passed']
results = {}
for circuit in reg['circuits']:
    arms = {}
    for arm in reg['arms']:
        rd = B / 'runs' / f'{circuit}_{arm}'
        m = json.loads((rd / 'manifest.json').read_text())
        if m['status'] != 'completed':
            arms[arm] = dict(status=m['status'])
            continue
        assert m['metrics']['native_full_check_passed']
        audit = json.loads((rd / 'independent_audit.json').read_text())
        assert audit['audit']['passed']
        assert json.loads((rd / 'final_guide_audit.json').read_text())['passed']
        eq = rd / 'reuse_equivalence.json'
        if arm == 'E' and eq.exists(): assert json.loads(eq.read_text())['passed']
        env = m['environment']
        assert env['VPR_H3D_TARGET_FRONTIER']=='1'
        assert env['VPR_H3D_QUERY_CRITICALITY_ORDER']==('1' if arm=='Cq' else '0')
        assert env['VPR_H3D_ALL_LAYER_BB']==env['VPR_H3D_LAYER_BB_FEEDBACK']=='0'
        if arm=='P':assert json.loads((rd/'priority_equivalence.json').read_text())['passed']
        assert env['VPR_H3D_DELAY_BUDGET'] == '4096' and env['VPR_H3D_TARGET_QUOTA'] == '256'
        assert env['VPR_H3D_FEEDBACK'] == env['VPR_H3D_TIMING_GUIDE'] == '0'
        lines = (rd / 'stdout.log').read_text().splitlines()
        counters = {}
        for prefix in ['H3D_PERSISTENT_DELAY ', 'H3D_TARGET_DELAY ', 'H3D_SELECTED_DELAY ', 'H3D_QUERY_PRIORITY ']:
            matched = [line for line in lines if line.startswith(prefix)]
            assert matched
            counters[prefix.strip()] = {k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', matched[-1])}
        p, q, selected = (counters[x] for x in ['H3D_PERSISTENT_DELAY', 'H3D_TARGET_DELAY', 'H3D_SELECTED_DELAY'])
        assert selected['informed_pins'] == selected['pins'] - selected['estimated']
        assert selected['pins'] == sum(selected[k] for k in ['both', 'source_only', 'sink_only', 'estimated'])
        if arm in ['P','Cq']:
            priority=counters['H3D_QUERY_PRIORITY']
            assert priority['enabled']==(arm=='Cq') and 0<=priority['reordered']<=priority['plans']
            if arm=='P':assert priority['reordered']==0
            assert p['retain']==1 and p['discards']==0
            assert p['enabled'] and p['peak_states'] <= p['slots'] == int(env['VPR_H3D_FRONTIER_SLOTS'])
            assert p['forward_settled'] + p['reverse_settled'] == q['settled'] <= 4096 * p['ledger_endpoints']
            assert p['terminal_certificates'] <= p['forward_settled']
            assert p['restarts'] <= p['evictions']
        else: assert not p['enabled'] and p['forward_settled'] == p['reverse_settled'] == 0
        rss = re.search(r'Maximum resident set size \(kbytes\): (\d+)', (rd / 'time.txt').read_text())
        arms[arm] = dict(status='legal', counters=counters, metrics=m['metrics'],
                         physical_metrics=audit['physical_metrics'], process_seconds=m['wall_seconds'],
                         peak_rss_kib=int(rss[1]) if rss else None,
                         planning_seconds=float(re.findall(r'planning_seconds=([0-9.]+)', '\n'.join(x for x in lines if x.startswith('H3D_PLAN ')))[-1]),
                         log_sha256=hashlib.sha256((rd / 'stdout.log').read_bytes()).hexdigest())
    results[circuit] = arms
result = dict(circuits=results, passed=True,
              scope='Different query strategy, not decision-equivalent optimization. Every universal-terminal and target-side settlement is charged. Native per-endpoint budget assertions supplement aggregate reconciliation here. Terminal certificate counts include repeats after eviction, not unique cache entries. Criticality order changes only candidate/query pass; DP pins unchanged. No ranking-uncertainty scheduler yet. Development times only.',
              script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              seal_sha256=hashlib.sha256((B / 'input_seal.json').read_bytes()).hexdigest())
(B / 'priority_mechanisms.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(results, indent=2))
