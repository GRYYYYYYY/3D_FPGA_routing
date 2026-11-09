#!/usr/bin/env python3
"""Separate placement-balance effects from within-placement router effects."""
import math
from collections import defaultdict

from analyze_flatland_evaluation import Evidence
from check_flatland_partition_balance import audit
from flatland_benchmark import BASE, read
from lazagna_common import utc, write_json


def comparisons(rows):
    groups = defaultdict(dict)
    for row in rows:
        key = tuple(row[k] for k in ['split', 'width', 'family'])
        identity = (row['circuit'], row['seed'], row['placement_arm'], row['router'])
        assert identity not in groups[key]
        groups[key][identity] = row
    output = []
    for key, cells in sorted(groups.items()):
        cases = sorted({identity[:2] for identity in cells})
        pairs = [(arm+' R1/A0', (arm, 'R1'), (arm, 'A0'))
                 for arm in ['literal', 'relative3']]
        pairs += [(router+' relative3/literal', ('relative3', router), ('literal', router))
                  for router in ['A0', 'R1', 'B2']]
        for label, numerator, denominator in pairs:
            values = []
            for circuit, seed in cases:
                a = cells[(circuit, seed, *numerator)]
                b = cells[(circuit, seed, *denominator)]
                if a['status'] == b['status'] == 'legal':
                    values.append(dict(circuit=circuit, seed=seed,
                        ratio=a['critical_path_ns']/b['critical_path_ns']))
            output.append(dict(split=key[0], width=key[1], family=key[2], contrast=label,
                registered_pairs=len(cases), legal_pairs=len(values), individual_pairs=values,
                geomean_ratio=math.exp(sum(math.log(v['ratio']) for v in values)/len(values)) if values else None))
    return output


def main():
    evidence = Evidence()
    registration = BASE/'partition_balance_sensitivity_jobs.json'
    plan = read(registration)
    evidence.bind(registration)
    evidence.bind(BASE/'partition_balance_sensitivity_protocol.json', plan['protocol_sha256'])
    evidence.bind(BASE/'selected_configs.json', plan['selection_sha256'])
    selected = read(BASE/'selected_configs.json')
    # Require finalized invocation input seals; full global graph rehash remains
    # part of final study closure, as in the primary evaluator.
    invocations = list((BASE/'balance_invocations').glob('*_input_integrity.json'))
    assert invocations, 'Missing sensitivity input seals'
    for path in invocations:
        assert read(path)['passed']
        evidence.bind(path)
    rows = []
    for job in plan['jobs']:
        stage = 'balance_'+job['placement_arm']
        size = read(BASE/'capacity_selection.json')['circuits'][job['circuit']]['size']
        name = f"{stage}_{job['circuit']}_s{job['seed']}_{job['family']}_n{size}_w{job['width']}_p1"
        directory = BASE/'balance_cases'/name
        result = read(directory/'result.json')
        evidence.bind(directory/'result.json')
        case = read(directory/'registration.json')
        evidence.bind(directory/'registration.json')
        assert case['job'] == job == result['job']
        evidence.bind(registration, case['registration_sha256'])
        assert result['status'] in ['completed', 'placement_failed', 'balance_failed']
        place = BASE/'runs'/result['placement']
        manifest = read(place/'manifest.json')
        evidence.bind(place/'manifest.json')
        command = manifest['command']
        assert float(command[command.index('--partition_imbalance_ratio')+1]) == job['partition_argument']
        evidence.bind(place/'stdout.log', manifest['outputs']['stdout.log']['sha256'])
        if result['status'] != 'placement_failed':
            d = place/'triton_evidence'
            partition = read(d/'manifest.json')
            evidence.bind(d/'manifest.json')
            assert partition['returncode'] == 0 and partition['output_valid']
            evidence.bind(d/'triton_hypergraph.hgr', partition['input_sha256'])
            evidence.bind(d/'triton_hypergraph.hgr.part.2', partition['output_sha256'])
            balance = audit(d/'triton_hypergraph.hgr', d/'triton_hypergraph.hgr.part.2', 2, job['partition_argument'])
            assert balance == result['balance'] == read(directory/'balance_audit.json')
            evidence.bind(directory/'balance_audit.json')
            if job['placement_arm'] == 'relative3':
                assert balance['balanced'] == (result['status'] == 'completed')
        else:
            assert manifest['status'] != 'completed'
        for router in job['routers']:
            row = dict(job, router=router, status=result['status'], critical_path_ns=None)
            if result['status'] == 'completed':
                chosen = selected['selections'][job['family']]['R1']
                spec = dict(router=router, variant=chosen['variant'] if router == 'R1' else None,
                            config=chosen['config'] if router == 'R1' else None)
                route = evidence.run(result['roles'][router], dict(job, phase=stage), 'p1', spec)
                row.update(status=route['status'], run=route['run'],
                           critical_path_ns=route['metrics'].get('critical_path_ns') if route['status']=='legal' else None)
            rows.append(row)
    output = BASE/'balance_analysis'
    output.mkdir(exist_ok=False)
    write_json(output/'summary.json', dict(utc=utc(), status='complete', observations=rows,
        comparisons=comparisons(rows), input_bindings=evidence.bindings,
        qualification='Two circuits per split. No pooled train/test estimate, speedup claim, or broad architecture ranking claim. Failed cases remain registered and are excluded from CPD ratios.'))


if __name__ == '__main__':
    main()
