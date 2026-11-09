#!/usr/bin/env python3
"""Independently validate the small common-plane architecture construction."""
from array import array
from collections import Counter
from itertools import zip_longest
import json

from audit_flatland_controlled_planes import load
from compare_lazagna_graphs import records
from lazagna_common import ROOT, sha256, utc, write_json

BASE = ROOT/'results/architecture_flow_20261027'


def canonical(e):
    return e.tag, tuple(sorted(e.attrib.items())), (e.text or '').strip(), tuple(canonical(c) for c in e)


def nonplanar_records(path):
    layers = array('h'); half = bytearray()
    for section, e in records(path):
        if section == 'rr_nodes':
            layers.append(int(e.find('loc').get('layer')))
            half.append(e.get('type') == 'CHANX' and e.get('direction') == 'NONE')
        elif section == 'rr_edges':
            u, v = int(e.get('src_node')), int(e.get('sink_node'))
            if layers[u] == layers[v] and not half[u] and not half[v]: continue
        yield section, canonical(e)


def resources(path):
    segments = {}; counts = Counter(); length = Counter(); node_capacity = Counter()
    for section, e in records(path):
        if section == 'segments': segments[int(e.get('id'))] = e.get('name')
        elif section == 'rr_nodes':
            if e.get('type') not in ('CHANX', 'CHANY') or e.get('direction') == 'NONE': continue
            loc = e.find('loc'); seg = segments[int(e.find('segment').get('segment_id'))]
            capacity = int(e.get('capacity'))
            units = int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
            counts[seg] += 1; length[seg] += capacity*units; node_capacity[seg] += capacity
        elif section == 'rr_edges': break
    return dict(planar_nodes_by_segment=dict(counts), planar_node_capacity_by_segment=dict(node_capacity),
                planar_wire_unit_capacity_by_segment=dict(length), total_planar_wire_unit_capacity=sum(length.values()))


def main():
    directory = BASE/'common_plane_models/v2/n25_w100'
    output = directory/'independent_validation.json'
    if output.exists(): raise FileExistsError(output)
    manifest = json.loads((directory/'manifest.json').read_text())
    sb = manifest['models']['sb']['graph']; reference = load(sb)
    results = {}
    for family in ['cb_o', 'hybrid_o']:
        path = manifest['models'][family]['graph']; derived = load(path, reference['identities'])
        assert derived['keys'] == reference['keys'] and derived['edges'] == reference['edges']
        original = BASE/'runs'/f'controlled_graph_{family}_n25_w100_ideal/rr_graph.xml'
        count = 0
        for a, b in zip_longest(nonplanar_records(original), nonplanar_records(path)):
            assert a == b, (family, count)
            count += 1
        results[family] = dict(same_ordinary_nodes=True, same_planar_edges=True,
            planar_edges=len(derived['edges']), all_other_records_exactly_preserved=count,
            crossings=derived['cross'], graph_sha256=sha256(path))
        print(family, 'exact common plane and preserved nonplanar records', flush=True)
    two = BASE/'runs/controlled_graph_matched_2d_n25_w100_ideal/rr_graph.xml'
    capacity = {}
    for family in ['sb', 'cb_o', 'hybrid_o', 'matched_2d']:
        data = json.loads((BASE/'graph_audits_v2'/f'controlled_graph_{family}_n25_w100_ideal.json').read_text())
        slots = data['total_slots']
        capacity[family] = dict(clb=slots['clb'], spram=slots['spram'], complex_dsp=slots['complex_dsp'],
                                io=slots['io']+slots.get('io_double', 0))
    assert all(v == capacity['sb'] for v in capacity.values())
    wires = dict(sb=resources(sb), matched_2d=resources(two))
    write_json(output, dict(utc=utc(), passed=True, model_comparisons=results, logical_capacities=capacity,
        wire_resources=wires,
        planar_wire_capacity_2d_vs_3d_ratio=wires['matched_2d']['total_planar_wire_unit_capacity']/wires['sb']['total_planar_wire_unit_capacity'],
        limitation='Same logical capacities, but different 2D footprint, I/O density, and planar wire inventory. This validation does not imply equal silicon area or power.'))


if __name__ == '__main__': main()
