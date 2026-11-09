#!/usr/bin/env python3
"""Explicit old-to-native import schema adaptation, without changing graph topology."""
import copy
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from lazagna_common import sha256, utc, write_json


def prepare_import(source_graph, source_architecture, directory, width=25, height=25):
    source_graph, source_architecture, directory = map(Path, (source_graph, source_architecture, directory))
    directory.mkdir(parents=True, exist_ok=False)
    root = ET.parse(source_architecture).getroot()
    layout = root.find('layout')
    selected = [x for x in layout if x.get('width') == str(width) and x.get('height') == str(height)]
    if len(selected) != 1: raise ValueError('Select layout by physical dimensions, not ambiguous names')
    fixed = copy.deepcopy(selected[0]); fixed.set('name', 'fixture')
    layout.clear(); layout.append(fixed)
    for locations in root.findall('tiles/tile/sub_tile/pinlocations'):
        grouped = {}
        for loc in list(locations):
            loc.attrib.pop('layer_offset', None)
            key = tuple(sorted(loc.attrib.items()))
            if key in grouped:
                grouped[key].text = ' '.join(((grouped[key].text or '')+' '+(loc.text or '')).split())
                locations.remove(loc)
            else: grouped[key] = loc
    if root.find('switchblocklist') is not None: root.remove(root.find('switchblocklist'))
    sw = root.find('device/switch_block'); sw.attrib.clear(); sw.set('type','wilton'); sw.set('fs','3')
    segments = root.find('segmentlist')
    unused_id = len(segments) if len(fixed.findall('layer')) > 1 else None
    if unused_id is not None:
        z = ET.SubElement(segments,'segment',name='unused_native_Z_schema',freq='0',length='1',axis='z',type='unidir',Rmetal='0',Cmetal='0')
        ET.SubElement(z,'mux',name='L4_driver')
        ET.SubElement(z,'sb',type='pattern').text='0 0'
        ET.SubElement(z,'cb',type='pattern').text='0'
        for fc in root.findall('tiles/tile/sub_tile/fc'):
            ET.SubElement(fc,'fc_override',fc_type='abs',fc_val='0',segment_name='unused_native_Z_schema')
    arch = directory/'import_only.xml'; ET.indent(root)
    ET.ElementTree(root).write(arch,encoding='utf-8',xml_declaration=True)
    graph = directory/'rr_graph.xml'
    changed = 0
    with source_graph.open() as src, graph.open('x') as out:
        for line in src:
            if '<loc ' in line:
                if len(re.findall(r'\blayer="(\d+)"',line)) != 1:
                    raise ValueError('Expected exactly one old node layer')
                line = re.sub(r'\blayer="(\d+)"',r'layer_low="\1" layer_high="\1"',line)
                if any(t != '0' for t in re.findall(r'\btwist="([^"]+)"',line)):
                    raise ValueError('Nonzero twist requires an explicit model')
                line = re.sub(r' twist="0"','',line); changed += 1
            if '</segments>' in line and unused_id is not None:
                out.write(f'<segment id="{unused_id}" name="unused_native_Z_schema" length="1" res_type="GENERAL"><timing/></segment>\n')
            out.write(line)
    result = dict(utc=utc(), source_graph=str(source_graph), source_architecture=str(source_architecture),
        source_graph_sha256=sha256(source_graph), source_architecture_sha256=sha256(source_architecture),
        graph=str(graph), architecture=str(arch), graph_sha256=sha256(graph), architecture_sha256=sha256(arch),
        converted_node_locations=changed, unused_segment_id=unused_id,
        contract='Imported graph is authoritative; node IDs, geometry, directions, capacities, edges, switches and delays preserved. Import shell may NEVER generate a native graph.',
        shell_changes='Select exact grid; merge pin-location layer attributes; inert Wilton parse placeholder; zero-frequency, zero-Fc unused Z metadata')
    write_json(directory/'conversion.json',result)
    return result
