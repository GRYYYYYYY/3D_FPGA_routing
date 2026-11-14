"""Stream actual routed resources and identify slack-bearing release scopes.

Release counts describe removal from the current tree before a replacement;
they are neither final savings nor guarantees of a feasible replacement. A
terminal-layer cut reference ignores topology, capacity and SB/CB substitution.
"""
import collections
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from check_route import NET_RE, NODE_RE, TraceNode, coordinates


def stream_trace(path):
    """Yield the reference route parser's nets one at a time, including branches."""
    current = None
    seen = set()
    with Path(path).open() as stream:
        for number, line in enumerate(stream, 1):
            header = NET_RE.match(line)
            if header:
                if current is not None:
                    yield current
                current = None
                if 'global net' not in header[3]:
                    net = int(header[1])
                    assert net not in seen, ('duplicate net', net)
                    seen.add(net)
                    current = dict(net=net, name=header[2], trace=[])
            elif line.startswith('Node:'):
                match = NODE_RE.match(line)
                assert match is not None and current is not None, ('route format', number)
                low = coordinates(match[3])
                current['trace'].append(TraceNode(
                    int(match[1]), match[2], low,
                    coordinates(match[4]) if match[4] else low,
                    int(match[5]), int(match[6]) if match[6] else None))
    if current is not None:
        yield current


def tree_data(trace, metadata):
    """Recover actual directed tree edges and pin sets without a delay proxy."""
    root = trace[0].inode
    parent = {}
    sink_by_pin = {}
    for first, second in zip(trace, trace[1:]):
        if first.switch == -1:
            continue
        value = (first.inode, first.switch)
        assert second.inode not in parent or parent[second.inode] == value
        parent[second.inode] = value
    for node in trace:
        m = metadata(node.inode)
        assert (node.kind, node.low, node.high) == (m['kind'], m['low'], m['high'])
        if node.kind == 'SINK':
            assert node.pin is not None and node.pin > 0
            assert node.pin not in sink_by_pin or sink_by_pin[node.pin] == node.inode
            sink_by_pin[node.pin] = node.inode
    used = {n.inode for n in trace}
    assert root not in parent and set(parent) | {root} == used
    descendants = collections.defaultdict(set)
    paths = {}
    for pin, sink in sink_by_pin.items():
        path = [sink]
        while path[-1] != root:
            path.append(parent[path[-1]][0])
            assert len(path) <= len(used), 'Cycle in native tree'
        paths[pin] = path
        for node in path:
            descendants[node].add(pin)
    assert set(descendants) == used, 'A native branch has no terminal'
    crossing = {}
    sb = set()
    cb = set()
    for node, (up, switch) in parent.items():
        a, b = metadata(up), metadata(node)
        if a['low'][2] != b['low'][2]:
            if a['kind'] == 'OPIN':
                kind = 'CB'
                cb.add(up)
            else:
                assert a['kind'] == 'CHANX' and a['direction'] == 'NONE'
                kind = 'SB'
                sb.add(up)
            crossing[node] = dict(up=up, resource_kind=kind, resource=up,
                                  from_layer=a['low'][2], to_layer=b['low'][2])
    terminal_layers = {metadata(root)['low'][2]} | {metadata(n)['low'][2] for n in sink_by_pin.values()}
    assert len(terminal_layers) <= 2 and max(terminal_layers) - min(terminal_layers) <= 1
    cut_reference = int(len(terminal_layers) > 1)
    # The audited adapter has single-layer RR nodes and one-boundary crossings.
    assert all(metadata(n)['low'][2] == metadata(n)['high'][2] for n in used)
    assert all(abs(r['from_layer'] - r['to_layer']) == 1 for r in crossing.values())
    assert len(sb) + len(cb) >= cut_reference
    excursions = []
    for node, cross in crossing.items():
        pins = descendants[node]
        if {metadata(sink_by_pin[p])['low'][2] for p in pins} == {cross['from_layer']}:
            excursions.append(dict(node=node, **cross, pins=sorted(pins)))
    return dict(root=root, used=used, parent=parent, sinks=sink_by_pin,
                descendants=descendants, paths=paths, crossing=crossing,
                SB=sb, CB=cb, layer_cut_reference=cut_reference, excursions=excursions)


def release_scope(tree, pins, metadata):
    """Count terminal-path removal; native pruning/nonconfigurable closure remains separate."""
    pins = set(pins)
    assert pins and pins <= tree['sinks'].keys()
    touched = set().union(*(set(tree['paths'][p]) for p in pins))
    removed = {n for n in touched if n != tree['root'] and tree['descendants'][n] <= pins}
    kept = {k: set() for k in ['SB', 'CB']}
    for node, edge in tree['crossing'].items():
        if node not in removed:
            kept[edge['resource_kind']].add(edge['resource'])
    return dict(pins=sorted(pins), released_nodes=sorted(removed),
                released_SB=sorted(tree['SB'] - kept['SB']),
                released_CB=sorted(tree['CB'] - kept['CB']),
                released_wire=sum(wire_units(metadata(n)) for n in removed))


def wire_units(meta):
    """Use precisely the existing physical auditor's planar-wire definition."""
    if meta['kind'] not in ['CHANX', 'CHANY'] or meta['direction'] == 'NONE':
        return 0
    return 1 + abs(meta['high'][0] - meta['low'][0]) + abs(meta['high'][1] - meta['low'][1])


def pin_screen(pins, sta, worst, minimum_margin_s):
    """Screen current slack only; native final STA must check every replacement."""
    rows = []
    for pin in pins:
        p = sta.get(pin)
        known = p is not None and isinstance(p['slack_s'], (float, int)) and math.isfinite(p['slack_s'])
        margin = p['slack_s'] - worst if known else None
        rows.append(dict(pin=pin, slack_s=None if p is None else p['slack_s'],
                         margin_s=margin, raw_criticality=None if p is None else p['criticality'],
                         eligible=bool(known and not p['ignored'] and not p['global'] and margin > minimum_margin_s)))
    return dict(eligible=all(r['eligible'] for r in rows), pins=rows,
                minimum_margin_s=min((r['margin_s'] for r in rows if r['margin_s'] is not None), default=None),
                unknown_pins=sum(r['margin_s'] is None for r in rows))
