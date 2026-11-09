#!/usr/bin/env python3
"""Prove native placement × routing and paper placement × routing input reuse."""
import concurrent.futures
import json
from pathlib import Path
import shutil
import sys

import three_baseline_common as common
from lazagna_common import ROOT,sha256,utc,write_json
from run_vpr import parse_metrics
from run_h3d_delay_study import route_body_hash

BASE=ROOT/'results/architecture_flow_20261027'
A0=ROOT/'artifacts/bin/baseline/vpr'
BINARY=ROOT/'artifacts/bin/flatland-edge-v2/vpr'


def run(family):
    common.BASE=BASE
    fixture=json.loads((BASE/'adapter_pilot_v2_protocol.json').read_text())['fixtures'][family]
    origin=Path(fixture['source_directory'])
    arch,graph=fixture['conversion']['architecture'],fixture['conversion']['graph']
    blif=ROOT/'vendor/vtr/vtr_flow/benchmarks/blif/ex5p.blif'
    for arm in ['a0','delay']:
        name=f'crossflow_smoke_{family}_native_place_{arm}'
        d=BASE/'runs'/name;d.mkdir(parents=True,exist_ok=False)
        packed,place=d/'packed.net',d/'placed.place'
        shutil.copy2(origin/'packed.net',packed)
        inputs=[arch,graph,blif,packed]
        command=[A0 if arm=='a0' else BINARY,arch,blif]
        if arm=='a0': command.append('--place')
        else:
            source=BASE/'runs'/f'crossflow_smoke_{family}_native_place_a0'/'placed.place'
            shutil.copy2(source,place);inputs.append(place)
        command.extend(['--route','--analysis','--device','fixture','--route_chan_width',100,
            '--num_workers',1,'--seed',1,'--clock_modeling','ideal','--check_route','full',
            '--verify_file_digests','off','--merge_constant_generators','off','--read_rr_graph',graph,
            '--max_router_iterations',200,'--routing_failure_predictor','off','--timing_report_npaths',0,
            '--net_file',packed,'--place_file',place,'--route_file',d/'routed.route'])
        env={} if arm=='a0' else dict(VPR_H3D_MODE='static',VPR_H3D_REACHABILITY='scc',
            VPR_H3D_GRAPH_ENCODING='edge',VPR_H3D_STATS='1',VPR_H3D_CANDIDATE_COST='delay')
        receipt=common.run(name,command,inputs=[command[0],*inputs],environment=env,timeout=1200)
        metrics=parse_metrics((d/'stdout.log').read_text())
        write_json(d/'result.json',dict(status=receipt['status'],metrics=metrics,
            route_body_sha256=route_body_hash(d/'routed.route') if (d/'routed.route').exists() else None))
        if not metrics['native_full_check_passed']:raise RuntimeError(name)


if __name__=='__main__':
    p=BASE/'crossflow_smoke_protocol.json'
    if p.exists():raise FileExistsError(p)
    write_json(p,dict(utc=utc(),circuit='ex5p',seed=1,architectures=['sb','cb_o','hybrid_o'],
        native_placement='Official A0 on paper-packed input and original physical graph',
        paper_placement='Archived complete P1 including weighted TritonPart',
        paper_placement_routes='Reuse adapter_pilot_v2_{family}_{a0,delay}',
        within_placement_pairs='Exact packed netlist, placement coordinates, graph, delays; private copies',
        purpose='Input compatibility and factor separation only; not a benchmark result',
        binaries={str(p):sha256(p) for p in [A0,BINARY]}))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,['sb','cb_o','hybrid_o']))
