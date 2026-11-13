#!/usr/bin/env python3
"""Validate necessary source-cut analysis on sealed legal and failed controls."""
from pathlib import Path
from array import array
import collections
import json
import os
import resource
import shutil
import signal
import sys
import time

D = Path(__file__).resolve().parent
sys.path[:0] = [str(D.parents[1] / 'scripts'), str(D)]
import check_route as cr
import compare_lazagna_graphs as cg
import source_escape_cut as matching


def write(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')


def main():
    resource.setrlimit(resource.RLIMIT_AS, (32 * 1024**3, 32 * 1024**3))
    signal.alarm(1800)
    sources = {
        'clstm_legal': D / 'target_feedback_transfer_dev_02/runs/clstm_like.small_Tf',
        'robot_legal': D / 'target_feedback_transfer_expansion_dev_01/runs/robot_rl_Tf',
        'tpu_legal': D / 'target_feedback_transfer_expansion_dev_01/runs/tpu_like.small.os_Tf',
        'attention_legal': D / 'layer_bbox_dev_01/runs/attention_layer_A1',
        'attention_failed': D / 'target_feedback_scale_dev_01/runs/attention_layer_Tf',
    }
    out = D / 'source_escape_controls_01'
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    out.mkdir(exist_ok=False)
    shutil.copy2(__file__, out / 'runner.py')
    shutil.copy2(matching.__file__, out / 'source_escape_cut.py')
    paths = [out / 'runner.py', out / 'source_escape_cut.py', Path(cr.__file__), Path(cg.__file__)]
    manifests, graphs, traces = {}, {}, {}
    for name, rd in sources.items():
        m = json.loads((rd / 'manifest.json').read_text())
        assert json.loads((rd.parent.parent / 'input_seal.json').read_text())['passed']
        paths.extend([rd / 'manifest.json', rd / 'routed.route', rd.parent.parent / 'input_seal.json'])
        assert cr.sha256(rd / 'routed.route') == m['outputs']['routed.route']['sha256']
        if name.endswith('_legal'):
            assert m['status'] == 'completed' and m['metrics']['native_full_check_passed']
            assert json.loads((rd / 'independent_audit.json').read_text())['audit']['passed']
            paths.append(rd / 'independent_audit.json')
        else:
            assert m['status'] == 'failed'
        g = m['command'][m['command'].index('--read_rr_graph') + 1]
        graphs[g] = m['shared_inputs'][g]['sha256']
        manifests[name] = m
        traces[name] = cr.read_trace(rd / 'routed.route')
    assert len(graphs) == 1
    graph = Path(next(iter(graphs)))
    assert cr.sha256(graph) == graphs[str(graph)]
    paths.append(graph)
    bindings = {str(p): cr.sha256(p) for p in paths}
    write(out / 'registration.json', dict(question='Necessary first-exit matching must accept four independently '
        'legal native routes; failed attention has the same source mapping as its legal global-scope control, '
        'so a success of the matching test is not proof of routing success. Reuse one exact graph scan.',
        sources={k: str(v) for k, v in sources.items()}, bindings=bindings,
        pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
        memory_bytes=32 * 1024**3, timeout_seconds=1800, disk_reserve_bytes=80 * 1024**3, native_route_calls=0))
    started = time.monotonic()
    internal, capacities, edges = bytearray(), array('I'), collections.defaultdict(set)
    for section, e in cg.records(graph):
        if section == 'rr_nodes':
            assert int(e.get('id')) == len(internal)
            internal.append(e.get('type') in ['SOURCE', 'OPIN'])
            capacities.append(int(e.get('capacity')))
        elif section == 'rr_edges':
            u, v = int(e.get('src_node')), int(e.get('sink_node'))
            if internal[u]:
                edges[u].add(v)
    results, root_maps, closure_cache = {}, {}, {}
    for name, nets in traces.items():
        adj, used_exits, roots = {}, collections.Counter(), {}
        for net, data in nets.items():
            trace = data['trace']
            if not trace:
                continue
            root = trace[0].inode
            assert trace[0].kind == 'SOURCE'
            roots[net] = root
            if root not in closure_cache:
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
                closure_cache[root] = exits
            adj[net] = closure_cache[root]
            if name.endswith('_legal'):
                first = next(n.inode for n in trace if not internal[n.inode])
                assert first in adj[net]
                used_exits[first] += 1
        caps = {r: capacities[r] for rs in adj.values() for r in rs}
        result = matching.match_cuts(adj, caps)
        if name.endswith('_legal'):
            assert all(n <= capacities[r] for r, n in used_exits.items())
            assert result['matched'] == len(adj)
        results[name] = dict(native_status=manifests[name]['status'], nets=len(adj), matched=result['matched'],
                             unmatched=len(result['unmatched']), legal_constructive_assignment_checked=name.endswith('_legal'))
        root_maps[name] = roots
    assert root_maps['attention_legal'] == root_maps['attention_failed']
    assert results['attention_failed']['unmatched'] == 0
    checks = {p: cr.sha256(Path(p)) == h for p, h in bindings.items()}
    assert all(checks.values())
    write(out / 'input_seal.json', dict(passed=True, checks=checks))
    write(out / 'completion.json', dict(passed=True, results=results, attention_source_maps_identical=True,
        native_route_calls=0, wall_seconds=time.monotonic() - started,
        qualification='Necessary test only: all legal controls pass, and failed attention also passes. '
                      'Does not justify deleting failed cases or inferring feasibility from matching alone.'))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
