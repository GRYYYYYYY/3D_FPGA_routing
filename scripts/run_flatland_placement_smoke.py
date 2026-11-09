#!/usr/bin/env python3
"""Exercise complete published placement, including actual weighted partitioning."""
import concurrent.futures
import json
import sys

import three_baseline_common as common
from lazagna_common import ROOT

BASE = ROOT/'results/architecture_flow_20261027'


def run(spec):
    family, flow = spec.split(':') if ':' in spec else ('sb', spec)
    common.BASE = BASE
    name = 'placement_smoke_ex5p_' + family + '_' + flow
    directory = BASE/'runs'/name
    arch = ROOT/'vendor/beyond-flatland-src/Architecture_Files/sb_architecture.xml' if family == 'sb' else BASE/'architectures'/f'{family}_probe25.xml'
    blif = ROOT/'vendor/vtr/vtr_flow/benchmarks/blif/ex5p.blif'
    binary = ROOT/'artifacts/bin'/('flatland-buildfix' if flow == 'published_default' else 'flatland-triton-integrated')/'vpr'
    command = [binary, arch, blif, '--device', '25x25' if family == 'sb' else 'probe25', '--route_chan_width', 100,
        '--num_workers', 1, '--seed', 1, '--clock_modeling', 'ideal',
        '--check_route', 'full', '--max_router_iterations', 200,
        '--routing_failure_predictor', 'off', '--timing_report_npaths', 0,
        '--net_file', directory/'packed.net', '--place_file', directory/'placed.place',
        '--route_file', directory/'routed.route', '--write_rr_graph', directory/'rr_graph.xml']
    if flow == 'paper_3d':
        data = json.loads((BASE/'published_reference_analysis.json').read_text())
        label = {'sb':'SB', 'cb_o':'CB-O', 'hybrid_o':'Hybrid-O'}[family]
        configs = data['datasets'][label+'_paper']['configs']
        unique = {json.dumps(x, sort_keys=True) for x in configs.values()}
        if len(unique) != 1: raise ValueError('Paper SB config varies by circuit')
        for key, value in json.loads(unique.pop()).items():
            command.extend([key, str(value)])
        command.extend(['--partition_post_pack', '--soft_partitioning', 'init_place'])
    return common.run(name, command, inputs=[binary,arch,blif], timeout=1200)


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(run, sys.argv[1:] or ['published_default', 'integrated_default', 'paper_3d']))
