#!/usr/bin/env python3
"""Explicit six-circuit development population; never omit pending/failed cases."""
from pathlib import Path
import collections, hashlib, json, math

D = Path(__file__).resolve().parent
selection = [
    ('spmv', 'feedback_dev_01', 'U'),
    ('softmax', 'feedback_dev_01', 'U'),
    ('eltwise_layer', 'feedback_expansion_01', 'U'),
    ('attention_layer', 'feedback_expansion_01', 'U'),
    ('bnn', 'feedback_bnn_dev_01', 'U'),
    ('gemm_layer', 'feedback_gemm_dev_01', 'C'),
]
rows, binding = [], {}
def read(path):
    binding[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text())

for circuit, name, implementation in selection:
    batch = D / name
    references = read(batch / f'{circuit}_references.json')
    sealed = (batch / 'input_seal.json').exists() and read(batch / 'input_seal.json')['passed']
    observations = read(batch / 'observations.json') if (batch / 'observations.json').exists() else []
    for role, actual in [('A0', 'A0'), ('R1', 'R1'), ('U', implementation)]:
        if role in references:
            row = dict(circuit=circuit, arm=role, **references[role])
        else:
            found = [x for x in observations if x['circuit'] == circuit and x['arm'] == actual]
            if found:
                row = dict(found[0])
                if row['status'] == 'legal' and not sealed:
                    row['status'] = 'completed_pending_seal'
            else:
                rd = batch / 'runs' / f'{circuit}_{actual}'
                m = read(rd / 'manifest.json') if (rd / 'manifest.json').exists() else {}
                status = m.get('status', 'missing')
                if status == 'completed': status = 'completed_pending_audit_seal'
                if status == 'running': status = 'recorded_running'
                row = dict(circuit=circuit, path=str(rd), status=status,
                           metrics=m.get('metrics') or {}, process_seconds=m.get('wall_seconds'))
        if row['status'] == 'legal':
            rd = Path(row['path'])
            audit = read(rd / 'independent_audit.json')
            manifest = read(rd / 'manifest.json')
            assert audit['audit']['passed'] and manifest['metrics']['native_full_check_passed']
            if role == 'U':
                assert sealed and read(rd / 'final_guide_audit.json')['passed']
        row.pop('h3d', None)
        row.update(arm=role, implementation_arm=actual, selected_batch=name)
        rows.append(row)

index = {(r['circuit'], r['arm']): r for r in rows}
summary = {}
for reference in ['A0', 'R1']:
    pairs = []
    for circuit, _, _ in selection:
        a, b = index[circuit, reference], index[circuit, 'U']
        if a['status'] == b['status'] == 'legal':
            pairs.append((circuit, a['metrics']['critical_path_ns'], b['metrics']['critical_path_ns']))
    summary[reference] = dict(declared_circuits=len(selection), both_legal=len(pairs),
                              improved=sum(b < a for _, a, b in pairs),
                              tied=sum(b == a for _, a, b in pairs),
                              regressed=sum(b > a for _, a, b in pairs),
                              geomean_improvement_pct=100 * (1 - math.exp(sum(math.log(b/a) for _, a, b in pairs)/len(pairs))) if pairs else None,
                              worst_improvement_pct=min((100*(1-b/a) for _, a, b in pairs), default=None), pairs=pairs)
result = dict(scope='Six declared development circuits, one selected full-feedback execution each. C on gemm is the same quality policy with exact compact closure optimization; it is paired against static F in its batch. No eligibility trigger, mixed scorer or timing guide. Previously seen single seed, not blind validation. Historical timing never used for speedup.',
              selection=selection, summary=summary,
              statuses={a: dict(collections.Counter(r['status'] for r in rows if r['arm'] == a)) for a in ['A0', 'R1', 'U']},
              observations=rows, input_sha256=binding,
              aggregation_rule='All six remain in declared population. CPD ratios use only both-legal, audited, sealed full-feedback pairs. No failed CPD ranking.',
              script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(D / 'feedback_circuit_summary.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(dict(summary=summary, statuses=result['statuses']), indent=2))
