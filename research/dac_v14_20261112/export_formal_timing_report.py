#!/usr/bin/env python3
"""Export the sealed, circuit-balanced timing evidence into development-paper data."""
import csv
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
B = D / 'formal_timing_01'
P = D / 'paper'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    a = json.loads((B / 'analysis.json').read_text())
    assert a['sealed'] and a['batch_complete'] and a['statuses'] == {'legal': 45}
    assert json.loads((B / 'completion.json').read_text())['gated_cases'] == []
    rows = []
    for c, arms in a['medians'].items():
        for arm, m in arms.items():
            obs = [r for r in a['observations'] if r['circuit'] == c and r['arm'] == arm]
            assert len(obs) == 3 and m['complete']
            assert len({json.dumps([r['metrics']['critical_path_ns'], r['iterations'], r['physical_metrics']], sort_keys=True) for r in obs}) == 1
            r = obs[0]
            rows.append(dict(circuit=c, arm=arm, repetitions=3, status='legal',
                process_median_s=m['process_median'], process_max_s=m['process_max'],
                planning_median_s=m['planning_median'], router_median_s=m['router_median'],
                peak_rss_median_kib=m['max_rss_kib_median'], peak_rss_max_kib=m['max_rss_kib_max'],
                cpd_ns=r['metrics']['critical_path_ns'], iterations=r['iterations'],
                sb_occupancy=r['physical_metrics']['sb_pair_net_occupancy'],
                cb_occupancy=r['physical_metrics']['cb_crossing_output_source_net_occupancy']))
    csv_path = P / 'data/formal_timing_v14.csv'
    with csv_path.open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    tex = [r'\begin{table*}[t]', r'\centering\small',
        r'\caption{Sealed same-environment timing on five previously seen, mutually legal circuits, with three rotated repetitions per arm. Full-process and planning times are per-circuit medians in seconds. U is frozen full-net feedback with exact closure views.}',
        r'\label{tab:formal-v14}', r'\begin{tabular}{lrrrrrrrr}', r'\hline',
        r'Circuit & A0 process & R1 process & U process & U/A0 & U/R1 & R1 plan & U plan & U peak RSS (GiB)\\', r'\hline']
    md = ['# Sealed formal timing: A0 / old R1 / full-feedback closure-view U', '',
        'Five seen, mutually legal circuits; Hybrid-O/P0/W100, seed 11, three rotated orders. All 45 roles legal; no gated cases. Each complete route and quality record passed the registered reference-reuse gate. Inputs were sealed after execution. Shared host; study heavy jobs excluded; fixed CPU 0; uniform input prewarming. This is neither a blind cohort nor a success-rate experiment.', '',
        '| Circuit | A0 process s | R1 process s | U process s | U/A0 | U/R1 | R1 planning s | U planning s |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for c, arms in a['medians'].items():
        x, y, z = (arms[k] for k in ['A0', 'R1', 'U'])
        vals = [x['process_median'], y['process_median'], z['process_median'], z['process_median']/x['process_median'], z['process_median']/y['process_median'], y['planning_median'], z['planning_median']]
        tex.append(c.replace('_', r'\_') + ' & ' + ' & '.join(f'{v:.3f}' for v in vals + [z['max_rss_kib_median']/1048576]) + r'\\')
        md.append('| ' + c + ' | ' + ' | '.join(f'{v:.6f}' for v in vals) + ' |')
    tex.extend([r'\hline', r'\end{tabular}', r'\end{table*}', ''])
    (P / 'data/formal_timing_v14.tex').write_text('\n'.join(tex))
    comp = a['comparisons']
    reduction = (1-comp['R1->U']['circuit_geomean_new_over_reference'])*100
    overhead = (comp['A0->U']['circuit_geomean_new_over_reference']-1)*100
    md.extend(['', f'Circuit-geometric U/R1 process-time reduction: {reduction:.6f}%; U/A0 overhead: {overhead:.6f}%. Every circuit is faster than old R1 and slower than A0. These ratios include guide-feedback differences as well as reuse and do not isolate the cache contribution.', '',
        'CSV retains legal CPD, iterations, actual SB/CB occupancy, process median/max, planning/router components and peak RSS median/max. All raw repetitions, GNU time counters and paired ratios remain in analysis.json. RSS is GNU time peak resident set size in Linux KiB, not a simultaneous process-tree sum. Component times are never added to full-process wall. Attention remains failed in the separate six-circuit quality denominator. Tf, pressure and retained-prefix variants are outside this timing claim.', ''])
    (B / 'final_report.md').write_text('\n'.join(md))
    sources = ['analysis.json', 'completion.json', 'input_seal.json', 'registration.json']
    receipt = dict(status='sealed_export_passed', source_sha256={n:sha(B/n) for n in sources},
        exporter_sha256=sha(Path(__file__)), artifacts_sha256={str(p.relative_to(D)):sha(p) for p in [csv_path, P/'data/formal_timing_v14.tex', B/'final_report.md']},
        all_roles=45, legal_roles=45, circuits=5, repetitions=3,
        process_reduction_vs_R1_pct=reduction, process_overhead_vs_A0_pct=overhead,
        qualification='Frozen full-feedback closure-view U only; no cache-only causal attribution or broader quality/success claim.')
    (B / 'final_report_binding.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    main()
