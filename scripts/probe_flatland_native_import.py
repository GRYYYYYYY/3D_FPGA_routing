#!/usr/bin/env python3
"""Test lossless graph schema migration; arch shells must never generate graphs."""
import concurrent.futures
import json
import re
import sys
import xml.etree.ElementTree as ET

import three_baseline_common as common
from lazagna_common import ROOT, sha256, utc, write_json

BASE = ROOT/'results/architecture_flow_20261027'
A0 = ROOT/'artifacts/bin/baseline/vpr'
SOURCE_NAMES = {f: f'graph_{f}_25_w100_routeclock' + ('_explicit' if f in ('cb_o','hybrid_o') else '')
                for f in ('2d', 'sb', 'cb_o', 'hybrid_o')}


def prepare(family):
    source_dir = BASE/'runs'/SOURCE_NAMES[family]
    original = json.loads((source_dir/'manifest.json').read_text())
    if original['status'] != 'completed': raise ValueError('Source graph failed')
    target = BASE/'native_import'/family; target.mkdir(parents=True, exist_ok=False)
    arch = target/'import_shell.xml'
    root = ET.parse(original['command'][1]).getroot()
    removed = 0
    for locations in root.findall('tiles/tile/sub_tile/pinlocations'):
        grouped = {}
        for loc in list(locations):
            if 'layer_offset' in loc.attrib:
                removed += 1
                del loc.attrib['layer_offset']
            key = tuple(sorted(loc.attrib.items()))
            if key in grouped:
                grouped[key].text = ' '.join(((grouped[key].text or '') + ' ' + (loc.text or '')).split())
                locations.remove(loc)
            else:
                grouped[key] = loc
    ET.indent(root)
    ET.ElementTree(root).write(arch, encoding='utf-8', xml_declaration=True)
    graph = target/'rr_graph.xml'
    changed = 0
    with (source_dir/'rr_graph.xml').open() as src, graph.open('x') as out:
        for line in src:
            if '<loc ' in line:
                matches = re.findall(r'\blayer="(\d+)"', line)
                if len(matches) != 1: raise ValueError('Unexpected old node coordinates')
                line = re.sub(r'\blayer="(\d+)"', r'layer_low="\1" layer_high="\1"', line)
                twists = re.findall(r'\btwist="([^"]+)"', line)
                if any(t != '0' for t in twists): raise ValueError('Cannot discard a nonzero twist')
                line = re.sub(r' twist="0"', '', line)
                changed += 1
            out.write(line)
    write_json(target/'conversion.json', dict(utc=utc(), source_graph=str(source_dir/'rr_graph.xml'),
        source_graph_sha256=sha256(source_dir/'rr_graph.xml'), converted_graph_sha256=sha256(graph),
        changed_node_location_records=changed, layer_offset_records_removed_from_shell=removed,
        limitation='Architecture is an import shell only. Cross-layer pin routing remains exclusively in the imported graph. Do NOT generate native graphs from this shell.',
        preserved='All node IDs, geometry, capacity, direction, switches, edges, delays unchanged; layer scalar becomes equal low/high, zero twist omitted'))
    return arch, graph


def run(family):
    common.BASE = BASE
    arch, graph = prepare(family)
    blif = ROOT/'vendor/LaZagna/benchmarks/and2/and2.blif'
    name = 'native_import_' + family
    device = 'probe25' if family in ('cb_o', 'hybrid_o') else '25x25'
    return common.run(name, [A0, arch, blif, '--pack', '--device', device,
        '--route_chan_width', 100, '--num_workers', 1, '--read_rr_graph', graph,
        '--clock_modeling', 'route', '--verify_file_digests', 'off'], inputs=[A0, arch, graph, blif], timeout=600)


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(run, sys.argv[1:] or list(SOURCE_NAMES)))
