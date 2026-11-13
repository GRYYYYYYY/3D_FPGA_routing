#!/usr/bin/env python3
"""Verify a Hall cut directly from graph edges, without the matching algorithm."""
from pathlib import Path
import argparse
import json
import os
import resource
import signal
import sys
import time

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D.parents[1] / 'scripts'))
import check_route as cr


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--diagnostic', default='source_escape_diagnostic_01')
    parser.add_argument('--out', default='source_escape_verification_01.json')
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (32 * 1024**3, 32 * 1024**3))
    signal.alarm(1800)
    B = D / args.diagnostic
    seal = json.loads((B / 'input_seal.json').read_text())
    assert seal['passed']
    cert = json.loads((B / 'certificate.json').read_text())
    assert cert['witness'], 'No deficient cut to verify'
    reg = json.loads((B / 'registration.json').read_text())
    source = Path(reg['source'])
    manifest = json.loads((source / 'manifest.json').read_text())
    graph = Path(manifest['command'][manifest['command'].index('--read_rr_graph') + 1])
    assert cr.sha256(graph) == manifest['shared_inputs'][str(graph)]['sha256']
    traces = cr.read_trace(source / 'routed.route')
    claimed_internal = {u for r in cert['nets'].values() for u in r['internal_closure']}
    claimed_exits = {int(u) for u in cert['capacities']}
    relevant = claimed_internal | claimed_exits
    edges = {u: set() for u in claimed_internal}
    metadata = {}
    out = D / args.out
    assert not out.exists()
    paths = [B / 'certificate.json', B / 'input_seal.json', B / 'registration.json',
             graph, source / 'manifest.json', source / 'routed.route', Path(__file__), Path(cr.__file__)]
    bindings = {str(p): cr.sha256(p) for p in paths}
    (out.with_suffix('.registration.json')).write_text(json.dumps(dict(bindings=bindings,
        pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
        question='Independently verify the claimed cut by streaming native XML with the standard-library parser, '
                 'without importing or calling the matching implementation.', timeout_seconds=1800,
        memory_bytes=32 * 1024**3), indent=2) + '\n')
    start = time.monotonic()
    # Deliberately use the original ElementTree parser, not the diagnostic's lxml iterator.
    for section, element in cr.graph_records(graph):
        if section == 'rr_nodes':
            u = int(element.get('id'))
            if u in relevant:
                loc = element.find('loc').attrib
                metadata[u] = dict(kind=element.get('type'), capacity=int(element.get('capacity')),
                    low=[int(loc['xlow']), int(loc['ylow']), int(loc.get('layer_low', loc.get('layer', 0)))])
        elif section == 'rr_edges':
            u, v = int(element.get('src_node')), int(element.get('sink_node'))
            if u in claimed_internal:
                edges[u].add(v)
    assert set(metadata) == relevant
    assert all(metadata[u]['kind'] in ['SOURCE', 'OPIN'] for u in claimed_internal)
    assert all(metadata[u]['kind'] not in ['SOURCE', 'OPIN'] for u in claimed_exits)
    neighborhoods = {}
    for name, record in cert['nets'].items():
        n = int(name)
        assert traces[n]['name'] == record['name']
        assert traces[n]['trace'][0].inode == record['source']
        assert metadata[record['source']]['kind'] == 'SOURCE'
        assert any(t.kind == 'SINK' for t in traces[n]['trace'])
        todo, seen, outside = [record['source']], set(), set()
        while todo:
            u = todo.pop()
            if u in seen:
                continue
            seen.add(u)
            for v in edges[u]:
                assert v in relevant, 'Unreported outgoing edge invalidates the cut'
                if metadata[v]['kind'] in ['SOURCE', 'OPIN']:
                    todo.append(v)
                else:
                    outside.add(v)
        assert seen == set(record['internal_closure'])
        assert outside == set(record['all_exit_resources'])
        neighborhoods[n] = outside
    for u in claimed_exits:
        assert metadata[u]['capacity'] == cert['capacities'][str(u)]
    for w in [cert['witness']] + cert['individual_witnesses']:
        union = {r for n in w['nets'] for r in neighborhoods[n]}
        capacity = sum(metadata[r]['capacity'] for r in union)
        assert union == set(w['resources'])
        assert len(w['nets']) == w['demand'] > capacity == w['capacity']
        assert w['deficit'] == w['demand'] - w['capacity']
    checks = {p: cr.sha256(Path(p)) == h for p, h in bindings.items()}
    assert all(checks.values())
    summary = {k: v for k, v in cert['witness'].items() if k not in ['nets', 'resources']}
    result = dict(passed=True, independent_graph_parser='xml.etree.ElementTree', matching_algorithm_called=False,
                  aggregate=summary, verified_net_sources=len(cert['nets']), verified_exit_resources=len(claimed_exits),
                  source_metadata={int(r['source']): metadata[int(r['source'])] for r in cert['nets'].values()},
                  all_exit_metadata={u: metadata[u] for u in claimed_exits},
                  input_sha256=bindings, input_seal=checks, wall_seconds=time.monotonic() - start,
                  qualification='Necessary first-exit cut under the recorded fixed SOURCE assignments: '
                                'each distinct net must occupy at least one exit resource. Sum of RR capacities '
                                'is smaller than demand, even without a bounding box. This proves infeasibility '
                                'conditional on those assignments, not for alternative placements or pin mappings. '
                                'The deficit bounds excess net occupancy, not the number of overused nodes.')
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, aggregate=summary, wall_seconds=result['wall_seconds'])))


if __name__ == '__main__':
    main()
