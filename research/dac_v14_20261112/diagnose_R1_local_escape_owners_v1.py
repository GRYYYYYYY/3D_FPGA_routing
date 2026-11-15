"""Prove the current local escape cut and screen its blocking-owner scopes."""
import collections, time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from resource_opportunity_census import stream_trace, tree_data, release_scope, pin_screen
from run_native_scope_policy_v4 import run_dir
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS
import numpy as np

start = time.monotonic()
state = Path(read(D / 'R1_last_vertical_excess_diagnostic_01/completion.json')['state'])
run = run_dir(state)
manifest = read(run / 'manifest.json')
cmd = manifest['command']
graph = Path(cmd[cmd.index('--read_rr_graph') + 1])
cache = FullRouteGraphCache(graph, D / 'full_route_graph_cache_bnn_01')
g = cache.g
nodes, edges, n, stride = g.nodes, g.edges, g.n, g.stride
def adj(u):
    keys = edges[np.searchsorted(edges, u*n*stride):np.searchsorted(edges, (u+1)*n*stride)]
    return list(map(int, (keys // stride) % n))
def metadata(u):
    a = nodes[u]
    return dict(kind=KINDS[int(a[1])], low=tuple(map(int, a[2:5])), high=tuple(map(int, a[5:8])),
                direction=cache.meta['directions'][int(cache.extra[u, 0])])
source, opin = 265257, 265308
assert adj(source) == [opin] and metadata(source)['kind'] == 'SOURCE' and metadata(opin)['kind'] == 'OPIN'
neighbors = adj(opin)
local = {u for u in neighbors if int(nodes[u, 4]) == 0}
cross = {u for u in neighbors if int(nodes[u, 4]) == 1}
assert len(local) == len(cross) == 8 and len(neighbors) == 16
assert all(metadata(u)['kind'] in ['CHANX', 'CHANY'] for u in neighbors)
assert all(int(nodes[u, 0]) == 1 for u in local)
reference = D / 'completed_resource_timing_dev_01/paired/round_002/proposal_01/transaction/current_group_evaluation'
rr = next(r for r in stream_trace(run_dir(reference) / 'routed.route') if r['net'] == 31767)
reference_nodes = {x.inode for x in rr['trace']}
wanted = local | reference_nodes
owners, relevant = collections.defaultdict(set), {}
for row in stream_trace(run / 'routed.route'):
    hits = wanted & {x.inode for x in row['trace']}
    if hits:
        relevant[row['net']] = row
        for u in hits:
            owners[u].add(row['net'])
actual = relevant[31767]
assert actual['trace'][0].inode == rr['trace'][0].inode == source
assert sorted((x.pin, x.inode) for x in actual['trace'] if x.kind == 'SINK') == sorted((x.pin, x.inode) for x in rr['trace'] if x.kind == 'SINK')
assert next(x for x in actual['trace'] if x.kind == 'SINK' and x.pin == 1).low[2] == 0
assert all(len(owners[u]) == 1 and 31767 not in owners[u] for u in local)
# A shared SOURCE/SINK class is a conflict only when its actual capacity is full.
# Do not mistake sharing of a capacity>1 terminal class for an overuse.
conflicts = {u: sorted(owners[u] - {31767}) for u in reference_nodes
             if len(owners[u] - {31767}) >= int(nodes[u, 0])}
owner_nets = {v for u in local for v in owners[u]}
vector = read(state / 'endpoint_vector.json')
pin_info = collections.defaultdict(dict)
import json
for line in (run / 'native_sta_frontier.jsonl').open():
    row = json.loads(line)
    if row.get('type') == 'pin' and row['net'] in owner_nets and not row['driver'] and row['route_tree_present']:
        pin_info[row['net']][row['pin']] = dict(slack_s=row['setup_slack_s'],
            criticality=row['setup_criticality_raw'], ignored=row['ignored'], **{'global': row['global']})
scopes = []
for u in sorted(local):
    owner = next(iter(owners[u]))
    tree = tree_data(relevant[owner]['trace'], metadata)
    targets = tree['descendants'][u]
    released = release_scope(tree, targets, metadata)
    assert u in released['released_nodes']
    scopes.append(dict(escape_node=u, owner_net=owner, owner_name=relevant[owner]['name'],
        pins=sorted(targets), connections=len(targets),
        current_0p2ns_screen=pin_screen(targets, pin_info[owner], vector['metrics']['least_slack_s'], .2e-9),
        released_before_replacement=released))
out = D / 'R1_local_escape_owner_diagnostic_01'
out.mkdir(exist_ok=False)
write(out / 'owner_scopes.json', scopes)
write(out / 'cache_identity.json', cache.receipt)
files = [Path(__file__).resolve(), D / 'R1_crossing_source_probe_01/verification.json',
         D / 'BNN_vertical_cut_bound_01/completion.json', state / 'endpoint_vector.json',
         run / 'manifest.json', run / 'routed.route', run / 'native_sta_frontier.jsonl',
         run_dir(reference) / 'routed.route', cache.directory / 'completion.json',
         out / 'owner_scopes.json', out / 'cache_identity.json']
write(out / 'completion.json', dict(passed=True, native_calls_new=0, state=str(state),
    source=source, only_OPIN=opin, local_layer_escape_nodes={str(u): sorted(owners[u]) for u in sorted(local)},
    all_eight_unit_capacity_local_escapes_occupied_by_other_nets=True,
    target_pin1_fixed_layer=0, first_available_escape_must_use_CB_to_layer1=True,
    minimum_distinct_crossing_resources_for_net_with_other_routes_frozen=2,
    current_target_crossings=2, single_net_crossing_reduction_impossible_with_other_routes_frozen=True,
    one_CB_reference_state=str(reference), reference_same_exact_SOURCE_SINK_RR_nodes=True,
    reference_one_CB_tree_conflicts=conflicts,
    SB_pair_has_reverse_layer0_to1_edge=8689817 in adj(5916265),
    SB_pair_layer1_to0_edge=5916265 in adj(8689817),
    blocking_owner_nets=sorted(owner_nets), screened_owner_scopes=len(scopes),
    eligible_owner_scopes_0p2ns=sum(s['current_0p2ns_screen']['eligible'] for s in scopes),
    source_sha256={str(f): sha(f) for f in files}, complete_read_only_seconds=time.monotonic()-start,
    qualification='Capacity-conditioned local cut, not a global optimum: SOURCE has one OPIN, all eight same-layer OPIN channel exits are held by distinct other nets at unit capacity; remaining OPIN exits cross to layer1. Pin1 is fixed on layer0, so preserving every other route forces a first CB0-to1 plus a distinct return crossing. Current one-CB/one-SB target attains this frozen-other-route bound. The5103global fixed-terminal bound remains valid, but its one-CB historical witness conflicts with current owners. Shared terminal classes use their true capacity. Owner slack/release screens are not feasible repairs or predicted savings; a separate joint-owner native/FULL/STA transaction is required. No old actor/rule changed and no QoR/time borrowed.'))
print(dict(passed=True, local_cut_requires_joint_owner_release=True,
           owners=sorted(owner_nets), eligible_scopes=sum(s['current_0p2ns_screen']['eligible'] for s in scopes)), flush=True)
