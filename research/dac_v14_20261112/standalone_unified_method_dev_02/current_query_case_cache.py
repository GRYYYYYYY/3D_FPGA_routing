"""Exact current-occupancy filter reuse across same-state connections.

Only immutable current occupancy is shared. Each pruned tree, anchor and own-net
capacity credit remains connection-specific. No change to query search or STA.
"""
import collections
import numpy as np


def saturated_nodes(owners, capacities):
    result = set(map(int, np.flatnonzero(np.asarray(capacities) == 0)))
    result.update(node for node, nets in owners.items() if len(nets) >= capacities[node])
    return result

def make_case_fast(connection, traces, kinds, delays, owners, capacities, saturated):
    net, pin, sink = connection['net'], connection['pin'], connection['sink']
    trace = traces[net]['trace']
    nodes = {n.inode: n for n in trace}
    parents, switches = {}, {}
    children = collections.defaultdict(set)
    for a, z in zip(trace, trace[1:]):
        if a.switch == -1:
            continue
        assert z.inode not in parents or parents[z.inode] == a.inode
        parents[z.inode] = a.inode
        switches[a.inode, z.inode] = a.switch
        children[a.inode].add(z.inode)
    removed, node = set(), sink
    assert not children[sink]
    while node in parents:
        if children[node] - removed or (node != sink and kinds[node] == 'SINK'):
            break
        removed.add(node)
        node = parents[node]
    retained, root = set(nodes) - removed, trace[0].inode
    prefixes, stack = {root: 0.}, [root]
    while stack:
        parent = stack.pop()
        for child in children[parent]:
            assert child not in prefixes
            prefixes[child] = prefixes[parent] + delays[switches[parent, child]]
            stack.append(child)
    assert prefixes.keys() == nodes.keys()
    assert any(n.inode == sink and n.pin == pin and n.kind == 'SINK' for n in trace)
    anchors = {str(n): prefixes[n] for n in sorted(retained) if kinds[n] not in ['SINK', 'IPIN']}
    blocked = saturated - {n for n in nodes if len(owners.get(n, [])) - 1 < capacities[n]}
    assert not retained & blocked
    original, node = [], sink
    while node in parents:
        original.append(node)
        node = parents[node]
    original.append(node)
    original.reverse()
    at = max(i for i, n in enumerate(original) if n in retained)
    assert str(original[at]) in anchors and not set(original[at:]) & blocked
    other = {n.inode for n in trace if n.kind == 'SINK' and n.pin is not None and n.pin != pin}
    assert other <= retained and sink not in other
    return dict(net=net, pin=pin, sink=sink, root=root, original_nodes=sorted(nodes), retained=sorted(retained),
                removed=sorted(removed), anchors=anchors, blocked=sorted(blocked), current_physical_seconds=prefixes[sink],
                original_path=original, other_sinks=sorted(other), tree_edges=[[u, v, sw, delays[sw]] for (u, v), sw in switches.items()],
                anchor_eligibility='Retained SOURCE/OPIN/channel; no IPIN/SINK anchors; same semantics as original capacity reference.',
                domain='Full-device graph; no single-cross restriction.')
