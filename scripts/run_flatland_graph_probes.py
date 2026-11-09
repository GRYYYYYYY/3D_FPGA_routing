#!/usr/bin/env python3
"""Generate original paper graphs before deciding how to adapt our router."""
import concurrent.futures
import sys
import copy
import xml.etree.ElementTree as ET

import three_baseline_common as common
from lazagna_common import ROOT, sha256, utc, write_json

BASE = ROOT / 'results/architecture_flow_20261027'
PAPER = ROOT / 'artifacts/bin/flatland-buildfix/vpr'
ARCH = ROOT / 'vendor/beyond-flatland-src/Architecture_Files'
BLIF = ROOT / 'vendor/LaZagna/benchmarks/and2/and2.blif'


def run(family, explicit=False):
    common.BASE = BASE
    source = ARCH / f'{family}_architecture.xml'
    name = 'graph_' + family + '_25_w100_routeclock'
    if explicit:
        original = source
        root = ET.parse(original).getroot()
        layout = root.find('layout')
        chosen = [x for x in layout if x.get('width') == ('35' if family == '2d' else '25')]
        if len(chosen) != 1:
            raise ValueError('Expected a unique grid by physical size')
        fixed = copy.deepcopy(chosen[0]); fixed.set('name', 'probe25')
        layout.clear(); layout.append(fixed)
        source = BASE / 'architectures' / f'{family}_probe25.xml'
        source.parent.mkdir(exist_ok=True)
        if source.exists():
            raise FileExistsError(source)
        ET.indent(root)
        ET.ElementTree(root).write(source, encoding='utf-8', xml_declaration=True)
        name += '_explicit'
        write_json(source.with_suffix('.json'), dict(source=str(original), source_sha256=sha256(original),
            derivative_sha256=sha256(source), change='Select one fixed layout by dimensions, rename it probe25; all non-layout XML unchanged'))
    output = BASE / 'runs' / name / 'rr_graph.xml'
    command = [PAPER, source, BLIF, '--pack', '--device', 'probe25' if explicit else '25x25',
               '--route_chan_width', 100, '--num_workers', 1,
               '--clock_modeling', 'route', '--write_rr_graph', output]
    return common.run(name, command, inputs=[PAPER, source, BLIF], timeout=600)


if __name__ == '__main__':
    explicit = '--explicit' in sys.argv
    families = [x for x in sys.argv[1:] if x != '--explicit'] or ['2d', 'sb', 'cb_o', 'hybrid_o']
    protocol = BASE / 'graph_probe_protocol.json'
    if not protocol.exists():
        write_json(protocol, dict(utc=utc(), families=families, binary_sha256=sha256(PAPER),
            purpose='Schema/topology/resource probe only, not QoR or a matched 2D comparison',
            original_architectures=True, device_name='25x25', channel_width=100,
            clocks='route', workers_per_process=1, max_concurrent=4))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(lambda family: run(family, explicit), families):
            print(result['name'], result['status'])
