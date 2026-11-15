"""Current-STA selectors over explicit observations. No historical state aliases.

These functions only propose scopes. No native feasibility, acceptance or timing
benefit is inferred. Admission and physical/native verification belong to caller.
"""
import collections, json
from fractions import Fraction
from pathlib import Path
import numpy as np
from immutable_rr_audit_cache import KINDS
from resource_opportunity_census import stream_trace, tree_data, release_scope, pin_screen, wire_units
from current_resource_bundle_v2 import serialize_request


def crossing_scopes(run, vector, cache, minimum_margin_s=.2e-9):
    rd=Path(run);v=vector;g=cache.g;pins=collections.defaultdict(dict)
    for line in (rd / 'native_sta_frontier.jsonl').open():
        r = json.loads(line)
        if r.get('type') == 'pin' and (not r['driver']) and r['route_tree_present']:
            pins[r['net']][r['pin']] = dict(slack_s=r['setup_slack_s'], criticality=r['setup_criticality_raw'], ignored=r['ignored'], **{'global': r['global']})
    candidates = []
    sb = collections.Counter()
    cb = collections.Counter()
    wire = 0
    multiple = 0
    for rec in stream_trace(rd / 'routed.route'):
        if not rec['trace']:
            continue
        local = {}
    
        def metadata(n):
            if n not in local:
                r = g.nodes[n]
                (direction, _) = map(int, cache.extra[n])
                local[n] = dict(kind=KINDS[int(r[1])], low=tuple(map(int, r[2:5])), high=tuple(map(int, r[5:8])), direction=cache.meta['directions'][direction])
            return local[n]
        tree = tree_data(rec['trace'], metadata)
        sb.update(tree['SB'])
        cb.update(tree['CB'])
        wire += sum((wire_units(metadata(n)) for n in tree['used']))
        if len(tree['SB']) + len(tree['CB']) <= tree['layer_cut_reference']:
            continue
        multiple += 1
        groups = collections.defaultdict(set)
        for (node, e) in tree['crossing'].items():
            groups[e['resource_kind'], e['resource']].update(tree['descendants'][node])
        seen = set()
        for (_, targets) in sorted(groups.items()):
            identity = tuple(sorted(targets))
            if identity in seen:
                continue
            seen.add(identity)
            screen = pin_screen(targets, pins[rec['net']], v['metrics']['least_slack_s'], minimum_margin_s)
            if not screen['eligible']:
                continue
            released = release_scope(tree, targets, metadata)
            freed = len(released['released_SB']) + len(released['released_CB'])
            kept = sorted(tree['SB'] - set(released['released_SB']) | tree['CB'] - set(released['released_CB']))
            if not freed or not kept:
                continue
            by_pin = {r['pin']: r for r in screen['pins']}
            candidates.append(dict(net=rec['net'], name=rec['name'], removed_crossing_resources=freed, minimum_margin_s=screen['minimum_margin_s'], resource_per_sink=str(Fraction(freed, len(targets))), retained_crossing_sources=kept, **released, ordered_queries=[dict(net=rec['net'], pin=p, raw_criticality=by_pin[p]['raw_criticality']) for p in sorted(targets)]))
    candidates.sort(key=lambda r: (-Fraction(r['removed_crossing_resources'], len(r['pins'])), len(r['pins']), -r['minimum_margin_s'], r['net'], r['pins']))
    actual = dict(planar_wirelength_excluding_sb_half_nodes=wire, sb_pairs_used=len(sb), sb_pair_net_occupancy=sum(sb.values()), cb_crossing_output_sources_used=len(cb), cb_crossing_output_source_net_occupancy=sum(cb.values()))
    return dict(candidates=candidates, actual_resources=actual, multi_crossing_nets=multiple)


def owner_scopes(run, vector, cache, minimum_margin_ns=.2):
    run=Path(run)
    g = cache.g
    def metadata(u):
        a = g.nodes[u]
        return dict(kind=KINDS[int(a[1])], low=tuple(map(int, a[2:5])), high=tuple(map(int, a[5:8])), direction=cache.meta['directions'][int(cache.extra[u, 0])])
    def adj(u):
        (lo, hi) = np.searchsorted(g.edges, [u * g.n * g.stride, (u + 1) * g.n * g.stride])
        return list(map(int, g.edges[lo:hi] // g.stride % g.n))
    owners = np.full(g.n, -1, dtype=np.int64)
    (potentials, classifications) = ([], [])
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
        (cb, sb) = (set(), set())
        for (a, b) in zip(trace, trace[1:]):
            if a.switch != -1 and a.low[2] != b.low[2]:
                if a.kind == 'OPIN':
                    cb.add(a.inode)
                else:
                    sb.add(tuple(sorted([a.inode, b.inode])))
        count = len(cb) + len(sb)
        reference = int(len(layers) > 1)
        assert count >= reference
        if count > reference and any((x.kind == 'SINK' and x.low[2] == trace[0].low[2] for x in trace)):
            potentials.append(dict(row=row, crossings=count, terminal_reference=reference, excess=count - reference))
    certificates = []
    owner_nets = set()
    for candidate in potentials:
        row = candidate['row']
        source = row['trace'][0].inode
        children = adj(source)
        label = dict(net=row['net'], current_crossings=candidate['crossings'], terminal_cut_reference=candidate['terminal_reference'])
        if metadata(source)['kind'] != 'SOURCE' or len(children) != 1 or metadata(children[0])['kind'] != 'OPIN':
            classifications.append(dict(label, status='unsupported_source_fanout'))
            continue
        opin = children[0]
        z = metadata(source)['low'][2]
        neighbors = adj(opin)
        local = [u for u in neighbors if metadata(u)['low'][2] == z]
        cross = [u for u in neighbors if metadata(u)['low'][2] != z]
        if not local or not cross or any((metadata(u)['kind'] not in ['CHANX', 'CHANY'] for u in neighbors)) or any((int(g.nodes[u, 0]) != 1 for u in local)):
            classifications.append(dict(label, status='unsupported_OPIN_exit_cut'))
            continue
        if any((owners[u] in [-1, row['net']] for u in local)):
            classifications.append(dict(label, status='local_exit_not_entirely_blocked_by_others'))
            continue
        assert candidate['crossings'] >= 2
        cert = dict(label, status='frozen_other_routes_force_two_distinct_crossing_resources', source=source, only_OPIN=opin, source_layer=z, local_exits=[dict(node=u, owner_net=int(owners[u]), capacity=1) for u in sorted(local)], cross_exits=sorted(cross), minimum_current_frozen_other_route_crossings=2, bound_attained=candidate['crossings'] == 2, target_pins=sorted({x.pin for x in row['trace'] if x.kind == 'SINK'}), target_current_crossing_sources=sorted((cb['up'] for cb in tree_data(row['trace'], metadata)['crossing'].values())))
        candidate['certificate'] = cert
        certificates.append(cert)
        owner_nets.update((int(owners[u]) for u in local))
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
        if row.get('type') == 'pin' and row['net'] in wanted and (not row['driver']) and row['route_tree_present']:
            pin_info[row['net']][row['pin']] = dict(slack_s=row['setup_slack_s'], criticality=row['setup_criticality_raw'], ignored=row['ignored'], **{'global': row['global']})
    trees = {net: tree_data(row['trace'], metadata) for (net, row) in traces.items()}
    (groups, screens) = ([], [])
    margin = minimum_margin_ns * 1e-09
    for cert in certificates:
        (net, target_pins) = (cert['net'], cert['target_pins'])
        target_screen = pin_screen(target_pins, pin_info[net], vector['metrics']['least_slack_s'], margin)
        for exit in cert['local_exits']:
            (owner, node) = (exit['owner_net'], exit['node'])
            pins = sorted(trees[owner]['descendants'][node])
            released = release_scope(trees[owner], pins, metadata)
            assert node in released['released_nodes']
            screen = pin_screen(pins, pin_info[owner], vector['metrics']['least_slack_s'], margin)
            item = dict(target_net=net, owner_net=owner, escape_node=node, target_screen=target_screen, owner_screen=screen, owner_pins=pins, owner_released_before_replacement=released, eligible=target_screen['eligible'] and screen['eligible'])
            screens.append(item)
            if not item['eligible']:
                continue
            cuts = []
            for (which, ps) in [(net, target_pins), (owner, pins)]:
                cuts.append(dict(net=which, pins=ps, ordered_queries=[dict(net=which, pin=p, raw_criticality=pin_info[which][p]['criticality']) for p in ps]))
            (request, _, queries) = serialize_request(cuts)
            rank = [-int(cert['current_crossings'] - cert['terminal_cut_reference']), len(target_pins) + len(pins), -screen['minimum_margin_s'], -target_screen['minimum_margin_s'], net, owner, node]
            groups.append(dict(item, target_pins=target_pins, actual_nets=2, connections=len(queries), queries=queries, request=request, ranking_key=rank, certificate_net=net))
    groups.sort(key=lambda r: r['ranking_key'])
    return dict(certificates=certificates, screens=screens, groups=groups, classifications=classifications, routed_nets=total_nets, positive_excess_same_layer_target_nets=len(potentials))
