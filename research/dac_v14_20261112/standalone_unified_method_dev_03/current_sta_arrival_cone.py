"""Current endpoint selection and exact native float32 maximum-arrival tracing.

Read-only scheduling evidence. Never substitutes for final native FULL/STA.
"""
import argparse
import json
import math
import struct
import time
from pathlib import Path
from native_timing_echo_v2 import read_echo
from retained_prefix_workflow import read, write, sha


def f32(value):
    return struct.unpack('f', struct.pack('f', value))[0]


def trace(graph, roots, launch):
    arrivals = {node: value for (typ, entity, node, l, c), value in graph['tags'].items()
                if typ == 'SETUP_DATA_ARRIVAL' and entity == 'node' and (l, c) == (launch, -1)}
    seen, selected, sources, unresolved, fanins = set(), set(), [], [], []
    todo = list(roots)
    while todo:
        node = todo.pop()
        if node in seen:
            continue
        seen.add(node)
        if node not in arrivals:
            unresolved.append(dict(node=node, reason='missing matching arrival domain'))
            continue
        if graph['nodes'][node]['type'] == 'SOURCE':
            sources.append(node)
            continue
        choices = []
        for edge in graph['nodes'][node]['in_edges']:
            e = graph['edges'][edge]
            if e['disabled'] or e['src_node'] not in arrivals or 'max_delay' not in graph['delays'][edge]:
                continue
            proposal = f32(arrivals[e['src_node']] + graph['delays'][edge]['max_delay'])
            choices.append(dict(edge=edge, source=e['src_node'], proposal_s=proposal,
                                gap_s=arrivals[node]-proposal))
        if not choices or max(p['proposal_s'] for p in choices) != arrivals[node]:
            unresolved.append(dict(node=node, reason='native maximum recurrence not reproduced'))
            continue
        wins = [p for p in choices if p['proposal_s'] == arrivals[node]]
        fanins.append(dict(node=node, arrival_s=arrivals[node], choices=choices,
                           winning_edges=[p['edge'] for p in wins]))
        for p in wins:
            selected.add(p['edge'])
            todo.append(p['source'])
    return dict(nodes=sorted(seen), edges=sorted(selected), sources=sorted(sources),
                unresolved=unresolved, fanins=fanins)


def select(state, near_ns=0.):
    assert math.isfinite(near_ns) and near_ns >= 0
    state = Path(state)
    complete = read(state/'completion.json')
    assert complete['passed']
    run = Path(complete['run'])
    vector = read(state/'endpoint_vector.json')
    graph = read_echo(run/'timing_graph.full_precision.echo')
    worst = min(vector['setup'].values())
    endpoints = [dict(identity=json.loads(key), slack_s=value) for key, value in vector['setup'].items()
                 if value <= worst + near_ns*1e-9]
    groups = {}
    for ep in endpoints:
        node, atom, name, launch, capture = ep['identity']
        assert graph['nodes'][node]['type'] == 'SINK'
        assert graph['tags'][('SETUP_SLACK','node',node,launch,capture)] == ep['slack_s']
        groups.setdefault(launch, []).append(node)
    cones = {launch: trace(graph, roots, launch) for launch, roots in groups.items()}
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
    files = [Path(__file__).resolve(), Path(__file__).with_name('native_timing_echo_v2.py'),
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
