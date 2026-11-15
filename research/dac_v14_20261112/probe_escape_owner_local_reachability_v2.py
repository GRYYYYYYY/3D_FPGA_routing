"""Capacity-aware same-layer path probe after explicit terminal-path removals.

This is a read-only structural model, not native routing or a joint feasibility
certificate: owner replacement, all target sinks, native pruning closure, timing
and independent SB/CB/wire envelopes still require the actual transaction.
"""
import argparse, collections, os, resource, time
from rr_unsigned_edge_lookup_v1 import edge_row_bounds
from seed_census_analysis_pool_v2 import process_identity
from pathlib import Path
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '1'
import numpy as np
from retained_prefix_workflow import read, write, sha
from resource_opportunity_census import stream_trace, tree_data, release_scope
from run_native_scope_policy_v4 import run_dir
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS


def probe(selector_directory, cache_directory, output, per_query_seconds=120.):
    started = time.monotonic()
    output, selection = Path(output).resolve(), Path(selector_directory).resolve()
    assert not output.exists() and per_query_seconds > 0
    output.mkdir(parents=True)
    write(output/'registration.json', dict(pid=os.getpid(), start_ticks=process_identity(os.getpid())['start_ticks'],
        native_calls_new=0, selector_directory=str(selection), source_sha256={str(Path(__file__).resolve()): sha(__file__),
        str(Path(__file__).resolve().with_name('rr_unsigned_edge_lookup_v1.py')): sha(Path(__file__).resolve().with_name('rr_unsigned_edge_lookup_v1.py'))}))
    write(output/'progress.json', dict(status='verifying_selected_state_and_graph'))
    resource.setrlimit(resource.RLIMIT_AS, (64*1024**3, 64*1024**3))
    selected = read(selection/'completion.json')
    assert selected['passed'] and selected['native_calls_new'] == 0
    assert all(sha(path) == digest for path, digest in selected['source_sha256'].items())
    assert all(sha(selection/name) == digest for name, digest in selected['artifact_sha256'].items())
    state = Path(selected['state'])
    run = run_dir(state)
    manifest = read(run/'manifest.json')
    command = manifest['command']
    cache = FullRouteGraphCache(command[command.index('--read_rr_graph')+1], cache_directory)
    g = cache.g
    groups = read(selection/'groups.json')
    certificates = {c['net']: c for c in read(selection/'certificates.json')}
    wanted = {r[key] for r in groups for key in ['target_net', 'owner_net']}
    traces = {}
    occupancy = np.zeros(g.n, dtype=np.int32)
    counted_nets = 0
    write(output/'progress.json', dict(status='counting_actual_per_net_node_occupancy'))
    for row in stream_trace(run/'routed.route'):
        if not row['trace']:
            continue
        counted_nets += 1
        used = np.fromiter({node.inode for node in row['trace']}, dtype=np.int64)
        occupancy[used] += 1
        if row['net'] in wanted:
            traces[row['net']] = row
    assert wanted == traces.keys()
    assert np.all(occupancy <= g.nodes[:, 0]), 'Current route overuses real RR capacity'
    original_occupancy = occupancy.copy()
    def metadata(u):
        a = g.nodes[u]
        return dict(kind=KINDS[int(a[1])], low=tuple(map(int, a[2:5])), high=tuple(map(int, a[5:8])),
                    direction=cache.meta['directions'][int(cache.extra[u, 0])])
    trees = {net: tree_data(row['trace'], metadata) for net, row in traces.items()}
    def adjacent(u):
        lo, hi = edge_row_bounds(g.edges, g.n, g.stride, u)
        return ((int(key)//g.stride % g.n, int(key) % g.stride) for key in g.edges[lo:hi])
    def search(source, sinks):
        start = time.monotonic()
        layer = int(g.nodes[source, 4])
        remaining = set(sinks)
        seen = {source: None}
        queue = collections.deque([source])
        timed_out = False
        expanded = 0
        while queue and remaining:
            u = queue.popleft()
            expanded += 1
            if expanded % 512 == 0 and time.monotonic()-start > per_query_seconds:
                timed_out = True
                break
            for v, switch in adjacent(u):
                if v in seen or int(g.nodes[v, 4]) != layer or occupancy[v] >= g.nodes[v, 0]:
                    continue
                assert int(g.nodes[v, 7]) == layer
                seen[v] = (u, switch)
                queue.append(v)
                remaining.discard(v)
        witnesses = []
        for sink in sorted(set(sinks)-remaining):
            reverse = [sink]
            edges = []
            while reverse[-1] != source:
                child = reverse[-1]
                parent, switch = seen[child]
                edges.append([parent, child, switch])
                reverse.append(parent)
            path, edges = reverse[::-1], edges[::-1]
            assert len(set(path)) == len(path) and path[0] == source and path[-1] == sink
            assert all(int(g.nodes[node, 4]) == layer == int(g.nodes[node, 7]) for node in path)
            assert all(occupancy[node] < g.nodes[node, 0] for node in path[1:])
            keys = np.array([(u*g.n+v)*g.stride+s for u, v, s in edges], dtype=np.uint64)
            positions = np.searchsorted(g.edges, keys)
            assert np.all(positions < len(g.edges)) and np.array_equal(g.edges[positions], keys)
            witnesses.append(dict(sink=sink, nodes=path, edges=edges,
                                  capacities=[int(g.nodes[u, 0]) for u in path],
                                  residual_occupancies_before_target_addition=[int(occupancy[u]) for u in path]))
        return dict(status='paths_found' if not remaining else 'search_timed_out' if timed_out else 'exhausted_no_path',
                    all_local_sinks_reached=not remaining, search_complete=not timed_out,
                    visited_nodes=len(seen), remaining_sinks=sorted(remaining), witnesses=witnesses,
                    query_seconds=time.monotonic()-start)
    results = []
    for target, cert in sorted(certificates.items()):
        tree = trees[target]
        pins = cert['target_pins']
        assert set(pins) == set(tree['sinks'])
        source = tree['root']
        same_layer = {pin: sink for pin, sink in tree['sinks'].items()
                      if int(g.nodes[sink, 4]) == int(g.nodes[source, 4])}
        assert same_layer
        target_release = release_scope(tree, pins, metadata)
        target_removed = np.array(target_release['released_nodes'], dtype=np.int64)
        assert np.all(occupancy[target_removed] > 0)
        occupancy[target_removed] -= 1
        baseline = search(source, set(same_layer.values()))
        results.append(dict(target_net=target, owner_net=None, target_local_pins=same_layer,
                            target_removed_nodes=target_release['released_nodes'], owner_removed_nodes=[], **baseline))
        for group in [r for r in groups if r['target_net'] == target]:
            owner = group['owner_net']
            release = release_scope(trees[owner], group['owner_pins'], metadata)
            assert release == group['owner_released_before_replacement']
            removed = np.array(release['released_nodes'], dtype=np.int64)
            assert group['escape_node'] in release['released_nodes'] and np.all(occupancy[removed] > 0)
            occupancy[removed] -= 1
            result = search(source, set(same_layer.values()))
            results.append(dict(target_net=target, owner_net=owner, target_local_pins=same_layer,
                owner_pins=group['owner_pins'], escape_node=group['escape_node'], ranking_key=group['ranking_key'],
                target_removed_nodes=target_release['released_nodes'], owner_removed_nodes=release['released_nodes'], **result))
            occupancy[removed] += 1
            write(output/'progress.json', dict(completed_queries=len(results), last_owner=owner,
                                             status=result['status'], visited_nodes=result['visited_nodes']))
            print(dict(owner=owner, status=result['status'], visited_nodes=result['visited_nodes'],
                       seconds=result['query_seconds']), flush=True)
        occupancy[target_removed] += 1
    assert np.array_equal(occupancy, original_occupancy), 'Explicit occupancy model was not restored'
    write(output/'queries.json', results)
    write(output/'cache_identity.json', cache.receipt)
    source_files = [Path(__file__).resolve(), Path(__file__).resolve().with_name('rr_unsigned_edge_lookup_v1.py'), output/'registration.json', selection/'completion.json', selection/'groups.json',
                    selection/'certificates.json', state/'completion.json', run/'routed.route',
                    run/'manifest.json', cache.directory/'completion.json']
    receipt = dict(passed=True, native_calls_new=0, state=str(state), counted_nets=counted_nets,
        queries=len(results), search_timeouts=sum(r['status'] == 'search_timed_out' for r in results),
        all_occupancy_restored=True, target_only_queries=sum(r['owner_net'] is None for r in results),
        owner_queries=sum(r['owner_net'] is not None for r in results),
        owner_local_paths_found=sum(r['owner_net'] is not None and r['all_local_sinks_reached'] for r in results),
        complete_read_only_seconds=time.monotonic()-started,
        source_sha256={str(p): sha(p) for p in source_files},
        artifact_sha256={name: sha(output/name) for name in ['queries.json', 'cache_identity.json']},
        qualification='Actual directed RR edges and full per-net occupancy with real node capacities; shared SOURCE/SINK classes are not unit-capacity approximations. Target full terminal paths and only each named owner descendant scope are projected removed, all other route allocations frozen. Search is restricted to source layer and exact fixed same-layer target sinks. Witnesses certify local structural reachability only in that explicit residual model, with owner not yet replaced and other target sinks not jointly routed. Native prune/nonconfigurable closure, route order/objective/bounding box, simultaneous owner replacement, FULL/STA and original wire/SB/CB budgets remain actual transaction requirements. Timeout means unknown; exhausted no-path is limited to this explicit model. No candidate quality, actor commit, native repair, new independent benchmark or complete algorithm speedup inferred. Existing registered experiment selection/order/configuration unchanged.')
    write(output/'completion.json', receipt)
    return receipt

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--selector-directory', type=Path, required=True)
    p.add_argument('--full-graph-cache', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--per-query-seconds', type=float, default=120.)
    a = p.parse_args()
    result = probe(a.selector_directory, a.full_graph_cache, a.output, a.per_query_seconds)
    print({key: result[key] for key in ['passed', 'queries', 'search_timeouts', 'owner_local_paths_found', 'complete_read_only_seconds']}, flush=True)
