"""Construct a complete two-net proposal using a fixed selected escape owner.

Target keeps the original paths to the other sinks. Its same-layer sink uses
its recorded residual path; owner cuts reconnect in that updated occupancy.
BFS minimizes edge count in the same layer, not the native weighted objective.
Only actual native FULL/STA can turn this proposal into a legal observation.
"""
import argparse, collections, hashlib, os, resource, time
from pathlib import Path
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[key] = '1'
import numpy as np
from retained_prefix_workflow import read, write, sha
from run_native_scope_policy_v4 import run_dir
from resource_opportunity_census import stream_trace, wire_units
from coordinated_repair_tree import from_trace, nodes, prune_sinks, attach, prefixes, serialize
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import KINDS
from rr_unsigned_edge_lookup_v1 import edge_row_bounds
from state_resource_assurance import require_publication_proof, resource_assurance
from seed_census_analysis_pool_v2 import process_identity


def build(selection, reachability, cache_directory, output):
    start = time.monotonic()
    selection, reachability, output = map(lambda x: Path(x).resolve(), [selection, reachability, output])
    assert not output.exists()
    output.mkdir(parents=True)
    resource.setrlimit(resource.RLIMIT_AS, (64*1024**3, 64*1024**3))
    write(output/'registration.json', dict(pid=os.getpid(), start_ticks=process_identity(os.getpid())['start_ticks'],
          status='registered_before_construction', native_calls_new=0, source_sha256={str(Path(__file__).resolve()): sha(__file__)}))
    selected, probe = [read(p/'completion.json') for p in [selection, reachability]]
    assert selected['passed'] and probe['passed'] and selected['state'] == probe['state']
    for path, receipt in [(selection, selected), (reachability, probe)]:
        assert all(sha(p) == h for p, h in receipt['source_sha256'].items())
        assert all(sha(path/n) == h for n, h in receipt['artifact_sha256'].items())
    group = read(selection/'groups.json')[0]  # Preserve the prospectively selected group.
    target, owner = group['target_net'], group['owner_net']
    query = next(row for row in read(reachability/'queries.json') if row['target_net'] == target and row['owner_net'] == owner)
    assert query['all_local_sinks_reached'] and len(query['witnesses']) == 1
    target_pin = int(next(iter(query['target_local_pins'])))
    state = Path(selected['state'])
    source = run_dir(state)
    require_publication_proof(state)
    current_axes = resource_assurance(state)['resource_axes']
    manifest = read(source/'manifest.json')
    cmd = manifest['command']
    cache = FullRouteGraphCache(cmd[cmd.index('--read_rr_graph')+1], cache_directory)
    g = cache.g
    occupancy = np.zeros(g.n, dtype=np.int32)
    rows = {}
    for row in stream_trace(source/'routed.route'):
        if not row['trace']:
            continue
        used = np.fromiter({a.inode for a in row['trace']}, dtype=np.int64)
        occupancy[used] += 1
        if row['net'] in [target, owner]:
            rows[row['net']] = row
    assert set(rows) == {target, owner} and np.all(occupancy <= g.nodes[:, 0])
    original = {net: from_trace(row['trace'], g.switches) for net, row in rows.items()}
    def metadata(u):
        a = g.nodes[u]
        return dict(kind=KINDS[int(a[1])], low=tuple(map(int,a[2:5])), high=tuple(map(int,a[5:8])),
                    ptc=int(a[8]), direction=cache.meta['directions'][int(cache.extra[u, 0])])
    trees = {target: prune_sinks(original[target], [target_pin]), owner: prune_sinks(original[owner], group['owner_pins'])}
    witness = query['witnesses'][0]
    path = witness['nodes']
    assert path[-1] == original[target]['sinks'][target_pin] and path[0] == original[target]['root']
    kept = nodes(trees[target])
    last_kept = max(i for i, node in enumerate(path) if node in kept)
    assert all(node in kept for node in path[:last_kept+1])
    for i in range(last_kept):
        assert trees[target]['edges'][path[i+1]][:2] == tuple(witness['edges'][i][::2])
    suffix_edges = witness['edges'][last_kept:]
    trees[target] = attach(trees[target], target_pin, path[-1], path[last_kept:],
                           [edge[2] for edge in suffix_edges], [g.switches[edge[2]] for edge in suffix_edges])
    # Remove both old allocations, install the complete target and retained owner.
    for tree in original.values():
        used = np.array(sorted(nodes(tree)),dtype=np.int64)
        assert np.all(occupancy[used] > 0)
        occupancy[used] -= 1
    for tree in trees.values():
        occupancy[np.array(sorted(nodes(tree)),dtype=np.int64)] += 1
    assert np.all(occupancy <= g.nodes[:, 0])
    reconnects = []
    for pin in group['owner_pins']:
        sink = original[owner]['sinks'][pin]
        layer = int(g.nodes[sink, 4])
        retained = nodes(trees[owner])
        seeds = sorted(u for u in retained if int(g.nodes[u, 4]) == layer)
        assert seeds
        parent = {u: None for u in seeds}
        queue = collections.deque(seeds)
        began, expanded = time.monotonic(), 0
        while queue and sink not in parent:
            u = queue.popleft()
            expanded += 1
            if expanded % 512 == 0 and time.monotonic()-began > 120.:
                break
            lo, hi = edge_row_bounds(g.edges, g.n, g.stride, u)
            for key in g.edges[lo:hi]:
                v, switch = int(key)//g.stride % g.n, int(key) % g.stride
                if v in parent or int(g.nodes[v, 4]) != layer or occupancy[v] >= g.nodes[v, 0]:
                    continue
                parent[v] = (u, switch)
                queue.append(v)
        if sink not in parent:
            write(output/'completion.json',dict(passed=True,status='no_complete_structural_candidate',native_calls_new=0,
                  failed_owner_pin=pin,search_exhausted=not queue,visited_nodes=len(parent),committed_to_original_actor=False,
                  qualification='Only this explicit same-layer BFS/target witness model failed; no native infeasibility or zero-cost result claimed.'))
            return
        reverse, switches = [sink], []
        while parent[reverse[-1]] is not None:
            up, switch = parent[reverse[-1]]
            reverse.append(up); switches.append(switch)
        forward, switches = reverse[::-1], switches[::-1]
        trees[owner] = attach(trees[owner], pin, sink, forward, switches, [g.switches[s] for s in switches])
        occupancy[np.array(forward[1:],dtype=np.int64)] += 1
        reconnects.append(dict(net=owner,pin=pin,nodes=forward,switches=switches,visited_nodes=len(parent),query_seconds=time.monotonic()-began))
    assert np.all(occupancy <= g.nodes[:, 0])
    for net, tree in trees.items():
        assert tree['sinks'] == original[net]['sinks']
        prefixes(tree)
        g.require_edges([(u,v,s) for v,(u,s,_) in tree['edges'].items()])
    def axes(tree):
        cb, sb = set(), set()
        for v,(u,_,_) in tree['edges'].items():
            if int(g.nodes[u,4]) != int(g.nodes[v,4]):
                if metadata(u)['kind'] == 'OPIN': cb.add(u)
                else: sb.add(tuple(sorted([u,v])))
        return dict(wirelength=sum(wire_units(metadata(u)) for u in nodes(tree)), SB_pairs=len(sb), CB_sources=len(cb))
    before, after = [{net: axes(tree) for net,tree in value.items()} for value in [original,trees]]
    delta = {key:sum(after[net][key]-before[net][key] for net in trees) for key in current_axes}
    proposed_axes = {key:current_axes[key]+delta[key] for key in current_axes}
    delays=[]
    for net,tree in trees.items():
        old,new = prefixes(original[net]),prefixes(tree)
        for pin,sink in tree['sinks'].items():
            delays.append(dict(net=net,pin=pin,sink=sink,before_s=old[sink],after_s=new[sink],delta_s=new[sink]-old[sink]))
            if net==target and pin!=target_pin: assert old[sink]==new[sink]
    metadata_all = {u:metadata(u) for tree in trees.values() for u in nodes(tree)}
    replacements = {net:serialize(tree,metadata_all) for net,tree in trees.items()}
    # Preserve every byte outside the declared two net blocks.
    import re
    header = re.compile(r'^Net\s+(\d+)\s+\(')
    candidate = output/'candidate.route'
    with (source/'routed.route').open(newline='') as incoming, candidate.open('w',newline='') as outgoing:
        skip=False
        for line in incoming:
            match=header.match(line)
            if match:
                net=int(match[1]);skip=net in replacements
                if skip: outgoing.write(line+'\n'+replacements[net]+'\n')
            if not skip:outgoing.write(line)
    def untouched(path):
        digest=hashlib.sha256();skip=False
        with path.open(newline='') as stream:
            for line in stream:
                match=header.match(line)
                if match:skip=int(match[1]) in replacements
                if not skip:digest.update(line.encode())
        return digest.hexdigest()
    untouched_digest=untouched(source/'routed.route')
    assert untouched(candidate)==untouched_digest
    recounted=np.zeros(g.n,dtype=np.int32);seen=set()
    for row in stream_trace(candidate):
        if not row['trace']:continue
        used={a.inode for a in row['trace']};recounted[np.array(sorted(used),dtype=np.int64)] += 1
        if row['net'] in trees:
            assert from_trace(row['trace'],g.switches)==trees[row['net']];seen.add(row['net'])
    assert seen==set(trees) and np.array_equal(occupancy,recounted) and np.all(recounted<=g.nodes[:,0])
    write(output/'transaction_trees.json',trees)
    write(output/'owner_reconnections.json',reconnects)
    write(output/'physical_sink_delays.json',delays)
    write(output/'cache_identity.json',cache.receipt)
    files=[Path(__file__).resolve(),Path(__file__).resolve().with_name('rr_unsigned_edge_lookup_v1.py'),
           Path(__file__).resolve().with_name('coordinated_repair_tree.py'),selection/'completion.json',selection/'groups.json',
           reachability/'completion.json',reachability/'queries.json',state/'completion.json',state/'endpoint_vector.json',
           source/'manifest.json',source/'routed.route',cache.directory/'completion.json',output/'registration.json']
    write(output/'completion.json',dict(passed=True,status='complete_structural_candidate_pending_native_FULL_STA',
        native_calls_new=0,state=str(state),input_run=str(source),selection=str(selection),reachability=str(reachability),
        selected_target=target,selected_owner=owner,selected_owner_pins=group['owner_pins'],target_local_pin=target_pin,
        affected_nets=sorted(trees),allowed_changed_connections=[[target,target_pin]]+[[owner,pin] for pin in group['owner_pins']],
        candidate_route=str(candidate),candidate_sha256=sha(candidate),original_resources=current_axes,
        original_tree_resources=before,candidate_tree_resources=after,structural_resource_delta=delta,
        structural_full_route_resources=proposed_axes,all_fixed_sinks_restored=True,all_original_OTHER_net_bytes_exact=True,
        untouched_route_bytes_sha256=untouched_digest,all_actual_RR_node_capacities_satisfied=True,
        native_FULL_STA_completed=False,committed_to_original_actor=False,complete_construction_seconds=time.monotonic()-start,
        source_sha256={str(p):sha(p) for p in files},
        artifact_sha256={name:sha(output/name) for name in ['candidate.route','transaction_trees.json','owner_reconnections.json','physical_sink_delays.json','cache_identity.json']},
        qualification='First prospectively ranked owner only, no selection over final candidate quality. Recorded same-layer target witness plus original other target sink paths; owner sink scopes reconnect by deterministic same-layer minimum-hop BFS in updated occupancy. All sink mappings, actual RR edges/switches, capacities and unchanged other-net bytes checked. Resource counts and zero-RC switch-sum delays are structural proposal properties, not a native legal/timing observation. Native pruning/configurability, FULL/freshSTA, independent physical audit and exact original CPD/wire/SB/CB envelopes remain gates. Both original actor and frozen native/domain comparison remain unchanged. This changes tree construction relative to native weighted search and is an explicit separate development intervention, not a one-factor domain attribution or cold complete-cost claim.'))
    print(dict(passed=True,status='candidate_pending_native',resources=proposed_axes,delta=delta,construction_seconds=time.monotonic()-start),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--selector-directory',type=Path,required=True);p.add_argument('--reachability',type=Path,required=True);p.add_argument('--full-graph-cache',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    build(a.selector_directory,a.reachability,a.full_graph_cache,a.output)
