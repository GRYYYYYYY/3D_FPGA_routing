#!/usr/bin/env python3
"""Bounded, read-only audit of failed fixed-parameter transfer artifacts."""
from pathlib import Path
import argparse
import collections
import csv
import json
import os
import resource
import shutil
import signal
import sys
import time

D = Path(__file__).resolve().parent
ROOT = D.parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(D)]
import check_route as cr
import flatland_benchmark as study
import compare_lazagna_graphs
import routing_log_metrics
from compare_lazagna_graphs import records
from routing_log_metrics import last_iteration


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def analyze_saved(source, evidence, output):
    audit = cr.audit(evidence['graph_path'], source / 'routed.route', graph_evidence=evidence)
    traces = cr.read_trace(source / 'routed.route')
    occupancy = collections.Counter()
    nets = collections.defaultdict(set)
    entries, exits = set(), set()
    for net, data in traces.items():
        trace = data['trace']
        for node in {n.inode for n in trace}:
            occupancy[node] += 1
            nets[node].add(net)
        for a, b in zip(trace, trace[1:]):
            if a.switch != -1 and a.low[2] != b.low[2]:
                entries.add(a.inode)
                exits.add(b.inode)
    overused = []
    affected = collections.defaultdict(set)
    for node, count in occupancy.items():
        meta = evidence['nodes'][node]
        if count <= meta['capacity']:
            continue
        overused.append(dict(node=node, occupancy=count, capacity=meta['capacity'],
                             kind=meta['kind'], low=meta['low'], high=meta['high'],
                             is_used_crossing_entry=node in entries,
                             is_used_crossing_destination=node in exits,
                             nets=sorted(nets[node])))
        for net in nets[node]:
            affected[net].add(node)
    assert len(overused) == audit['route']['overused_rr_nodes']
    guide_path = source / 'h3d_final_guides.csv'
    guides = set()
    if guide_path.exists():
        with guide_path.open() as stream:
            guides = {(int(r['net']), int(r['pin'])) for r in csv.DictReader(stream)}
    guided_nets = {n for n, _ in guides}
    connections, remote, guided = set(), set(), set()
    descendant_rows = []
    for net, resources in sorted(affected.items()):
        trace = traces[net]['trace']
        children = collections.defaultdict(set)
        sinks = {n.inode: (n.pin, n.low[2]) for n in trace if n.kind == 'SINK'}
        for a, b in zip(trace, trace[1:]):
            if a.switch != -1:
                children[a.inode].add(b.inode)
        for node in sorted(resources):
            todo, seen, descendants = [node], set(), []
            while todo:
                u = todo.pop()
                if u in seen:
                    continue
                seen.add(u)
                if u in sinks:
                    pin, layer = sinks[u]
                    key = net, pin
                    connections.add(key)
                    if layer != trace[0].low[2]:
                        remote.add(key)
                    if key in guides:
                        guided.add(key)
                    descendants.append(dict(pin=pin, sink=u, remote=key in remote, guided=key in guides))
                todo.extend(children[u])
            descendant_rows.append(dict(net=net, overused_node=node, connections=descendants))
    physical = study.physical_route_metrics(source / 'routed.route', evidence)
    summary = dict(overused_rr_nodes=len(overused),
                   overused_by_kind=dict(collections.Counter(r['kind'] for r in overused)),
                   overused_crossing_entries=sum(r['is_used_crossing_entry'] for r in overused),
                   overused_crossing_destinations=sum(r['is_used_crossing_destination'] for r in overused),
                   affected_nets=len(affected), affected_nets_with_final_guides=len(set(affected) & guided_nets),
                   affected_connections=len(connections), remote_connections=len(remote),
                   same_layer_connections=len(connections - remote), guided_connections=len(guided))
    write(output / 'scoped_audit.json', audit)
    result = dict(native_status='failed', not_legal_qor=True, source=str(source),
                  physical_metrics_of_saved_failed_artifact=physical,
                  native_last_iteration=last_iteration((source / 'stdout.log').read_text().splitlines()),
                  summary=summary, overused=overused, descendant_events=descendant_rows,
                  saved_route_summary=audit['route'], scoped_audit_passed=audit['passed'],
                  audit_error_count=len(audit['errors']), caveats=audit['not_checked'],
                  qualification='Saved failed artifact, not legal QoR or necessarily last-iteration state. '
                                'Final guide membership does not prove guidance at all earlier iterations. '
                                'No causal attribution or atom-pin STA certification.')
    write(output / 'analysis.json', result)
    return dict(summary=summary, physical_metrics=physical, source=str(source))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', default='target_feedback_transfer_dev_02')
    parser.add_argument('--circuit', default='conv_layer')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (32 * 1024**3, 32 * 1024**3))
    signal.alarm(1800)
    batch = D / args.batch
    assert json.loads((batch / 'input_seal.json').read_text())['passed']
    reg = json.loads((batch / 'registration.json').read_text())
    refs = json.loads((batch / f'{args.circuit}_references.json').read_text())
    sources = {a: Path(r['path']) for a, r in refs.items()}
    sources.update({a: batch / 'runs' / f'{args.circuit}_{a}' for a in reg['arms']})
    sources = {a: p for a, p in sources.items() if json.loads((p / 'manifest.json').read_text())['status'] == 'failed'}
    assert sources
    out = D / args.out
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    out.mkdir(exist_ok=False)
    shutil.copy2(__file__, out / 'runner.py')
    ctx = study.context(args.circuit, reg['family'], reg['seed'], reg['width'])
    graph = Path(ctx['fixture']['original_graph'])
    paths = [batch / 'input_seal.json', batch / 'registration.json', batch / f'{args.circuit}_references.json',
             graph, Path(ctx['model_path']), out / 'runner.py', Path(cr.__file__), Path(study.__file__),
             Path(compare_lazagna_graphs.__file__), Path(routing_log_metrics.__file__)]
    graph_digest = cr.sha256(graph)
    for source in sources.values():
        manifest = json.loads((source / 'manifest.json').read_text())
        native_graph = manifest['command'][manifest['command'].index('--read_rr_graph') + 1]
        assert manifest['shared_inputs'][native_graph]['sha256'] == graph_digest
        assert cr.sha256(source / 'routed.route') == manifest['outputs']['routed.route']['sha256']
        paths.extend(source / f for f in ['manifest.json', 'routed.route', 'stdout.log'])
        if (source / 'h3d_final_guides.csv').exists():
            paths.append(source / 'h3d_final_guides.csv')
    bindings = {str(p): cr.sha256(p) for p in paths}
    write(out / 'registration.json', dict(question='Do failed transfer routes retain crossing overuse or mostly '
                                         'unguided planar conflicts? Compare all failed A0/R1/F/V/Tf/A1 artifacts '
                                         'without new routing, preserving failed status.',
                                         sources={a: str(p) for a, p in sources.items()}, bindings=bindings,
                                         pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
                                         timeout_seconds=1800, memory_bytes=32 * 1024**3, disk_reserve_bytes=80 * 1024**3,
                                         native_route_calls=0))
    start = time.monotonic()
    cr.graph_records = records
    evidence = cr.batch_graph_evidence(graph, [p / 'routed.route' for p in sources.values()])
    evidence['graph_path'] = graph
    results = {}
    for arm, source in sources.items():
        (out / arm).mkdir()
        results[arm] = analyze_saved(source, evidence, out / arm)
    checks = {p: cr.sha256(Path(p)) == h for p, h in bindings.items()}
    write(out / 'input_seal.json', dict(passed=all(checks.values()), checks=checks))
    assert all(checks.values())
    write(out / 'summary.json', dict(passed=True, native_route_calls=0, results=results,
                                    qualification='Failure artifacts only; no success/QoR promotion or causal attribution.'))
    write(out / 'completion.json', dict(status='read_only_diagnostic_complete', wall_seconds=time.monotonic() - start))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
