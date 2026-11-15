"""Find capacity-conditioned source escape cuts and current-STA owner groups."""
import argparse, collections, os, resource, time
from pathlib import Path
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '1'
import numpy as np
from retained_prefix_workflow import read, write, sha
from run_native_scope_policy_v4 import run_dir
from resource_opportunity_census import stream_trace, tree_data, release_scope, pin_screen
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS
from state_resource_assurance import resource_assurance
from current_resource_bundle_v2 import serialize_request

def select(state, cache_directory, output, minimum_margin_ns=.2):
    start = time.monotonic()
    state, output = Path(state).resolve(), Path(output).resolve()
    assert minimum_margin_ns >= 0 and not output.exists()
    resource.setrlimit(resource.RLIMIT_AS, (64*1024**3, 64*1024**3))
    assurance = resource_assurance(state)
    run = run_dir(state)
    manifest, vector = read(run / 'manifest.json'), read(state / 'endpoint_vector.json')
    assert manifest['metrics']['native_full_check_passed']
    graph = Path(manifest['command'][manifest['command'].index('--read_rr_graph')+1])
    cache = FullRouteGraphCache(graph, cache_directory)
    g = cache.g
    def metadata(u):
        a = g.nodes[u]
        return dict(kind=KINDS[int(a[1])], low=tuple(map(int, a[2:5])), high=tuple(map(int, a[5:8])),
                    direction=cache.meta['directions'][int(cache.extra[u, 0])])
    def adj(u):
        lo, hi = np.searchsorted(g.edges, [u*g.n*g.stride, (u+1)*g.n*g.stride])
        return list(map(int, (g.edges[lo:hi] // g.stride) % g.n))
    # Unit-capacity nodes have one net owner; shared terminal classes are excluded.
    owners = np.full(g.n, -1, dtype=np.int64)
    potentials, classifications = [], []
    total_nets = 0
    for row in stream_trace(run / 'routed.route'):
        trace = row['trace']
        if not trace:
            continue
        total_nets += 1
        used = np.fromiter({x.inode for x in trace}, dtype=np.int64)
        assert np.all((used >= 0) & (used < g.n))
        unit = used[g.nodes[used, 0] == 1]
        assert np.all((owners[unit] == -1) | (owners[unit] == row['net'])), 'Current unit-capacity overuse'
        owners[unit] = row['net']
        layers = {trace[0].low[2]} | {x.low[2] for x in trace if x.kind == 'SINK'}
        cb, sb = set(), set()
        for a, b in zip(trace, trace[1:]):
            if a.switch != -1 and a.low[2] != b.low[2]:
                if a.kind == 'OPIN':
                    cb.add(a.inode)
                else:
                    sb.add(tuple(sorted([a.inode, b.inode])))
        count = len(cb) + len(sb)
        reference = int(len(layers) > 1)
        assert count >= reference
        if count > reference and any(x.kind == 'SINK' and x.low[2] == trace[0].low[2] for x in trace):
            potentials.append(dict(row=row, crossings=count, terminal_reference=reference,
                                   excess=count-reference))
    certificates = []
    owner_nets = set()
    for candidate in potentials:
        row = candidate['row']
        source = row['trace'][0].inode
        children = adj(source)
        label = dict(net=row['net'], current_crossings=candidate['crossings'],
                     terminal_cut_reference=candidate['terminal_reference'])
        if metadata(source)['kind'] != 'SOURCE' or len(children) != 1 or metadata(children[0])['kind'] != 'OPIN':
            classifications.append(dict(label, status='unsupported_source_fanout'))
            continue
        opin = children[0]
        z = metadata(source)['low'][2]
        neighbors = adj(opin)
        local = [u for u in neighbors if metadata(u)['low'][2] == z]
        cross = [u for u in neighbors if metadata(u)['low'][2] != z]
        if not local or not cross or any(metadata(u)['kind'] not in ['CHANX', 'CHANY'] for u in neighbors) or any(int(g.nodes[u, 0]) != 1 for u in local):
            classifications.append(dict(label, status='unsupported_OPIN_exit_cut'))
            continue
        if any(owners[u] in [-1, row['net']] for u in local):
            classifications.append(dict(label, status='local_exit_not_entirely_blocked_by_others'))
            continue
        assert candidate['crossings'] >= 2
        cert = dict(label, status='frozen_other_routes_force_two_distinct_crossing_resources',
                    source=source, only_OPIN=opin, source_layer=z,
                    local_exits=[dict(node=u, owner_net=int(owners[u]), capacity=1) for u in sorted(local)],
                    cross_exits=sorted(cross), minimum_current_frozen_other_route_crossings=2,
                    bound_attained=candidate['crossings'] == 2,
                    target_pins=sorted({x.pin for x in row['trace'] if x.kind == 'SINK'}),
                    target_current_crossing_sources=sorted(cb['up'] for cb in tree_data(row['trace'], metadata)['crossing'].values()))
        candidate['certificate'] = cert
        certificates.append(cert)
        owner_nets.update(int(owners[u]) for u in local)
        classifications.append(dict(label, status=cert['status']))
    wanted = owner_nets | {c['net'] for c in certificates}
    traces = {c['row']['net']: c['row'] for c in potentials if c['row']['net'] in wanted}
    if owner_nets:
        for row in stream_trace(run / 'routed.route'):
            if row['net'] in owner_nets:
                traces[row['net']] = row
    assert wanted <= traces.keys()
    pin_info = collections.defaultdict(dict)
    import json
    for line in (run / 'native_sta_frontier.jsonl').open():
        row = json.loads(line)
        if row.get('type') == 'pin' and row['net'] in wanted and not row['driver'] and row['route_tree_present']:
            pin_info[row['net']][row['pin']] = dict(slack_s=row['setup_slack_s'],
                criticality=row['setup_criticality_raw'], ignored=row['ignored'], **{'global': row['global']})
    trees = {net: tree_data(row['trace'], metadata) for net, row in traces.items()}
    groups, screens = [], []
    margin = minimum_margin_ns * 1e-9
    for cert in certificates:
        net, target_pins = cert['net'], cert['target_pins']
        target_screen = pin_screen(target_pins, pin_info[net], vector['metrics']['least_slack_s'], margin)
        for exit in cert['local_exits']:
            owner, node = exit['owner_net'], exit['node']
            pins = sorted(trees[owner]['descendants'][node])
            released = release_scope(trees[owner], pins, metadata)
            assert node in released['released_nodes']
            screen = pin_screen(pins, pin_info[owner], vector['metrics']['least_slack_s'], margin)
            item = dict(target_net=net, owner_net=owner, escape_node=node, target_screen=target_screen,
                        owner_screen=screen, owner_pins=pins, owner_released_before_replacement=released,
                        eligible=target_screen['eligible'] and screen['eligible'])
            screens.append(item)
            if not item['eligible']:
                continue
            cuts = []
            for which, ps in [(net, target_pins), (owner, pins)]:
                cuts.append(dict(net=which, pins=ps, ordered_queries=[dict(net=which, pin=p,
                    raw_criticality=pin_info[which][p]['criticality']) for p in ps]))
            request, _, queries = serialize_request(cuts)
            rank = [-int(cert['current_crossings'] - cert['terminal_cut_reference']),
                    len(target_pins)+len(pins), -screen['minimum_margin_s'],
                    -target_screen['minimum_margin_s'], net, owner, node]
            groups.append(dict(item, target_pins=target_pins, actual_nets=2,
                               connections=len(queries), queries=queries, request=request,
                               ranking_key=rank, certificate_net=net))
    groups.sort(key=lambda r: r['ranking_key'])
    output.mkdir(parents=True)
    write(output / 'certificates.json', certificates)
    write(output / 'screens.json', screens)
    write(output / 'groups.json', groups)
    write(output / 'classifications.json', classifications)
    write(output / 'cache_identity.json', cache.receipt)
    if groups:
        (output / 'selected_request.txt').write_text(groups[0]['request'])
    files = [Path(__file__).resolve(), state/'completion.json', state/'endpoint_vector.json',
             run/'manifest.json', run/'routed.route', run/'native_sta_frontier.jsonl',
             Path(assurance['evidence']), cache.directory/'completion.json']
    artifacts = ['certificates.json', 'screens.json', 'groups.json', 'classifications.json', 'cache_identity.json']
    if groups:
        artifacts.append('selected_request.txt')
    receipt = dict(passed=True, state=str(state), native_calls_new=0,
        routed_nets=total_nets, positive_excess_same_layer_target_nets=len(potentials),
        certified_escape_cuts=len(certificates), eligible_joint_groups=len(groups),
        selected_group=None if not groups else {k: groups[0][k] for k in ['target_net', 'owner_net', 'target_pins', 'owner_pins', 'connections', 'ranking_key']},
        ranking='decreasing crossing excess, increasing total connections, decreasing owner margin, decreasing target margin, target net, owner net, escape node',
        minimum_current_margin_ns=minimum_margin_ns, resource_assurance=assurance,
        complete_read_only_seconds=time.monotonic()-start,
        source_sha256={str(f): sha(f) for f in files}, artifact_sha256={n: sha(output/n) for n in artifacts},
        qualification='Circuit-independent diagnostic selector over actual current route/graph/STA. Supported cut requires a SOURCE with one OPIN and unit-capacity same-layer channel exits all held by other nets; remaining exits cross away. A source-layer target then needs a distinct return crossing while others are frozen. Shared terminal classes are never treated as unit-capacity conflicts. Unsupported topology and unblocked/screen-rejected cases remain explicit. This does not certify global optimality, replacement feasibility or native QoR; all accepted transactions still require real complete native/capacity/FULL/STA checks. Ownership census/cache verification and screening are one-time research costs here, not measured complete algorithm times. No net/RR IDs or benchmark-specific thresholds hardcoded; no existing actor/rule changed.')
    write(output / 'completion.json', receipt)
    return receipt

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--full-graph-cache', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--minimum-margin-ns', type=float, default=.2)
    a = p.parse_args()
    r = select(a.state, a.full_graph_cache, a.output, a.minimum_margin_ns)
    print({k: r[k] for k in ['passed', 'routed_nets', 'certified_escape_cuts', 'eligible_joint_groups', 'selected_group', 'complete_read_only_seconds']}, flush=True)
