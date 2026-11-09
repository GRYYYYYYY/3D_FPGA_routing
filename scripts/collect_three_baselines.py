#!/usr/bin/env python3
"""Keep literature, cross-tool systems, and same-graph algorithm results separate."""
from collections import Counter
import csv
import math
from pathlib import Path

from three_baseline_common import BASE, ROOT, read, sha256, utc, write_json


def refined_failure(job):
    """Keep immutable runner receipts; classify resource failures from the log."""
    classification = job.get('classification', job['state'])
    if job.get('directory'):
        log = (Path(job['directory'])/'stdout.log').read_text(errors='replace')
        if 'Failed to find device which satisfies resource requirements' in log:
            return 'device_capacity_failure'
    return classification


def paired_cpd(rows, baseline, treatment):
    index = {}
    for row in rows:
        key = row['case'], row['arm']
        if key in index:
            raise ValueError(f'Duplicate case/arm: {key}')
        index[key] = row
    cases = sorted({r['case'] for r in rows if r['arm'] in (baseline, treatment)})
    pairs, excluded = [], []
    for case in cases:
        a, b = index.get((case, baseline)), index.get((case, treatment))
        if not (a and b and a['valid_solution'] and b['valid_solution']):
            excluded.append(case)
            continue
        left, right = a['cpd_ns'], b['cpd_ns']
        if not all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in (left, right)):
            raise ValueError(f'Invalid successful CPD: {case}')
        pairs.append(dict(case=case, baseline_cpd_ns=left, treatment_cpd_ns=right,
                          ratio=right/left, change_percent=100*(right/left-1)))
    gm = math.exp(sum(math.log(p['ratio']) for p in pairs)/len(pairs)) if pairs else None
    return dict(baseline=baseline, treatment=treatment, registered_cases=len(cases),
                paired_legal_cases=len(pairs), excluded_cases=excluded, pairs=pairs,
                cpd_geomean_ratio=gm, cpd_change_percent=100*(gm-1) if gm is not None else None)


def main():
    output = BASE/'summary.json'
    assert not output.exists()
    validation = read(BASE/'validation.json')
    assert validation['passed']
    assert validation['protocol_sha256'] == sha256(BASE/'protocol.json')
    assert validation['route_state_sha256'] == sha256(BASE/'route_state.json')
    audits = {a['name']: a for a in validation['audits']}
    rows = []
    for job in read(BASE/'route_state.json')['jobs']:
        valid = job.get('native_legal', False) and audits.get(job['name'], {}).get('passed', False)
        metrics = job.get('metrics', {})
        rows.append(dict(case=job['case'], arm=job['arm'], state=job['state'],
            classification='audited_success' if valid else refined_failure(job),
            runner_classification=job.get('classification', job['state']),
            valid_solution=valid, cpd_ns=metrics.get('critical_path_ns') if valid else None,
            iterations=metrics.get('iterations') if valid else None,
            route=audits[job['name']]['route'] if valid else None,
            directory=job.get('directory')))
    counts = {arm: dict(Counter(r['classification'] for r in rows if r['arm'] == arm)) for arm in ('modern', 'a0', 'a3')}
    algorithm = paired_cpd(rows, 'a0', 'a3')
    algorithm['scope'] = 'Same native graph, packed netlist, placement and route options; A3 environment only changes router planning.'
    system = paired_cpd(rows, 'modern', 'a3')
    system['scope'] = 'Same packed netlist and placement, different toolchains and RRG families; conditional system result, not isolated algorithm or equal-resource result.'
    native_system = paired_cpd(rows, 'modern', 'a0')
    native_system['scope'] = system['scope']
    original = read(ROOT/'results/analysis.json')
    oldrows = [dict(case=r['circuit'], arm=r['variant'], valid_solution=r['valid_solution'],
                    cpd_ns=r['metrics'].get('critical_path_ns') if r['valid_solution'] else None)
               for r in original['rows'] if r['dataset']=='native20_w100' and r['variant'] in ('a0', 'a3')]
    original_pair = paired_cpd(oldrows, 'a0', 'a3')
    literature = read(BASE/'published_reference.json')
    write_json(output, dict(utc=utc(), validated=True, validation_sha256=sha256(BASE/'validation.json'),
        counts=counts, rows=rows, comparisons=dict(B1_published=dict(
            status='reported_literature_reference_only', reference=literature,
            direct_A3_ratio=None,
            missing='Common author 2D denominator, exact synthesized inputs/experiment revision, and matching architecture condition; published Table IV has no 50% SB row.'),
            B2_modern_system=system, B3_native_algorithm=algorithm,
            modern_vs_native_A0_system=native_system, B3_original_native20=original_pair),
        inference_limits=['Single seed and 11 preselected diagnostic circuits.',
            'Graph generation uses routed-clock connectivity; measured routing uses ideal clocks in every arm.',
            'No speedup claims: concurrent runs and different PnR stages.',
            'Cross-family VPR wirelength counts are not directly comparable.',
            'Failures and missing placements remain in the denominator; CPD ratios use jointly legal, audited pairs only.']))
    with (BASE/'per_case.csv').open('w', newline='') as stream:
        fields=['case','arm','classification','valid_solution','cpd_ns','iterations','directory']
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    print('Counts', counts, flush=True)
    for label, comparison in [('A3/A0',algorithm),('A3/modern',system),('A0/modern',native_system)]:
        print(label, comparison['paired_legal_cases'], comparison['cpd_change_percent'], flush=True)


if __name__ == '__main__':
    main()
