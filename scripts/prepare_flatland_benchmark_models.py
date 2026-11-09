#!/usr/bin/env python3
"""Prepare and audit one registered physical device shared by benchmark cases."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from itertools import zip_longest
import json
from pathlib import Path

from audit_flatland_controlled_planes import load
from audit_flatland_graphs import audit
from derive_flatland_common_plane import derive
from flatland_formats import prepare_import
from lazagna_common import ROOT, sha256, utc, write_json
from prepare_flatland_controlled_architectures import prepare as prepare_architectures
from prepare_flatland_matched_2d import prepare as prepare_2d
from run_flatland_controlled_graphs import run as generate_3d
from validate_flatland_common_plane import nonplanar_records, resources
from validate_flatland_pilots import semantic_records
from verify_flatland_import_stream import verify as verify_import
import three_baseline_common as common

BASE = ROOT/'results/architecture_flow_20261027'


def capacities(size):
    span = size-2
    dsp = 2*span*len(range(2, size-1, 8))
    ram = 2*span*len(range(4, size-1, 8))
    return dict(clb=2*span*span-dsp-ram, complex_dsp=dsp, spram=ram, io=64*span)


def choose_size(counts, protocol):
    assert set(counts) <= {'clb', 'complex_dsp', 'spram', 'io'}
    for size in protocol['sizing']['candidate_sides']:
        available = capacities(size)
        if all(n/available[k] <= .8 for k,n in counts.items()): return size
    raise ValueError('No registered capacity supports this circuit at <=80% per resource class')


def main(size, width):
    common.BASE = BASE
    assert width in (100, 300)
    protocol = json.loads((BASE/'benchmark_protocol.json').read_text())
    assert size in protocol['sizing']['candidate_sides']
    assert json.loads((BASE/'model_smoke_validation/summary.json').read_text())['passed']
    output = BASE/'benchmark_models'/f'n{size}_w{width}'
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'registration.json', dict(utc=utc(), size=size, width=width,
        protocol_sha256=sha256(BASE/'benchmark_protocol.json'), source_sha256=sha256(__file__),
        purpose='QoR-independent device preparation, exact topology and capacity audits', graph_workers=2))
    archdir = BASE/'controlled_architectures'/f'n{size}'
    if not archdir.exists(): prepare_architectures(size)
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(generate_3d, [(f,size,width) for f in ['sb','cb_o','hybrid_o']]))
    assert all(r['status'] == 'completed' for r in receipts)
    if not (archdir/'matched_2d.xml').exists(): prepare_2d(size, width)
    match = json.loads((archdir/'matched_2d_manifest.json').read_text())
    name = f'controlled_graph_matched_2d_n{size}_w{width}_ideal'
    two = BASE/'runs'/name/'rr_graph.xml'
    binary = ROOT/'artifacts/bin/flatland-buildfix/vpr'
    blif = ROOT/'vendor/LaZagna/benchmarks/and2/and2.blif'
    receipt = common.run(name, [binary, archdir/'matched_2d.xml', blif, '--pack', '--device', f'matched2d_{size}',
        '--route_chan_width', width, '--num_workers', 1, '--clock_modeling', 'ideal', '--write_rr_graph', two],
        inputs=[binary, archdir/'matched_2d.xml', blif], timeout=3600)
    assert receipt['status'] == 'completed'
    derive(size, width)
    models = json.loads((BASE/'common_plane_models/v2'/f'n{size}_w{width}'/'manifest.json').read_text())['models']
    reference = load(models['sb']['graph'])
    fixtures = {}; resource_rows = {}
    for family in ['sb','cb_o','hybrid_o','matched_2d']:
        original = BASE/'runs'/f'controlled_graph_{family}_n{size}_w{width}_ideal'/'rr_graph.xml'
        graph = Path(models[family]['graph']) if family != 'matched_2d' else original
        if family in ('cb_o','hybrid_o'):
            other = load(graph, reference['identities'])
            assert other['keys'] == reference['keys'] and other['edges'] == reference['edges']
            del other
            for a,b in zip_longest(nonplanar_records(original), nonplanar_records(graph)):
                assert a == b, f'{family}: nonplanar data changed'
        architecture = archdir/f'{family}.xml'
        row = audit(graph, architecture)
        slots = row['total_slots']; logical = {k:slots[k] for k in ['clb','complex_dsp','spram']}
        logical['io'] = slots['io']+slots.get('io_double',0)
        assert logical == capacities(size), (family, logical, capacities(size))
        assert row['unpaired_sb_nodes'] == 0 and row['nonzero_node_RC_count'] == 0
        row['logical_slots'] = logical; row['wire_resources'] = resources(graph)
        write_json(output/f'{family}_physical_audit.json', row); resource_rows[family] = row
        side = match['grid'][0] if family == 'matched_2d' else size
        converted = prepare_import(graph, architecture, output/family, width=side, height=side)
        schema_check = verify_import(graph, converted['graph'], converted['unused_segment_id'])
        fixtures[family] = dict(original_graph=str(graph), architecture=str(architecture), conversion=converted,
            native_schema_check=schema_check, physical_audit=str(output/f'{family}_physical_audit.json'))
        write_json(output/'progress.json', dict(utc=utc(), status='auditing', ready_families=list(fixtures)))
        print('benchmark model ready',size,width,family,flush=True)
    assert resource_rows['sb']['sb_pair_count'] == resource_rows['hybrid_o']['sb_pair_count']
    assert resource_rows['cb_o']['cb_crossing_source_rr_nodes'] == resource_rows['hybrid_o']['cb_crossing_source_rr_nodes']
    write_json(output/'manifest.json', dict(utc=utc(), status='ready', size=size, width=width, fixtures=fixtures,
        logical_slots=capacities(size), same_plane_exact=True,
        planar_wire_2d_over_3d=resource_rows['matched_2d']['wire_resources']['total_planar_wire_unit_capacity']/resource_rows['sb']['wire_resources']['total_planar_wire_unit_capacity'],
        limitation='Exact logical capacities and common 3D plane; 2D boundary/I/O/wire inventory differs. Hybrid has additional connectivity, not demonstrated equal physical area.'))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--size',type=int,required=True)
    parser.add_argument('--width',type=int,default=100); args=parser.parse_args()
    main(args.size,args.width)
