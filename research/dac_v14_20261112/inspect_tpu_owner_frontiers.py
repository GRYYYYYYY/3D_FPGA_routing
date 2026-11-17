"""Explain the recorded searches from the original prune and occupancy, without rerouting."""
from collections import defaultdict
from pathlib import Path
import hashlib
import json

from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS
from rr_unsigned_edge_lookup_v1 import edge_row_bounds
from resource_opportunity_census import stream_trace
from coordinated_repair_tree import nodes, from_trace, prune_sinks
from retained_prefix_workflow import D, sha, read

base = D / 'structural_p1_sta_01'
state = base / 'tpu_like.small.os/runs/state'
route = state / 'routed.route'
sel = base / 'tpu_like.small.os-owner/groups.json'
wits = base / 'tpu_like.small.os-reachability/queries.json'
cache = D / 'complete_serial_additional_circuits_01/robot_rl_native/flow/full_graph_cache'
files = [route, sel, wits, cache/'completion.json']
binding = read(base/'TPU_OWNER_ORIGINAL_BRANCH_CONFLICTS.json')['source_sha256']
assert all(sha(p) == binding[str(p)] for p in files)
cmd = read(state/'manifest.json')['command']
g = FullRouteGraphCache(cmd[cmd.index('--read_rr_graph')+1], cache).g
groups = read(sel)
queries = {q['owner_net']: q for q in read(wits)}
wanted = {r[k] for r in groups for k in ('target_net','owner_net')}
holders = defaultdict(set)
trees = {}
for row in stream_trace(route):
    net = row['net']
    if row['trace'] and net in wanted:
        trees[net] = from_trace(row['trace'], g.switches)
    for n in {t.inode for t in row['trace']}:
        holders[n].add(net)

def successors(node):
    lo, hi = edge_row_bounds(g.edges, g.n, g.stride, node)
    return sorted(set(map(int, g.edges[lo:hi] // g.stride % g.n)))

def describe(node):
    return dict(id=node, kind=KINDS[int(g.nodes[node,1])], layer=int(g.nodes[node,4]))

rows = []
for rank, group in enumerate(groups):
    owner, target = group['owner_net'], group['target_net']
    q = queries[owner]
    pin = int(next(iter(q['target_local_pins'])))
    op = group['owner_pins']
    kept = nodes(prune_sinks(trees[owner], op))
    tk = nodes(prune_sinks(trees[target], [pin]))
    witness = q['witnesses'][0]
    added = set(witness['nodes']) - tk
    def occupants(n, reserved):
        users = holders[n].copy()
        if n not in kept:
            users.discard(owner)
        if n not in tk:
            users.discard(target)
        if reserved and n in added:
            users.add(target)
        return users
    branch = []
    n = trees[owner]['sinks'][op[0]]
    while n not in kept:
        branch.append(n)
        n = trees[owner]['edges'][n][0]
    branch = [n] + branch[::-1]
    # Original tree supplies a constructive pre-reservation reachability witness.
    assert all(len(occupants(n, False)) < g.nodes[n,0] for n in branch[1:])
    blocked = [n for n in branch[1:] if len(occupants(n, True)) >= g.nodes[n,0]]
    assert blocked == [group['escape_node']]
    directory = (base/'owner_rank_sweep_01'/f'tpu_like.small.os-{rank}' if rank else
                 base/'tpu_like.small.os-cross-layer-candidate')
    reg = read(directory/'registration.json')['source_sha256']
    assert len(reg) == 1 and all(sha(p)==h for p,h in reg.items())
    result = read(directory/'completion.json')
    assert result['search_exhausted']
    root, = kept
    hop, = [n for n in successors(root) if n not in kept and len(occupants(n, True)) < g.nodes[n,0]]
    first = [root, hop]
    exits = {u:[dict(node=v, occupants=sorted(occupants(v,True)), cap=int(g.nodes[v,0]))
                for v in successors(u) if v not in first] for u in first}
    if rank:
        assert result['visited_nodes']==2 and all(len(e['occupants'])>=e['cap'] for es in exits.values() for e in es)
    rows.append(dict(rank=rank, owner=owner, target=target, target_pin=pin, owner_pins=op,
                     constructor=reg, receipt_sha256=sha(directory/'completion.json'),
                     registration_sha256=sha(directory/'registration.json'),
                     target_witness=witness['nodes'], retained_target=sorted(tk),
                     seed=describe(root), first_hop=describe(hop), boundary=exits,
                     original_path_before_reservation=branch, blocked_after=blocked,
                     visits=result['visited_nodes'], exhausted=True))
result = dict(inputs=binding, script_sha256=sha(__file__),rows=rows,
              qualification='Each original owner path certifies pre-reservation reachability. Post-reservation visits are historical. Boundary lists every edge endpoint outside the first two nodes, not the entire rank-0 frontier.')
out = base/'TPU_OWNER_FRONTIERS.json'
with out.open('x') as stream:
    json.dump(result,stream,indent=2)
    stream.write('\n')
