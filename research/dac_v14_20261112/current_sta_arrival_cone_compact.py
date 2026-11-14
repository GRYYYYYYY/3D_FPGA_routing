"""Current endpoint selection and exact native float32 maximum-arrival tracing.

Read-only scheduling evidence. Never substitutes for final native FULL/STA.
"""
import argparse
import json
import math
import struct
import time
from pathlib import Path
from compact_timing_cone import read_compact,trace_compact
from retained_prefix_workflow import read, write, sha


def f32(value):
    return struct.unpack('f', struct.pack('f', value))[0]


def select(state, near_ns=0.):
    assert math.isfinite(near_ns) and near_ns >= 0
    state = Path(state)
    complete = read(state/'completion.json')
    assert complete['passed']
    run = Path(complete['run'])
    vector = read(state/'endpoint_vector.json')
    worst = min(vector['setup'].values())
    endpoints = [dict(identity=json.loads(key), slack_s=value) for key, value in vector['setup'].items()
                 if value <= worst + near_ns*1e-9]
    graph = read_compact(run/'timing_graph.full_precision.echo', {e['identity'][3] for e in endpoints}, {(e['identity'][0],e['identity'][3],e['identity'][4]) for e in endpoints})
    groups = {}
    for ep in endpoints:
        node, atom, name, launch, capture = ep['identity']
        assert graph['kinds'][node] == 'SINK'
        assert graph['slacks'][node,launch,capture] == ep['slack_s']
        groups.setdefault(launch, []).append(node)
    cones = {launch: trace_compact(graph, roots, launch) for launch, roots in groups.items()}
    nodes = set().union(*(set(c['nodes']) for c in cones.values()))
    pins = []
    for line in (run/'native_sta_frontier.jsonl').open():
        p = json.loads(line)
        if p.get('type') != 'pin' or p['driver'] or p['ignored'] or p['global'] or not p['route_tree_present']:
            continue
        matched = [a for a in p['atoms'] if a['tnode_external'] in nodes]
        if matched:
            pins.append(dict(net=p['net'], pin=p['pin'], net_name=p['net_name'], pin_name=p['pin_name'],
                             native_net_delay_s=p['native_net_delay_s'], setup_slack_s=p['setup_slack_s'], atoms=matched))
    files = [Path(__file__).resolve(), Path(__file__).with_name('compact_timing_cone.py'), Path(__file__).with_name('current_sta_arrival_cone.py'),
             state/'completion.json', state/'endpoint_vector.json', run/'timing_graph.full_precision.echo',
             run/'native_sta_frontier.jsonl', run/'routed.route']
    return dict(passed=all(not c['unresolved'] for c in cones.values()), source_state=str(state.resolve()),
                near_ns=near_ns, worst_slack_s=worst, selected_endpoints=endpoints,
                cones=cones, routed_connections=pins,
                unresolved_non_source_nodes=[u for c in cones.values() for u in c['unresolved']],
                source_sha256={str(p):sha(p) for p in files},
                qualification='All exact maximum-arrival predecessors of current selected endpoints, grouped by launch domain. '
                'No selection tolerance; includes every exact winning fanin. Unknown recurrence prevents certification. '
                'May rank strict-CPD work; not a global filter for endpoint-Pareto opportunities, clocks or pin remapping.')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--near-ns', type=float, default=0.)
    args = p.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    result = select(args.state, args.near_ns)
    result['complete_process_seconds'] = time.monotonic()-started
    write(args.output, result)
    print(dict(passed=result['passed'], endpoints=len(result['selected_endpoints']),
               connections=[(p['net'],p['pin']) for p in result['routed_connections']],
               seconds=result['complete_process_seconds']), flush=True)
