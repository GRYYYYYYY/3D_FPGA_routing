#!/usr/bin/env python3
"""Check modern LaZagna on the exact same original paper graph and placement."""
import concurrent.futures
import json
from pathlib import Path
import shutil

import three_baseline_common as common
from lazagna_common import ROOT,sha256,utc,write_json
from run_vpr import parse_metrics

BASE=ROOT/'results/architecture_flow_20261027'
B2=ROOT/'artifacts/bin/lazagna-vtr9-port-buildfix/vpr'


def run(family):
    common.BASE=BASE
    source=BASE/'runs'/f'placement_smoke_ex5p_{family}_paper_3d'
    prior=json.loads((source/'manifest.json').read_text())
    arch=prior['command'][1];graph=source/'rr_graph.xml'
    name=f'b2_shared_graph_smoke_{family}'
    d=BASE/'runs'/name;d.mkdir(parents=True,exist_ok=False)
    packed,place=d/'packed.net',d/'fixed.place'
    shutil.copy2(source/'packed.net',packed);shutil.copy2(source/'placed.place',place)
    blif=ROOT/'vendor/vtr/vtr_flow/benchmarks/blif/ex5p.blif'
    command=[B2,arch,blif,'--route','--analysis','--device','25x25' if family=='sb' else 'probe25',
        '--route_chan_width',100,'--num_workers',1,'--seed',1,'--clock_modeling','ideal',
        '--check_route','full','--verify_file_digests','off','--read_rr_graph',graph,
        '--max_router_iterations',200,'--routing_failure_predictor','off','--timing_report_npaths',0,
        '--net_file',packed,'--place_file',place,'--route_file',d/'routed.route']
    r=common.run(name,command,inputs=[B2,arch,graph,blif,packed,place],timeout=1200)
    write_json(d/'result.json',dict(status=r['status'],metrics=parse_metrics((d/'stdout.log').read_text()),
        meaning='Toolchain/router comparison on common physical graph, packed netlist, placement and clock model; does not reproduce the LaZagna paper architecture'))


if __name__=='__main__':
    p=BASE/'b2_shared_graph_smoke_protocol.json'
    if p.exists():raise FileExistsError(p)
    write_json(p,dict(utc=utc(),binary=str(B2),binary_sha256=sha256(B2),
        families=['sb','cb_o','hybrid_o'],circuit='ex5p',purpose='Compatibility of third-party B2 with new common-graph controls'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,['sb','cb_o','hybrid_o']))
