#!/usr/bin/env python3
"""Read completed evidence; write only inside this manuscript directory."""
from pathlib import Path
import collections
import csv
import datetime
import hashlib
import json
import re

PAPER = Path(__file__).resolve().parent
ROOT = PAPER.parents[1]
BASE = ROOT / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
bindings = {}

def read(path):
    path = Path(path)
    data = path.read_bytes()
    bindings[str(path.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    return data.decode()

def js(name):
    return json.loads(read(BASE / name))

def compact_metric(d):
    return {k: v for k, v in d.items() if k not in ('per_sample',)}

evaluation = js('evaluation_analysis/summary.json')
rows = js('evaluation_analysis/role_observations.json')['rows']
panels = []
for family in ['sb', 'cb_o', 'hybrid_o']:
    for flow in ['p0', 'p1']:
        panel = evaluation['heldout'][family][flow]
        main = [r for r in rows if r['phase'] == 'heldout' and r['family'] == family and r['flow'] == flow]
        panels.append(dict(
            family=family, flow=flow,
            dual={k: compact_metric(v) if isinstance(v, dict) else v for k, v in panel['routing_dual'].items()},
            modern=compact_metric(panel['modern_lazagna_paired']),
            coverage={role: dict(collections.Counter(r['status'] for r in main if r['role'] == role)) for role in ['A0', 'R1', 'B2']},
        ))

mechanisms = []
for circuit in ['clstm_like.small', 'clstm_like.large']:
    pair = []
    for role in ['A0', 'R1']:
        row = next(r for r in rows if r['phase'] == 'heldout' and r['circuit'] == circuit and r['seed'] == 23 and r['family'] == 'hybrid_o' and r['flow'] == 'p0' and r['role'] == role)
        run = BASE / 'runs' / row['run']
        manifest = json.loads(read(run / 'manifest.json'))
        audit = json.loads(read(run / 'independent_audit.json'))
        paircheck = json.loads(read(run / 'pair_check.json'))
        log = read(run / 'stdout.log')
        report = read(run / 'report_timing.setup.rpt')
        final_counters = {}
        for line in log.splitlines():
            if line.startswith(('H3D_PLAN ', 'H3D_SCORE ', 'H3D_DELAY ', 'H3D_SCC ', 'H3D_TREE ', 'H3D_EDGE_ITER ')):
                final_counters[line.split()[0]] = line
        timing = {k: re.search(r'^' + k + r'\s*:\s*(.+)$', report, re.M).group(1) for k in ['Startpoint', 'Endpoint']}
        data_lines = report.split('data arrival time')[0].splitlines()
        timing['cell_output_increments_ns'] = sum(float(m.group(1)) for line in data_lines if (m := re.search(r'\.out\[\d+\].*?\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$', line)))
        timing['cell_input_increments_ns'] = sum(float(m.group(1)) for line in data_lines if (m := re.search(r'\.in\[\d+\].*?\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$', line)))
        timing['note'] = 'Sums of rounded report increments on each run\'s own worst path; input arcs include interconnect and local connectivity, not an independent RC decomposition.'
        audit_summary = {k:v for k,v in audit['audit'].items() if k != 'nets'}
        pair.append(dict(role=role, run=row['run'], metrics=manifest['metrics'], physical=audit['physical_metrics'], audit=audit_summary, audit_payload_note='Per-net audit detail remains in the original SHA256-bound independent_audit.json; not duplicated in the manuscript snapshot.', pair_check=paircheck, counters=final_counters, timing=timing, observed_process_seconds=manifest['wall_seconds']))
    mechanisms.append(dict(circuit=circuit, seed=23, family='hybrid_o', flow='p0', width=100, pair=pair, same_worst_path_endpoints=pair[0]['timing']['Startpoint'] == pair[1]['timing']['Startpoint'] and pair[0]['timing']['Endpoint'] == pair[1]['timing']['Endpoint']))

balance = js('balance_analysis/summary.json')
serial = js('serial_analysis/summary.json')
snapshot = dict(
    snapshot_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    scope='Completed strict main evaluation, serial timing and balance sensitivity. Paired-width remains separate and pending.',
    panels=panels,
    role_coverage={phase: {role: dict(collections.Counter(r['status'] for r in rows if r['phase'] == phase and r['role'] == role)) for role in ['A0','R1','B2']} for phase in sorted({r['phase'] for r in rows})},
    all_evaluation_role_counts=evaluation['role_status_counts'],
    unique_evaluation_counts=evaluation['unique_run_status_counts'],
    placement_only={f: compact_metric(evaluation['heldout'][f]['placement_only']) for f in ['sb','cb_o','hybrid_o']},
    factorial=evaluation['factorial_interactions'],
    rankings=evaluation['architecture_rankings'],
    ablations=evaluation['ablations'],
    diagnostics=evaluation['algorithm_diagnostics'],
    mechanisms=mechanisms,
    balance=dict(status_counts=dict(collections.Counter(r['status'] for r in balance['observations'])), comparisons=balance['comparisons'],observations=balance['observations']),
    serial={k:v for k,v in serial.items() if k not in ['source_sha256', 'evidence_source_sha256']},
    selected={f:v['R1'] for f,v in js('selected_configs.json')['selections'].items()},
    protocol=js('benchmark_protocol.json'),
    provenance_note='This is a manuscript extraction with SHA256 bindings, not the final full raw-artifact acceptance audit.'
)
for f in ['requirements.json']:
    read(BASE.parent/f)
extra = [BASE/n for n in ['partition_balance_sensitivity_protocol.json', 'execution_contract.json', 'measurement_interpretation.md', 'serial_protocol.json', 'mechanism_attribution_review_20261106.json']]
extra += [ROOT/'results/three_baselines_20261027/published_reference.json']
extra += [BASE/'execution_scripts'/n for n in ['analyze_flatland_evaluation.py', 'flatland_statistics.py', 'analyze_flatland_diagnostics.py', 'run_paired_width_diagnostic.py', 'analyze_paired_width_diagnostic.py']]
extra += [ROOT/'vendor/vtr-architecture-src/vpr/src/route'/n for n in ['h3d_fast_plan.cpp', 'h3d_delay_plan.cpp', 'h3d_routing.cpp', 'h3d_partition_dp.h', 'h3d_crossing.h', 'connection_router.tpp', 'route_net.tpp']]
balance_counts = collections.defaultdict(collections.Counter)
for f in sorted((BASE/'balance_cases').glob('*/balance_audit.json')):
    audit = json.loads(read(f))
    balance_counts[str(audit['balance_argument'])]['total'] += 1
    balance_counts[str(audit['balance_argument'])]['balanced'] += int(audit['balanced'])
snapshot['balance']['partition_audit_counts'] = dict(balance_counts)
for f in extra:
    read(f)
snapshot['source_sha256'] = bindings
(PAPER/'data/evidence_snapshot.json').write_text(json.dumps(snapshot,indent=2,ensure_ascii=False)+'\n')
with (PAPER/'data/main_results.csv').open('w') as f:
    writer = csv.writer(f)
    writer.writerow(['family', 'flow', 'complete_dual_circuits', 'vs_3d_improvement_percent', 'vs_2d_improvement_percent', 'legal_seed_pairs', 'wins', 'ties', 'losses', 'B2_complete_circuits', 'vs_B2_improvement_percent'])
    for panel in panels:
        dual = panel['dual']; metric = dual['vs_3d']
        writer.writerow([panel['family'], panel['flow'], len(dual['common_complete_circuits']), metric['geomean_improvement_percent'], dual['vs_2d']['geomean_improvement_percent'], metric['paired_legal_samples'], metric['improved_samples'], metric['tied_samples'], metric['regressed_samples'], len(panel['modern']['complete_circuits']), panel['modern']['geomean_improvement_percent']])
with (PAPER/'data/coverage.csv').open('w') as f:
    writer = csv.writer(f); writer.writerow(['family', 'flow', 'role', 'registered', 'legal', 'failed', 'timeout'])
    for panel in panels:
        for role, counts in panel['coverage'].items():
            writer.writerow([panel['family'], panel['flow'], role, 42, counts.get('legal',0), counts.get('failed',0), counts.get('timeout',0)])
print('Wrote',PAPER/'data/evidence_snapshot.json')
for p in panels:
    print(p['family'],p['flow'],p['coverage'])
for m in mechanisms:
    print('MECHANISM',m['circuit'],'same endpoints',m['same_worst_path_endpoints'])
    for r in m['pair']:
        print(r['role'],r['metrics'],r['physical'],r['counters'],{k:v for k,v in r['timing'].items() if k not in ['Startpoint','Endpoint']})
print('BALANCE',snapshot['balance']['status_counts'])
