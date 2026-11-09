#!/usr/bin/env python3
"""Count actual packed logical blocks before QoR-independent device sizing."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import xml.etree.ElementTree as ET

from lxml import etree

from lazagna_common import ROOT, sha256, utc, write_json
from prepare_flatland_controlled_architectures import common_root
import three_baseline_common as common

BASE = ROOT/'results/architecture_flow_20261027'


def packed_summary(path):
    # Hash full canonical XML after only private filename and architecture ID
    # removal. Preserve all logical/pin/mode/content ordering and attributes.
    tree = etree.parse(str(path)); root = tree.getroot()
    root.attrib.pop('name', None); root.attrib.pop('architecture_id', None)
    counts = Counter(e.get('instance', '').split('[')[0] for e in root.findall('block'))
    return dict(block_counts=dict(counts), blocks=sum(counts.values()),
        semantic_sha256=hashlib.sha256(etree.tostring(root, method='c14n')).hexdigest())


def run(spec):
    circuit, info = spec
    protocol = json.loads((BASE/'benchmark_protocol.json').read_text())
    binary = protocol['binaries']['paper_buildfix']['path']
    arch = BASE/'census_architecture.xml'; blif = info['path']
    name = f'pack_census_{circuit}_s11'; d = BASE/'runs'/name
    receipt = common.run(name, [binary, arch, blif, '--pack', '--device', 'controlled_150',
        '--seed', 11, '--num_workers', 1, '--clock_modeling', 'ideal', '--route_chan_width', 100,
        '--net_file', d/'packed.net'], inputs=[binary, arch, blif], timeout=3600,
        environment={'OMP_NUM_THREADS':'1'})
    result = dict(circuit=circuit, status=receipt['status'], receipt=str(d/'manifest.json'))
    if (d/'packed.net').exists():
        result.update(packed_summary(d/'packed.net'))
        result['packed_sha256'] = sha256(d/'packed.net')
    write_json(d/'census.json', result)
    return result


def main():
    common.BASE = BASE
    registration = BASE/'pack_census_protocol.json'
    if registration.exists(): raise FileExistsError(registration)
    protocol = json.loads((BASE/'benchmark_protocol.json').read_text())
    root = common_root('sb', 150); ET.indent(root)
    arch = BASE/'census_architecture.xml'
    if arch.exists(): raise FileExistsError(arch)
    ET.ElementTree(root).write(arch, encoding='utf-8', xml_declaration=True)
    write_json(registration, dict(utc=utc(), benchmark_protocol_sha256=sha256(BASE/'benchmark_protocol.json'),
        circuits=list(protocol['benchmarks']), source_sha256=sha256(__file__), max_workers=4,
        purpose='Packing capacity census only, no placement/routing/QoR selection',
        architecture_sha256=sha256(arch)))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, protocol['benchmarks'].items()))
    write_json(BASE/'pack_census_summary.json', dict(utc=utc(), results=results))


if __name__ == '__main__': main()
