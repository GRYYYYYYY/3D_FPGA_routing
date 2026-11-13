#!/usr/bin/env python3
"""Find necessary first-exit cuts under recorded native SOURCE assignments."""
from pathlib import Path
from array import array
import argparse
import collections
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
import compare_lazagna_graphs as cg
import source_escape_cut as matching


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (32 * 1024**3, 32 * 1024**3))
    signal.alarm(1800)
    batch = D / 'target_feedback_transfer_dev_02'
    assert json.loads((batch / 'input_seal.json').read_text())['passed']
    source = batch / 'runs/conv_layer_A1'
    manifest = json.loads((source / 'manifest.json').read_text())
    assert manifest['status'] == 'failed'
    graph = Path(manifest['command'][manifest['command'].index('--read_rr_graph') + 1])
    assert cr.sha256(graph) == manifest['shared_inputs'][str(graph)]['sha256']
    assert cr.sha256(source / 'routed.route') == manifest['outputs']['routed.route']['sha256']
    traces = cr.read_trace(source / 'routed.route')
    roots = {n: t['trace'][0].inode for n, t in traces.items() if t['trace']}
    names = {n: t['name'] for n, t in traces.items()}
    assert all(t['trace'][0].kind == 'SOURCE' and any(x.kind == 'SINK' for x in t['trace'])
               for t in traces.values() if t['trace'])
    source_identity = {}
    for arm in ['F', 'V', 'Tf']:
        p = batch / 'runs' / f'conv_layer_{arm}' / 'routed.route'
        other = cr.read_trace(p)
        assert roots == {n: t['trace'][0].inode for n, t in other.items() if t['trace']}
        source_identity[str(p)] = cr.sha256(p)
    out = D / args.out
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    out.mkdir(exist_ok=False)
    shutil.copy2(__file__, out / 'runner.py')
    shutil.copy2(matching.__file__, out / 'source_escape_cut.py')
    paths = [source / 'manifest.json', source / 'routed.route', graph, batch / 'input_seal.json',
             out / 'runner.py', out / 'source_escape_cut.py', Path(cr.__file__), Path(cg.__file__),
             D / 'test_source_escape_cut.py', D / 'source_escape_unit.log']
    bindings = {str(p): cr.sha256(p) for p in paths} | source_identity
    write(out / 'registration.json', dict(question='Can every recorded routed net occupy at least one '
          'first resource outside its complete SOURCE/OPIN closure, with native RR capacities? '
          'An exact Hall deficit proves a necessary obstruction conditional on this SOURCE mapping; '
          'matching success does not prove routability. No bounding-box restriction, guide, '
          'timing approximation, or new route call.', bindings=bindings, source=str(source),
          pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
          memory_bytes=32 * 1024**3, timeout_seconds=1800, disk_reserve_bytes=80 * 1024**3))
    started = time.monotonic()
    internal = bytearray()
    capacities = array('I')
    edges = collections.defaultdict(list)
    for section, element in cg.records(graph):
        if section == 'rr_nodes':
            node = int(element.get('id'))
            assert node == len(internal)
            internal.append(element.get('type') in ['SOURCE', 'OPIN'])
            capacities.append(int(element.get('capacity')))
        elif section == 'rr_edges':
            u, v = int(element.get('src_node')), int(element.get('sink_node'))
            if internal[u]:
                edges[u].append(v)
    neighbors, closures = {}, {}
    for net, root in roots.items():
        assert internal[root]
        todo, seen, exits = [root], set(), set()
        while todo:
            u = todo.pop()
            if u in seen:
                continue
            seen.add(u)
            for v in edges[u]:
                if internal[v]:
                    todo.append(v)
                else:
                    exits.add(v)
        neighbors[net], closures[net] = sorted(exits), sorted(seen)
    cut_caps = {r: capacities[r] for rs in neighbors.values() for r in rs}
    result = matching.match_cuts(neighbors, cut_caps)
    write(out / 'matching.json', result)
    witness_nets = set(result['aggregate_witness']['nets']) if result['aggregate_witness'] else set()
    witness_resources = {r for n in witness_nets for r in neighbors[n]}
    certificate = dict(nets={n: dict(name=names[n], source=roots[n], internal_closure=closures[n],
                       all_exit_resources=neighbors[n]) for n in sorted(witness_nets)},
                       capacities={r: capacities[r] for r in sorted(witness_resources)},
                       witness=result['aggregate_witness'], individual_witnesses=result['witnesses'])
    write(out / 'certificate.json', certificate)
    checks = {p: cr.sha256(Path(p)) == h for p, h in bindings.items()}
    write(out / 'input_seal.json', dict(passed=all(checks.values()), checks=checks))
    assert all(checks.values())
    write(out / 'completion.json', dict(status='necessary_cut_diagnostic_complete', native_route_calls=0,
          matched=result['matched'], total=result['total'], unmatched=len(result['unmatched']),
          individual_witnesses=len(result['witnesses']), wall_seconds=time.monotonic() - started,
          qualification='Conditional on the SOURCE mapping recorded identically by F/V/Tf/A1. '
                        'No independent atom-to-terminal certification or unrestricted-placement claim. '
                        'An independent graph-stream certificate verification is still required.'))
    print(json.dumps({k: v for k, v in result.items() if k not in ['assignments', 'witnesses', 'aggregate_witness', 'unmatched']}))


if __name__ == '__main__':
    main()
