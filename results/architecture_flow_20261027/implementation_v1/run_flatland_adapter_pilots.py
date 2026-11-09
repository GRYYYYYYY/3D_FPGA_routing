#!/usr/bin/env python3
"""Controlled routing adapter probes on fixed paper placements; no QoR claims."""
import concurrent.futures
import json
from pathlib import Path
import shutil
import sys

import three_baseline_common as common
from flatland_formats import prepare_import
from lazagna_common import ROOT, sha256, utc, write_json
from run_vpr import parse_metrics
from run_h3d_delay_study import route_body_hash

BASE = ROOT/'results/architecture_flow_20261027'
BINARY = ROOT/'artifacts/bin/flatland-edge-v1/vpr'
A0 = ROOT/'artifacts/bin/baseline/vpr'
ENV = {'VPR_H3D_MODE':'static','VPR_H3D_REACHABILITY':'scc',
       'VPR_H3D_GRAPH_ENCODING':'edge','VPR_H3D_STATS':'1'}
ARMS = {'a0': {}, 'off': dict(ENV,VPR_H3D_MODE='off'),
        'geometry': dict(ENV,VPR_H3D_VALIDATE_SCC='1'),
        'delay': dict(ENV,VPR_H3D_CANDIDATE_COST='delay',VPR_H3D_VALIDATE_DELAY='1'),
        'budget1': dict(ENV,VPR_H3D_CANDIDATE_COST='delay',VPR_H3D_DELAY_BUDGET='1'),
        'critical': dict(ENV,VPR_H3D_MIN_CRITICALITY='0.9'),
        'delay_critical': dict(ENV,VPR_H3D_CANDIDATE_COST='delay',VPR_H3D_MIN_CRITICALITY='0.9')}


def register():
    p = BASE/'adapter_pilot_protocol.json'
    if p.exists(): raise FileExistsError(p)
    fixtures = {}
    for f in ['sb','cb_o','hybrid_o']:
        d = BASE/'runs'/f'placement_smoke_ex5p_{f}_paper_3d'
        m = json.loads((d/'manifest.json').read_text())
        assert m['status'] == 'completed'
        conversion = prepare_import(d/'rr_graph.xml',m['command'][1],BASE/'adapter_fixtures'/f)
        fixtures[f] = dict(conversion=conversion,source_directory=str(d),
            packed_sha256=sha256(d/'packed.net'),placement_sha256=sha256(d/'placed.place'))
    write_json(p,dict(utc=utc(),binary=str(BINARY),binary_sha256=sha256(BINARY),
        a0_sha256=sha256(A0),fixtures=fixtures,environments=ARMS,max_workers=3,
        jobs=[dict(family=f,arm=a,name=f'adapter_pilot_{f}_{a}') for f in fixtures for a in ARMS],
        checks=['off route body equals official A0','budget1 equals geometry','FULL plus independent route audit',
                'SCC vs BFS on real cross-layer connections','bounded delay results vs unbounded direct-edge oracle'],
        purpose='Adapter correctness only. ex5p is excluded from tuning and benchmark statistics.'))


def run(job):
    common.BASE = BASE
    protocol = json.loads((BASE/'adapter_pilot_protocol.json').read_text())
    family, arm, name = job['family'],job['arm'],job['name']
    fixture = protocol['fixtures'][family]; source = Path(fixture['source_directory'])
    d = BASE/'runs'/name;d.mkdir(parents=True,exist_ok=False)
    packed, place = d/'packed.net',d/'fixed.place'
    shutil.copy2(source/'packed.net',packed);shutil.copy2(source/'placed.place',place)
    binary = A0 if arm == 'a0' else BINARY
    arch, graph = fixture['conversion']['architecture'],fixture['conversion']['graph']
    blif = ROOT/'vendor/vtr/vtr_flow/benchmarks/blif/ex5p.blif'
    command = [binary,arch,blif,'--route','--analysis','--device','fixture','--route_chan_width',100,
        '--num_workers',1,'--seed',1,'--clock_modeling','ideal','--check_route','full',
        '--verify_file_digests','off','--merge_constant_generators','off','--read_rr_graph',graph,
        '--max_router_iterations',200,'--routing_failure_predictor','off','--timing_report_npaths',0,
        '--net_file',packed,'--place_file',place,'--route_file',d/'routed.route']
    receipt = common.run(name,command,inputs=[binary,arch,graph,blif,packed,place],
                         environment=ARMS[arm],timeout=1200)
    metrics = parse_metrics((d/'stdout.log').read_text())
    write_json(d/'result.json',dict(family=family,arm=arm,status=receipt['status'],metrics=metrics,
        source_directory=str(source),route_body_sha256=route_body_hash(d/'routed.route') if (d/'routed.route').exists() else None,
        outputs={p.name:sha256(p) for p in [packed,place,d/'routed.route',d/'stdout.log'] if p.exists()}))


if __name__ == '__main__':
    if sys.argv[1] == 'register': register()
    elif sys.argv[1] == 'run':
        p = json.loads((BASE/'adapter_pilot_protocol.json').read_text())
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(run,p['jobs']))
