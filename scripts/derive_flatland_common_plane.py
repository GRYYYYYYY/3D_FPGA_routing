#!/usr/bin/env python3
"""Construct explicit counterfactual architectures with identical planar fabric.

This is architecture preparation, never an operation performed by the router.
CB/SB cross-layer resources remain those of the registered generated graphs.
The original graphs and paper architectures are retained without modification.
"""
import argparse
from array import array
from collections import Counter
import re

from compare_lazagna_graphs import records
from lazagna_common import ROOT, sha256, utc, write_json

BASE = ROOT / 'results/architecture_flow_20261027'
EDGE = re.compile(r'<edge\s+([^<>]*?)(?:/>|></edge>)')
ATTR = re.compile(r'(\w+)="(\d+)"')


def parse_edge(line):
    match = EDGE.fullmatch(line.strip())
    if match is None:
        raise ValueError('Unexpected edge children')
    attributes = ATTR.findall(match[1])
    assert len(attributes) == 3 and not ATTR.sub('', match[1]).strip()
    attributes = dict(attributes)
    assert set(attributes) == {'src_node', 'sink_node', 'switch_id'}
    return tuple(int(attributes[k]) for k in ['src_node', 'sink_node', 'switch_id'])


def canonical(element, omit=()):
    return (element.tag, tuple(sorted((k, v) for k, v in element.attrib.items() if k not in omit)),
            (element.text or '').strip(), tuple(canonical(c) for c in element))


def metadata(path):
    switches = {}; segments = {}; keys = []; layers = array('h'); ordinary = {}
    for section, element in records(path):
        if section == 'switches':
            switches[int(element.get('id'))] = canonical(element, ('id',))
        elif section == 'segments':
            segments[int(element.get('id'))] = canonical(element, ('id',))
        elif section == 'rr_nodes':
            assert int(element.get('id')) == len(keys)
            loc = element.find('loc'); layer = int(loc.get('layer')); layers.append(layer)
            half = element.get('type') == 'CHANX' and element.get('direction') == 'NONE'
            seg = element.find('segment')
            key = None if half else (canonical(element, ('id',)), segments[int(seg.get('segment_id'))] if seg is not None else None)
            keys.append(key)
            if key is not None:
                assert key not in ordinary
                ordinary[key] = len(keys) - 1
        elif section == 'rr_edges':
            break
    return dict(keys=keys, ordinary=ordinary, layers=layers, switches=switches)


def plane(meta, u, v):
    return meta['keys'][u] is not None and meta['keys'][v] is not None and meta['layers'][u] == meta['layers'][v]


def edge_records(path):
    with path.open() as stream:
        for line in stream:
            if line.lstrip().startswith('<edge '):
                yield parse_edge(line)


def derive(size, width):
    sources = {f: BASE/'runs'/f'controlled_graph_{f}_n{size}_w{width}_ideal'/'rr_graph.xml'
               for f in ['sb', 'cb_o', 'hybrid_o']}
    destination = BASE/'common_plane_models'/'v2'/f'n{size}_w{width}'
    destination.mkdir(parents=True, exist_ok=False)
    reference = metadata(sources['sb'])
    output = {'sb': dict(graph=str(sources['sb']), sha256=sha256(sources['sb']), transformation='none')}
    for family in ['cb_o', 'hybrid_o']:
        target = metadata(sources[family])
        assert reference['ordinary'].keys() == target['ordinary'].keys()
        mapping = array('i', (target['ordinary'].get(k, -1) for k in reference['keys']))
        switch_lookup = {v: k for k, v in target['switches'].items()}
        assert len(switch_lookup) == len(target['switches'])
        switch_map = {k: switch_lookup[v] for k, v in reference['switches'].items()}
        path = destination/f'{family}.xml'
        counts = Counter()
        with sources[family].open() as src, path.open('x') as out:
            for line in src:
                if line.lstrip().startswith('<edge '):
                    u, v, s = parse_edge(line)
                    if plane(target, u, v):
                        counts['removed_planar_records'] += 1
                        continue
                    counts['preserved_nonplanar_records'] += 1
                elif '</rr_edges>' in line:
                    for u, v, s in edge_records(sources['sb']):
                        if plane(reference, u, v):
                            out.write(f'<edge src_node="{mapping[u]}" sink_node="{mapping[v]}" switch_id="{switch_map[s]}"/>\n')
                            counts['inserted_reference_planar_records'] += 1
                out.write(line)
        assert counts['removed_planar_records'] == counts['inserted_reference_planar_records']
        output[family] = dict(graph=str(path), sha256=sha256(path), counts=dict(counts),
            ordinary_nodes=len(target['ordinary']), transformation='Replace ordinary same-layer edges by exact physical-node/switch mapping from SB; preserve all other records verbatim')
        print(family, dict(counts), flush=True)
    write_json(destination/'manifest.json', dict(utc=utc(), models=output,
        source_graphs={str(p): sha256(p) for p in sources.values()}, script_sha256=sha256(__file__),
        status='constructed; independent comparison and legal routes required',
        purpose='Counterfactual common-planar architecture family; NOT unchanged author architecture reproduction',
        cause='Author get_unidir_opin_connections increments shared Fc_ofs for both planar and cross-layer calls; enabling CB output crossings changes later planar destinations',
        preserved='Node identities/capacities/RC, exact switches/delays, grid, CB crossing edges, complete SB forced-pair paths',
        cost_qualification='Hybrid adds CB connections to SB. Equal area, mux cost, power, and independent physical via budget are NOT established.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--size', type=int, default=25)
    parser.add_argument('--width', type=int, default=100)
    args = parser.parse_args(); derive(args.size, args.width)
