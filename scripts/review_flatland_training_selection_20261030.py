#!/usr/bin/env python3
"""Describe frozen selected arms on training data; never select or tune anything."""
import math
from pathlib import Path

from flatland_benchmark import BASE, read
from lazagna_common import sha256, utc, write_json


def main():
    output = BASE / 'training_selection_review_20261030.json'
    assert not output.exists()
    summary = read(BASE / 'training_analysis/summary.json')
    assert summary['status'] == 'all_registered_training_attempts_accounted'
    assert len(summary['observations']) == summary['registered_attempts'] == 594
    hashes = {}

    def bind(path, expected=None):
        path = Path(path).resolve()
        digest = sha256(path)
        if expected is not None:
            assert digest == expected, path
        hashes[str(path)] = digest
        return read(path)

    bind(BASE / 'training_analysis/summary.json')
    selection = bind(BASE / 'selected_configs.json', summary['input_sha256'][str(BASE / 'selected_configs.json')])
    protocol = bind(BASE / 'benchmark_protocol.json', selection['protocol_sha256'])
    assert selection['status'] == 'frozen_before_heldout'
    families = {}
    for family, chosen in selection['selections'].items():
        arm = chosen['R1']
        rows = []
        for circuit in protocol['training']:
            obs = [x for x in summary['observations'] if x['circuit'] == circuit and x['family'] == family
                   and (x['router'] == 'A0' or (x['router'] == 'R1' and x['variant'] == arm['variant'] and x['config'] == arm['config']))]
            assert len(obs) == 2 and {x['router'] for x in obs} == {'A0', 'R1'}
            audit_path = BASE / 'training_cases' / f'{circuit}_{family}' / 'audit_summary.json'
            audit = bind(audit_path, selection['evidence_sha256'][str(audit_path)])
            assert audit['passed'] and audit['registered_route_count'] == 33
            legal = {x['name']: x for x in audit['legal']}
            row = dict(circuit=circuit, seed=11, arms={})
            for x in obs:
                assert x['seed'] == 11 and x['width'] == 100 and x['placement'] == 'p0'
                p = BASE / 'runs' / x['run'] / 'manifest.json'
                m = bind(p, summary['input_sha256'][str(p)])
                entry = dict(run=x['run'], status=x['status'], failure_class=x['failure_class'])
                if x['status'] == 'legal':
                    assert m['status'] == 'completed' and m['returncode'] == 0
                    metrics = m['metrics']
                    assert metrics == legal[x['run']]['metrics']
                    assert metrics['native_full_check_passed'] and metrics['routing_success_reported']
                    entry.update(critical_path_ns=metrics['critical_path_ns'], wirelength=metrics['wirelength'])
                row['arms'][x['router']] = entry
            a, r = (row['arms'][k] for k in ['A0', 'R1'])
            if a['status'] == r['status'] == 'legal':
                row.update(cpd_ratio=r['critical_path_ns'] / a['critical_path_ns'],
                           wirelength_ratio=r['wirelength'] / a['wirelength'])
                row['cpd_reduction_percent'] = 100 * (1 - row['cpd_ratio'])
            rows.append(row)
        paired = [r for r in rows if 'cpd_ratio' in r]
        def extreme(key):
            if not paired:
                return None
            r = key(paired, key=lambda r: r['cpd_reduction_percent'])
            return {k: r[k] for k in ['circuit', 'seed', 'cpd_reduction_percent']}
        families[family] = dict(selected_variant=arm['variant'], selected_config=arm['config'],
            registered_circuits=len(rows), legal_counts={k: sum(r['arms'][k]['status'] == 'legal' for r in rows) for k in ['A0', 'R1']},
            paired_count=len(paired), rows=rows,
            cpd_geomean_reduction_percent=100 * (1 - math.exp(sum(math.log(r['cpd_ratio']) for r in paired) / len(paired))) if paired else None,
            wirelength_geomean_change_percent=100 * (math.exp(sum(math.log(r['wirelength_ratio']) for r in paired) / len(paired)) - 1) if paired else None,
            best_observed=extreme(max), worst_observed=extreme(min),
            cpd_improved=sum(r['cpd_ratio'] < 1 for r in paired),
            cpd_unchanged=sum(r['cpd_ratio'] == 1 for r in paired),
            cpd_regressed=sum(r['cpd_ratio'] > 1 for r in paired))
    write_json(output, dict(utc=utc(), status='training_only_descriptive_review', families=families,
        input_sha256=hashes, source_sha256=sha256(__file__),
        interpretation='Same seed11/P0/W100/architecture A0 denominator, common legal circuits only. '
            'Selected on these training data: estimates have selection bias and do not establish heldout benefit. '
            'Failures retained without imputed QoR. Architecture cohorts differ: these gains cannot rank architectures. '
            'No 2D, B2, runtime speedup, significance, or full integrity-closure claim. '
            'Full route audit bytes are bound by prior training analysis, not rehashed by this lightweight review.'))
    for family, data in families.items():
        print(family, {k:v for k,v in data.items() if k != 'rows'})


if __name__ == '__main__':
    main()
