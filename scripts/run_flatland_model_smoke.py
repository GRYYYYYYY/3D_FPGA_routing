#!/usr/bin/env python3
"""Legal-flow gate for explicit common-plane 3D and matched-capacity 2D."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil

from flatland_formats import prepare_import
from lazagna_common import ROOT, sha256, utc, write_json
from run_vpr import parse_metrics
from run_flatland_pack_census import packed_summary
import three_baseline_common as common

BASE = ROOT/'results/architecture_flow_20261027'
A0 = ROOT/'artifacts/bin/baseline/vpr'
R1 = ROOT/'artifacts/bin/flatland-edge-v2/vpr'
P1 = ROOT/'artifacts/bin/flatland-triton-integrated/vpr'
BLIF = ROOT/'vendor/vtr/vtr_flow/benchmarks/blif/ex5p.blif'
ENV = dict(VPR_H3D_MODE='static', VPR_H3D_REACHABILITY='scc', VPR_H3D_GRAPH_ENCODING='edge',
           VPR_H3D_CANDIDATE_COST='delay', VPR_H3D_STATS='1')


def run(family):
    protocol = json.loads((BASE/'model_smoke_protocol.json').read_text())
    fixture = protocol['fixtures'][family]; conversion = fixture['conversion']
    controls = ['p0_a0', 'p0_delay'] if family == 'matched_2d' else ['p0_a0', 'p0_delay', 'p1_paper', 'p1_a0', 'p1_delay']
    source_packed = BASE/'runs/placement_smoke_ex5p_sb_paper_3d/packed.net'
    for control in controls:
        name = f'model_smoke_{family}_{control}'
        d = BASE/'runs'/name; d.mkdir(parents=True, exist_ok=False)
        packed, place = d/'packed.net', d/'placed.place'
        paper = control == 'p1_paper'
        binary = P1 if paper else R1 if control.endswith('delay') else A0
        arch = fixture['architecture'] if paper else conversion['architecture']
        graph = fixture['graph'] if paper else conversion['graph']
        command = [binary, arch, BLIF]
        inputs = [binary, arch, graph, BLIF]
        if not paper:
            if control.startswith('p1'):
                origin = BASE/'runs'/f'model_smoke_{family}_p1_paper'
                shutil.copy2(origin/'packed.net', packed)
                shutil.copy2(origin/'placed.place', place)
                inputs.append(place)
            else:
                shutil.copy2(source_packed, packed)
                if control == 'p0_a0': command.append('--place')
                else:
                    shutil.copy2(BASE/'runs'/f'model_smoke_{family}_p0_a0/placed.place', place)
                    inputs.append(place)
            inputs.append(packed); command.extend(['--route', '--analysis'])
        command.extend(['--device', 'controlled_25' if paper else 'fixture', '--route_chan_width', 100,
            '--num_workers', 1, '--seed', 1, '--clock_modeling', 'ideal', '--check_route', 'full',
            '--verify_file_digests', 'off', '--read_rr_graph', graph, '--max_router_iterations', 200,
            '--routing_failure_predictor', 'off', '--timing_report_npaths', 0,
            '--net_file', packed, '--place_file', place, '--route_file', d/'routed.route'])
        if paper:
            label = dict(sb='SB', cb_o='CB-O', hybrid_o='Hybrid-O')[family]
            configs = json.loads((BASE/'published_reference_analysis.json').read_text())['datasets'][label+'_paper']['configs']
            unique = {json.dumps(x, sort_keys=True) for x in configs.values()}; assert len(unique) == 1
            for k, v in json.loads(unique.pop()).items(): command.extend([k, str(v)])
            command.extend(['--partition_post_pack', '--soft_partitioning', 'init_place'])
        else: command.extend(['--merge_constant_generators', 'off'])
        receipt = common.run(name, command, inputs=inputs, environment=ENV if binary == R1 else {}, timeout=1200)
        metrics = parse_metrics((d/'stdout.log').read_text())
        write_json(d/'result.json', dict(status=receipt['status'], metrics=metrics, family=family, control=control))
        assert metrics['native_full_check_passed'] and metrics['routing_success_reported'], name
        assert packed_summary(packed)['semantic_sha256'] == packed_summary(source_packed)['semantic_sha256'], name


def main():
    common.BASE = BASE
    output = BASE/'model_smoke_protocol.json'
    if output.exists(): raise FileExistsError(output)
    model_dir = BASE/'common_plane_models/v2/n25_w100'
    manifest = json.loads((model_dir/'manifest.json').read_text())
    fixtures = {}
    for family in ['sb', 'cb_o', 'hybrid_o', 'matched_2d']:
        graph = manifest['models'][family]['graph'] if family != 'matched_2d' else BASE/'runs/controlled_graph_matched_2d_n25_w100_ideal/rr_graph.xml'
        arch = BASE/'controlled_architectures/n25'/f'{family}.xml'
        size = 35 if family == 'matched_2d' else 25
        conversion = prepare_import(graph, arch, BASE/'model_fixtures/n25_w100'/family, width=size, height=size)
        fixtures[family] = dict(graph=str(graph), architecture=str(arch), conversion=conversion)
    write_json(output, dict(utc=utc(), fixtures=fixtures, circuit='ex5p', seed=1, max_workers=2,
        purpose='Controlled-model legality and packing/placement compatibility only; excluded from formal QoR dataset',
        binaries={str(p):sha256(p) for p in [A0, R1, P1]}, script_sha256=sha256(__file__)))
    with ThreadPoolExecutor(max_workers=2) as pool: list(pool.map(run, fixtures))


if __name__ == '__main__': main()
