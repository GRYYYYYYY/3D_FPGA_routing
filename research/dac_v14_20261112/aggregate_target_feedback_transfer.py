#!/usr/bin/env python3
"""Keep all four pre-ordered seed21 transfer circuits and their failure states."""
from pathlib import Path
import collections
import hashlib
import json
import math

D = Path(__file__).resolve().parent
population = {'clstm_like.small': 'target_feedback_transfer_dev_02',
              'conv_layer': 'target_feedback_transfer_dev_02',
              'robot_rl': 'target_feedback_transfer_expansion_dev_01',
              'tpu_like.small.os': 'target_feedback_transfer_expansion_dev_01'}
arms = ['A0', 'R1', 'F', 'V', 'Tf', 'A1']
rows, bindings, environments, binaries = [], {}, {}, set()
for circuit, batch in population.items():
    B = D / batch
    assert json.loads((B / 'input_seal.json').read_text())['passed']
    assert json.loads((B / 'target_feedback_transfer_mechanisms.json').read_text())['passed']
    analysis = json.loads((B / 'analysis.json').read_text())
    assert (analysis['seed'], analysis['family'], analysis['flow'], analysis['width']) == (21, 'hybrid_o', 'p0', 100)
    for p in [B / 'input_seal.json', B / 'target_feedback_transfer_mechanisms.json', B / 'analysis.json']:
        bindings[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    for row in analysis['observations']:
        if row['circuit'] != circuit:
            continue
        row = dict(row)
        row['metrics'] = dict(row['metrics'])
        m = json.loads((Path(row['path']) / 'manifest.json').read_text())
        if row['arm'] in ['F', 'V', 'Tf', 'A1']:
            env = m['environment']
            assert environments.setdefault(row['arm'], env) == env
            binaries.add(m['shared_inputs'][m['command'][0]]['sha256'])
        if row['status'] != 'legal':
            row['failed_provisional_cpd_ns'] = row['metrics'].get('critical_path_ns')
            row['metrics']['critical_path_ns'] = None
        rows.append(row)
assert len(binaries) == 1 and len(rows) == len(population) * len(arms)
index = {(r['circuit'], r['arm']): r for r in rows}
paired = {}
for left, right in [('A0', 'Tf'), ('R1', 'Tf'), ('F', 'Tf'), ('V', 'Tf'), ('A1', 'Tf'), ('A0', 'A1')]:
    cases = []
    ratios = []
    for c in population:
        a, b = index[c, left], index[c, right]
        if a['status'] != 'legal' or b['status'] != 'legal':
            continue
        ratio = b['metrics']['critical_path_ns'] / a['metrics']['critical_path_ns']
        ratios.append(ratio)
        cases.append(dict(circuit=c, improvement_pct=100 * (1 - ratio)))
    paired[f'{left}->{right}'] = dict(both_legal=len(ratios), declared_circuits=len(population),
        improve=sum(r < 1 for r in ratios), tie=sum(r == 1 for r in ratios), regress=sum(r > 1 for r in ratios),
        circuit_geomean_improvement_pct=100 * (1 - math.exp(sum(map(math.log, ratios)) / len(ratios))),
        worst_improvement_pct=100 * (1 - max(ratios)), cases=cases,
        interpretation='different search scope' if left == 'A1' or right == 'A1' else 'same original search scope')
result = dict(scope='Four circuits in pre-pinned grid/name ordering, seed21 HybridO/P0/W100. '
    'No per-input retuning, no per-circuit best-arm selection, no blind test or formal timing claim. '
    'Conv failure remains in every denominator despite the separately verified necessary source-capacity cut.',
    circuits=list(population), status_counts={a: dict(collections.Counter(r['status'] for r in rows if r['arm'] == a)) for a in arms},
    paired=paired, observations=rows, bindings=bindings)
(D / 'target_feedback_transfer_circuit_summary.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(status=result['status_counts'], paired=paired), indent=2))
