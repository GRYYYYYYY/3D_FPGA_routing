#!/usr/bin/env python3
"""Four declared development circuits; keep missing/pending states and uniform methods."""
from pathlib import Path
import collections, hashlib, json, math
D = Path(__file__).resolve().parent
circuits = ['spmv', 'softmax', 'eltwise_layer', 'bnn']
rows, bound = [], {}
def read(p):
    bound[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return json.loads(p.read_text())
for circuit in circuits:
    small = circuit in ['spmv', 'softmax']
    query_batch = D / ('target_reuse_dev_01' if small else 'target_reuse_expansion_dev_01')
    refs = read(query_batch / f'{circuit}_references.json')
    locations = {a: Path(refs[a]['path']) for a in ['A0', 'R1']}
    locations.update({a: query_batch / 'runs' / f'{circuit}_{a}' for a in ['Q', 'E']})
    locations['P'] = D / ('persistent_query_dev_01' if small else 'persistent_expansion_dev_01') / 'runs' / f'{circuit}_P'
    locations['L'] = D / ('bound_clamp_dev_01' if small else 'bound_clamp_expansion_dev_01') / 'runs' / f'{circuit}_L'
    locations['Cq'] = D / ('query_priority_dev_01' if small else 'query_priority_expansion_dev_01') / 'runs' / f'{circuit}_Cq'
    locations['Bq'] = D / ('source_share_dev_01' if small else 'source_share_expansion_dev_01') / 'runs' / f'{circuit}_Bq'
    locations['Rq'] = D / ('reverse_rerank_dev_01' if small else 'reverse_rerank_expansion_dev_01') / 'runs' / f'{circuit}_Rq'
    feedback_batch = 'feedback_dev_01' if small else 'feedback_bnn_dev_01' if circuit == 'bnn' else 'feedback_expansion_01'
    locations['U'] = D / feedback_batch / 'runs' / f'{circuit}_U'
    for role, rd in locations.items():
        m = read(rd / 'manifest.json') if (rd / 'manifest.json').exists() else {}
        status = m.get('status', 'missing')
        audit = read(rd / 'independent_audit.json') if (rd / 'independent_audit.json').exists() else None
        batch = rd.parent.parent
        sealed = role in ['A0', 'R1'] or ((batch / 'input_seal.json').exists() and read(batch / 'input_seal.json')['passed'])
        guide = role in ['A0', 'R1'] or ((rd / 'final_guide_audit.json').exists() and read(rd / 'final_guide_audit.json')['passed'])
        if status == 'completed':
            status = 'legal' if m['metrics']['native_full_check_passed'] and audit and audit['audit']['passed'] and sealed and guide else 'completed_pending_audit_or_seal'
        if status == 'running': status = 'recorded_running'
        rows.append(dict(circuit=circuit, arm=role, status=status, metrics=m.get('metrics') or {},
                         physical_metrics=audit.get('physical_metrics') if audit else None, path=str(rd),
                         environment=m.get('environment'), process_seconds=m.get('wall_seconds'),
                         role='matched_historical_reference' if role in ['A0', 'R1'] else 'selected_sealed_method_execution' if status == 'legal' else 'unsealed_or_terminal_nonlegal'))
index = {(r['circuit'], r['arm']): r for r in rows}
summary = {}
for left, right in [(a,b) for a in ['A0','R1','U'] for b in ['Q','E','P','L','Cq','Bq','Rq']] + [('Q','E'),('E','P'),('P','L'),('E','L'),('P','Cq'),('P','Bq'),('Cq','Bq'),('P','Rq'),('Bq','Rq')]:
    pairs = []
    for c in circuits:
        a, b = index[c,left], index[c,right]
        if a['status'] == b['status'] == 'legal':
            ac, bc = a['metrics']['critical_path_ns'], b['metrics']['critical_path_ns']
            pairs.append(dict(circuit=c, reference_ns=ac, new_ns=bc, improvement_pct=100*(1-bc/ac)))
    summary[left+'->'+right] = dict(declared_circuits=len(circuits), both_legal=len(pairs),
        improved=sum(p['new_ns']<p['reference_ns'] for p in pairs), tied=sum(p['new_ns']==p['reference_ns'] for p in pairs),
        regressed=sum(p['new_ns']>p['reference_ns'] for p in pairs),
        geomean_improvement_pct=100*(1-math.exp(sum(math.log(p['new_ns']/p['reference_ns']) for p in pairs)/len(pairs))) if pairs else None,
        worst_improvement_pct=min((p['improvement_pct'] for p in pairs),default=None), pairs=pairs)
result = dict(scope='Four previously seen seed11 HybridO/P0/W100 development circuits, uniformly selected Q/E/P/L/Cq/Bq/Rq query strategies under original terminal-layer bounding boxes and full-feedback U comparator. No per-circuit best-arm selection, no blind generalization, no historical timing ratios. P large cases use exact closure views verified separately; unsealed cases stay in declared population and are excluded from legal CPD ratios.',
    summary=summary, statuses={a:dict(collections.Counter(r['status'] for r in rows if r['arm']==a)) for a in ['A0','R1','U','Q','E','P','L','Cq','Bq','Rq']},
    observations=rows, input_sha256=bound, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(D / 'query_circuit_summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:{a:b for a,b in v.items() if a!='pairs'} for k,v in summary.items()},indent=2))
