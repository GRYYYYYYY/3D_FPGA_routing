#!/usr/bin/env python3
"""Account for every registered training attempt without changing selection."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path

from analyze_flatland_evaluation import Evidence
from flatland_benchmark import BASE, read
from lazagna_common import sha256, utc, write_json


def job_key(job):
    return tuple(job[k] for k in ('circuit', 'family', 'seed', 'placement',
                                  'router', 'variant', 'config', 'width'))


def collect_case(circuit, family, jobs, evidence):
    directory = BASE / 'training_cases' / f'{circuit}_{family}'
    result = read(directory / 'result.json')
    audit = read(directory / 'audit_summary.json')
    evidence.bind(directory / 'result.json')
    evidence.bind(directory / 'audit_summary.json')
    assert result['status'] == 'completed', f'Unresolved training case: {directory}'
    assert audit['passed'] and audit['registered_route_count'] == len(jobs) == 33
    expected = {job_key(j): j for j in jobs}
    assert len(expected) == len(jobs)
    seen = set()
    rows = []
    for group in ('legal', 'failed'):
        for entry in audit[group]:
            name = entry['name']
            manifest = read(BASE / 'runs' / name / 'manifest.json')
            key = job_key(manifest['tags'])
            assert key in expected and key not in seen, (name, 'unexpected/duplicate registration')
            seen.add(key)
            job = expected[key]
            spec = {k: job[k] for k in ('router', 'variant', 'config')}
            actual = evidence.run(name, dict(job, phase='training'), job['placement'], spec)
            assert (actual['status'] == 'legal') == (group == 'legal'), name
            assert actual['status'] not in ('starting', 'running'), name
            rows.append(dict(job, run=name, status=actual['status'],
                             failure_class=actual.get('failure_class'),
                             returncode=actual.get('returncode')))
    assert seen == set(expected)
    assert len(audit['legal']) == audit['legal_count'] == result['legal_routes']
    assert len(audit['failed']) == audit['failed_count'] == result['failed_routes']
    assert result['registered_routes'] == len(rows)
    return rows


def summarize(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['family'], row['router'], row['variant'], row['config']].append(row)
    groups = []
    for (family, router, variant, config), items in grouped.items():
        assert len({r['circuit'] for r in items}) == len(items)
        counts = Counter(r['failure_class'] for r in items if r['status'] != 'legal')
        legal = sum(r['status'] == 'legal' for r in items)
        assert legal + sum(counts.values()) == len(items)
        groups.append(dict(family=family, router=router, variant=variant, config=config,
                           registered=len(items), legal=legal, failure_counts=dict(counts)))
    return dict(registered_attempts=len(rows), legal_attempts=sum(r['status'] == 'legal' for r in rows),
                groups=groups, observations=rows)


def main(output):
    output = Path(output)
    assert not output.exists()
    evidence = Evidence()
    plan = read(BASE / 'training_jobs.json')
    protocol = read(BASE / 'benchmark_protocol.json')
    selection = read(BASE / 'selected_configs.json')
    assert selection['status'] == 'frozen_before_heldout'
    evidence.bind(BASE / 'selected_configs.json')
    evidence.bind(BASE / 'training_jobs.json', selection['training_jobs_sha256'])
    evidence.bind(BASE / 'benchmark_protocol.json', plan['protocol_sha256'])
    assert selection['protocol_sha256'] == plan['protocol_sha256']
    for path, digest in selection['evidence_sha256'].items():
        evidence.bind(path, digest)
    jobs = plan['jobs']
    assert len(jobs) == len({job_key(j) for j in jobs}) == 594
    rows = []
    for circuit in protocol['training']:
        for family in protocol['architectures']:
            subset = [j for j in jobs if j['circuit'] == circuit and j['family'] == family]
            rows.extend(collect_case(circuit, family, subset, evidence))
    summary = summarize(rows)
    assert summary['registered_attempts'] == 594
    assert all(g['registered'] == 6 for g in summary['groups'])
    summary.update(utc=utc(), status='all_registered_training_attempts_accounted',
                   source_sha256=sha256(__file__), input_sha256=evidence.bindings,
                   interpretation='Training coverage only; all failures remain in denominators. '
                   'No failed-run CPD is used, and no selected configuration is changed.')
    write_json(output, summary)
    print(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=BASE / 'training_analysis/summary.json')
    main(parser.parse_args().output)
