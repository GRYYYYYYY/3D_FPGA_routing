#!/usr/bin/env python3
"""Recompute published Flatland CSV summaries; these are not local experiments."""
import ast
import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean

from lazagna_common import ROOT, sha256, utc, write_json

BASE = ROOT / 'results/architecture_flow_20261027'
SOURCE = ROOT / 'vendor/beyond-flatland-src/DAC26_results'
ARCHES = {'CB': '3d_cb', 'CB-O': '3d_cb_o', 'CB-I': '3d_cb_i',
          'SB': '3d_sb', 'Hybrid': 'hybrid', 'Hybrid-O': 'hybrid_o',
          'Hybrid-I': 'hybrid_i'}


def load(name):
    path = SOURCE / name
    with path.open() as f:
        raw = list(csv.reader(f))
    headers = [(i, r) for i, r in enumerate(raw) if r and r[0] == 'success']
    if len(headers) != 1:
        raise ValueError(f'Expected one header, wherever placed: {path}')
    header_index, fields = headers[0]
    if any(len(r) != len(fields) for r in raw):
        raise ValueError(f'Malformed row: {path}')
    rows = [dict(zip(fields, r)) for i, r in enumerate(raw) if i != header_index]
    grouped = defaultdict(list)
    configs = {}
    seen = set()
    failures = []
    for row in rows:
        key = (row['blif_file'], int(row['seed']))
        if key in seen:
            raise ValueError(f'Duplicate sample: {path}: {key}')
        seen.add(key)
        if row['success'] != 'True' or int(row['return_code']) != 0:
            failures.append(row)
            continue
        if any(not math.isfinite(float(row[k])) or float(row[k]) <= 0 for k in ('cpd', 'wl')):
            raise ValueError(f'Invalid QoR: {key}')
        grouped[key[0]].append(row)
        if row.get('config'):
            config = ast.literal_eval(row['config'])
            if key[0] in configs and configs[key[0]] != config:
                raise ValueError(f'Configuration changes across seeds: {key}')
            configs[key[0]] = config
    for circuit in {c for c, s in seen}:
        if {s for c, s in seen if c == circuit} != set(range(1, 11)):
            raise ValueError(f'Expected all ten seeds: {path}: {circuit}')
    means = {c: {k: mean(float(x[k]) for x in rs) for k in ('cpd', 'wl')}
             for c, rs in grouped.items() if len(rs) == 10}
    return dict(path=str(path), sha256=sha256(path), samples=len(rows),
                circuits=len(grouped), seeds=list(range(1, 11)), means=means,
                configs=configs, failures=failures, header_row_zero_based=header_index,
                incomplete_circuits={c: len(rs) for c, rs in grouped.items() if len(rs) != 10})


def compare(a, b, metric, circuits=None):
    common = set(a['means']) & set(b['means'])
    circuits = sorted(common if circuits is None else circuits)
    if not set(circuits) <= common:
        raise ValueError('Requested circuit is incomplete')
    ratios = {c: a['means'][c][metric] / b['means'][c][metric] for c in circuits}
    changes = {c: 100 * (r - 1) for c, r in ratios.items()}
    return dict(circuits=circuits, circuit_count=len(circuits),
                geomean_change_percent=100 * (math.exp(mean(map(math.log, ratios.values()))) - 1),
                maximum_reduction_percent=-min(changes.values()),
                maximum_regression_percent=max(0, max(changes.values())),
                wins=sum(r < 1 - 1e-9 for r in ratios.values()),
                ties=sum(abs(r - 1) <= 1e-9 for r in ratios.values()),
                losses=sum(r > 1 + 1e-9 for r in ratios.values()),
                per_circuit_change_percent=changes)


def main():
    out = BASE / 'published_reference_analysis.json'
    if out.exists():
        raise FileExistsError(out)
    datasets = {'2D': load('vtr9_2d_results.csv')}
    summary = {}
    for arch, stem in ARCHES.items():
        datasets[arch + '_baseline'] = load(f'vtr9_{stem}_results.csv')
        datasets[arch + '_paper'] = load(f'our_{stem}_results.csv')
        summary[arch] = {m: {
            'paper_vs_same_arch_3D': compare(datasets[arch + '_paper'], datasets[arch + '_baseline'], m),
            'paper_vs_common_2D': compare(datasets[arch + '_paper'], datasets['2D'], m),
            'baseline_vs_common_2D': compare(datasets[arch + '_baseline'], datasets['2D'], m),
        } for m in ('cpd', 'wl')}
    rank_circuits = sorted(set.intersection(*(set(d['means']) for d in datasets.values())))
    rank_scores = {flow: {a: compare(datasets[a + '_' + flow], datasets['2D'], 'cpd', rank_circuits)
                         for a in ARCHES} for flow in ('baseline', 'paper')}
    ranks = {flow: sorted(ARCHES, key=lambda a: rank_scores[flow][a]['geomean_change_percent'])
             for flow in rank_scores}
    write_json(out, dict(utc=utc(), evidence_kind='author-published CSV reanalysis, NOT local replication',
        source_commit='84ba44acf1bad597bc5a9d1f615415870e178a86',
        aggregation='arithmetic mean over ten seeds per circuit; geometric mean of circuit ratios',
        runtime='excluded: repository warns non-runtime CSVs were collected on a busy shared server',
        missing_data_policy='Failed rows retained; comparisons require all ten successful seeds per circuit; architecture ranking uses the global complete-circuit intersection',
        datasets=datasets, summary=summary, ranking_circuits=rank_circuits,
        rank_scores=rank_scores, architecture_ranks=ranks))
    for arch in ARCHES:
        s = summary[arch]['cpd']
        print(arch, 'CPD percent vs 3D / 2D:',
              round(s['paper_vs_same_arch_3D']['geomean_change_percent'], 4),
              round(s['paper_vs_common_2D']['geomean_change_percent'], 4))
    print(ranks)


if __name__ == '__main__':
    main()
