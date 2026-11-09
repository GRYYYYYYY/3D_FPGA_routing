#!/usr/bin/env python3
"""Audit published graph encodings without equating cross edges with physical vias."""
from array import array
from collections import Counter, defaultdict
import concurrent.futures
import sys
import xml.etree.ElementTree as ET

from compare_lazagna_graphs import records
from lazagna_common import ROOT, sha256, utc, write_json

BASE = ROOT / 'results/architecture_flow_20261027'


def audit(graph, arch):
    root = ET.parse(arch).getroot()
    slots = {t.get('name'): sum(int(s.get('capacity', 1)) for s in t.findall('sub_tile'))
             for t in root.findall('tiles/tile')}
    slots['EMPTY'] = 0
    types, pins, segments, switches = {}, {}, {}, {}
    grid, nodes, edge_types, crossings = Counter(), Counter(), Counter(), Counter()
    kinds, locations, names, capacities, indegree = [], [], [], array('I'), array('I')
    z_nodes, z_in, z_out, z_cross = set(), defaultdict(list), defaultdict(list), []
    direct_sources, direct_pins, crossing_delays = set(), set(), Counter()
    examples = defaultdict(list)
    block_grid = {}
    nonzero_rc = 0
    edges = 0
    for section, e in records(graph):
        a = e.attrib
        if section == 'block_types':
            key = int(a['id']); types[key] = a['name']
            pins[key] = {int(p.get('ptc')): p.text for p in e.findall('pin_class/pin')}
        elif section == 'segments':
            segments[int(a['id'])] = a['name']
        elif section == 'switches':
            timing = dict(e.find('timing').attrib)
            switches[int(a['id'])] = dict(name=a.get('name'), type=a.get('type'), timing=timing)
        elif section == 'grid' and e.tag == 'grid_loc':
            layer = int(a.get('layer', 0))
            loc = (int(a['x']), int(a['y']), layer)
            block_grid[loc] = int(a['block_type_id'])
            if int(a.get('width_offset', 0)) == 0 and int(a.get('height_offset', 0)) == 0:
                grid[(layer, types[int(a['block_type_id'])])] += 1
        elif section == 'rr_nodes':
            key = int(a['id'])
            if key != len(kinds):
                raise ValueError('Expected contiguous node IDs')
            l = e.find('loc').attrib
            loc = (int(l['xlow']), int(l['ylow']), int(l.get('layer', l.get('layer_low', 0))))
            kinds.append(a['type']); locations.append(loc)
            capacities.append(int(a.get('capacity', 1))); indegree.append(0)
            segment = e.find('segment')
            name = segments.get(int(segment.get('segment_id')), '') if segment is not None else ''
            names.append((int(l['ptc']), name))
            nodes[a['type']] += 1
            # This revision tags SB half-nodes with L4/L16, not necessarily the
            # segment named 3D_SB_connection. Direction NONE identifies the
            # synthetic half-node; the subsequent pairing checks prove usage.
            if a['type'] == 'CHANX' and a.get('direction') == 'NONE': z_nodes.add(key)
            timing = e.find('timing')
            if timing is not None and any(float(timing.get(k, 0)) != 0 for k in ('R', 'C')):
                nonzero_rc += 1
        elif section == 'rr_edges':
            u, v, s = (int(a[k]) for k in ('src_node', 'sink_node', 'switch_id'))
            indegree[v] += 1; edges += 1
            pair = kinds[u] + '->' + kinds[v]
            edge_types[pair] += 1
            if v in z_nodes and u not in z_nodes: z_in[v].append(s)
            if u in z_nodes and v not in z_nodes: z_out[u].append(s)
            if locations[u][2] != locations[v][2]:
                crossings[pair] += 1
                crossing_delays[(pair, s)] += 1
                if len(examples[pair]) < 4:
                    examples[pair].append(dict(source=u, sink=v, source_location=locations[u],
                         sink_location=locations[v], source_segment=names[u][1], sink_segment=names[v][1], switch=s))
                if u in z_nodes and v in z_nodes: z_cross.append((u, v, s))
                if kinds[u] == 'OPIN':
                    direct_sources.add(u)
                    direct_pins.add((*locations[u], names[u][0]))
    zero_clock_pins = Counter()
    for node, kind in enumerate(kinds):
        if kind != 'IPIN' or indegree[node] != 0: continue
        b = block_grid[locations[node]]
        pin = pins[b].get(names[node][0], '')
        if 'clk' in pin or 'clock' in pin:
            zero_clock_pins[types[b]] += 1
    used_pair_nodes = set()
    z_path_delays = Counter()
    for u, v, sw in z_cross:
        if u in used_pair_nodes or v in used_pair_nodes or z_out[u] or z_in[v]:
            raise ValueError('Z pairing is shared or bypassed; physical capacity needs a different model')
        if capacities[u] != 1 or capacities[v] != 1:
            raise ValueError('Unexpected Z pair capacity')
        used_pair_nodes.update((u, v))
        for sin, nin in Counter(z_in[u]).items():
            for sout, nout in Counter(z_out[v]).items():
                delay = sum(float(switches[s]['timing'].get('Tdel', 0)) for s in (sin, sw, sout))
                z_path_delays[(switches[sin]['name'], switches[sw]['name'], switches[sout]['name'], delay)] += nin*nout
    return dict(utc=utc(), graph=str(graph), graph_sha256=sha256(graph),
        architecture=str(arch), architecture_sha256=sha256(arch),
        grid=[dict(layer=l, type=t, tiles=n, slots=n*slots[t]) for (l,t), n in sorted(grid.items())],
        total_slots=dict(Counter({t: sum(n*slots[t] for (l,tt),n in grid.items() if tt==t) for t in slots})),
        node_counts=dict(nodes), edge_counts=dict(edge_types), total_nodes=len(kinds), total_edges=edges,
        cross_layer_edges=dict(crossings), switches=switches, crossing_examples=dict(examples),
        zero_indegree_clock_ipins=dict(zero_clock_pins), nonzero_node_RC_count=nonzero_rc,
        sb_pair_count=len(z_cross), sb_pair_nodes=len(used_pair_nodes), unpaired_sb_nodes=len(z_nodes-used_pair_nodes),
        schema_version=2, supersedes='v1 segment-name heuristic did not detect L4/L16-tagged SB half-nodes; v2 uses direction NONE plus explicit no-bypass pairing checks',
        cb_crossing_source_rr_nodes=len(direct_sources), cb_crossing_unique_tile_output_pins=len(direct_pins),
        cb_capacity_interpretation='Crossing edges share OPIN/receiving channel capacities; edge count is NOT an independent physical via-capacity count',
        crossing_delay_histogram=[dict(edge_type=p, switch=s, count=n) for (p,s),n in sorted(crossing_delays.items())],
        sb_full_transition_delay_histogram=[dict(switch_names=k[:3], seconds=k[3], count=n) for k,n in sorted(z_path_delays.items())])


def run(name):
    import json
    manifest = json.loads((BASE/'runs'/name/'manifest.json').read_text())
    if manifest['status'] != 'completed': raise ValueError(name)
    graph = BASE/'runs'/name/'rr_graph.xml'
    output = BASE/'graph_audits_v2'/f'{name}.json'; output.parent.mkdir(exist_ok=True)
    if output.exists(): raise FileExistsError(output)
    result = audit(graph, manifest['command'][1])
    write_json(output, result)
    print(name, result['total_slots'], result['cross_layer_edges'], 'SB pairs', result['sb_pair_count'], flush=True)


if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        list(pool.map(run, sys.argv[1:]))
