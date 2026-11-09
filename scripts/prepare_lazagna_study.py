#!/usr/bin/env python3
"""Freeze the study scope and compare architecture specifications structurally."""
import copy
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from lazagna_common import BASE, PAPER, ROOT, sha256, utc, write_json


def canonical(e):
    return [e.tag, sorted(e.attrib.items()), ' '.join((e.text or '').split()),
            [canonical(c) for c in e]]


def prepare_arch(source, label, size, delay_ratio=None):
    root = ET.parse(source).getroot()
    layout = root.find('layout')
    layers = [copy.deepcopy(x) for x in layout[0].findall('layer')]
    layout.clear()
    fixed = ET.SubElement(layout, 'fixed_layout', name=f'study_{size}', width=str(size), height=str(size))
    fixed.extend(layers)
    if delay_ratio is not None:
        switches = root.find('switchlist')
        base = float(switches.find("switch[@name='L4_driver']").get('Tdel'))
        # Reproduce the original arch_xml_modification.py division by three.
        # Its comment assumes three identical switches; the graph audit checks
        # actual switch IDs (the published SB creator uses a plane driver last).
        switches.find("switch[@name='3D_SB_switch']").set('Tdel', str(base * delay_ratio / 3))
    ET.indent(root, space='  ')
    target = BASE / 'architectures' / f'{label}_{size}.xml'
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise RuntimeError(f'Existing architecture: {target}')
    ET.ElementTree(root).write(target, encoding='utf-8', xml_declaration=True)
    return dict(path=str(target), sha256=sha256(target), source=str(source),
                source_sha256=sha256(source), grid=[size,size,2], delay_ratio=delay_ratio)


def main():
    if (BASE/'protocol.json').exists():
        raise RuntimeError('Protocol already frozen')
    paper_arch = PAPER / 'arch_files/templates/dsp_bram/vtr_arch_dsp_bram.xml'
    beyond_arch = ROOT / 'benchmarks/downloads/beyond_flatland/sb_architecture.xml'
    native_arch = ROOT / 'configs/architectures/koios_native3d_n6_f16_d1_v3.xml'
    paths = [paper_arch,beyond_arch,native_arch]
    roots = [ET.parse(p).getroot() for p in paths]
    equalities = {}
    for tag in ['models','complexblocklist','tiles']:
        equalities[tag] = dict(paper_equals_beyond=canonical(roots[0].find(tag))==canonical(roots[1].find(tag)),
                               paper_equals_native=canonical(roots[0].find(tag))==canonical(roots[2].find(tag)))
    native_tiles = copy.deepcopy(roots[2].find('tiles'))
    removed = 0
    for fc in native_tiles.findall('tile/sub_tile/fc'):
        for child in list(fc):
            if child.attrib == dict(fc_type='abs',fc_val='0',segment_name='z_segment'):
                fc.remove(child); removed += 1
    equalities['tiles_ignoring_explicit_zero_direct_Z_Fc'] = canonical(native_tiles)==canonical(roots[0].find('tiles'))
    evidence = dict(created_utc=utc(),sources=[dict(path=str(p),sha256=sha256(p)) for p in paths],
                    equalities=equalities,removed_zero_z_fc_overrides=removed,
                    paper_template_segments=[e.attrib for e in roots[0].findall('segmentlist/segment')],
                    native_segments=[e.attrib for e in roots[2].findall('segmentlist/segment')],
                    paper_table_segments={'L4_tracks':260,'L16_tracks':40},
                    warning='Paper table states 260:40 while published XML segment frequency weights are 280:40. Keep as-released XML primary and report this discrepancy; inspect generated counts.')
    write_json(BASE/'architecture_specification_comparison.json',evidence)
    arches={}
    for size in [40,100]:
        arches[f'paper_{size}']=prepare_arch(paper_arch,'paper',size,.739)
        arches[f'native_{size}']=prepare_arch(native_arch,'native',size)
    inputs = ['results/analysis.json','results/failure_diagnosis/analysis_native.json',
              'configs/sources.lock.json','configs/failure_diagnosis_native.json',str(native_arch)]
    plan=dict(created_utc=utc(),scope='Reproduce paper-era LaZagna PnR conditions and audit DSP/planar/inter-layer graph correspondence.',
              paper_source='https://arxiv.org/abs/2505.05579v1',
              source_selection='Last public LaZagna commit on 2025-05-08; author experiment commit is not specified in the paper.',
              sources={'lazagna':'16fa62c9385843144f9d00c3827e1d87accec4fb',
                       'openfpga':'729e6187fe9e88b8c24399cfe852bcd3b3fb9291',
                       'vtr':'a80511e8f96d560e680d2ebe9c18272a759ce493',
                       'yosys':'1bf908dea8e09f29e10b7eb44501151a63c68eb3'},
              paper_parameters={'grid':[100,100,2],'channel_width':300,'sb_fraction':.5,
                                'sb_pattern':'subset','sb_location':'repeated_interval','vertical_track_fraction':1,
                                'vertical_delay_ratio':.739,'placement':'cube_bb','seed':1},
              diagnostics={'small_grid':[40,40,2],'widths':[100,300],
                           'focus_cases':['attention_layer','conv_layer','dla_like.small','dla_like.medium','bnn','lstm','tpu_like.small.ws','tpu_like.large.ws','clstm_like.small','robot_rl','conv_layer_hls'],
                           'netlists':'Use the exact published BLIF inputs of the existing study to avoid a synthesis confound. Separately assess completeness of the historical Verilog synthesis flow.',
                           'graph_audit':'Canonical physical node/edge identities; collapse paired legacy vertical nodes only with explicit physical-channel mapping.',
                           'interpretation':'Changing toolchain, graph, packing or placement is not an algorithm-only comparison. Every run retains actual stage outcome; unsupported inputs, timeouts and capacity failures are separate.'},
              architectures=arches,protected_files={str(Path(p).resolve()):sha256(p) for p in inputs},
              status='sources_and_build_in_progress')
    write_json(BASE/'protocol.json',plan)
    print(json.dumps({'protocol':str(BASE/'protocol.json'),'specification':evidence},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
