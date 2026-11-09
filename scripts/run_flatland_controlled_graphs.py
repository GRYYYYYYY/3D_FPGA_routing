#!/usr/bin/env python3
"""Build registered controlled graphs without changing any author artifacts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json

import three_baseline_common as common
from lazagna_common import ROOT,utc,write_json

BASE=ROOT/'results/architecture_flow_20261027'
BINARY=ROOT/'artifacts/bin/flatland-buildfix/vpr'


def run(spec):
    family,size,width=spec;common.BASE=BASE
    arch=BASE/'controlled_architectures'/f'n{size}'/f'{family}.xml'
    blif=ROOT/'vendor/LaZagna/benchmarks/and2/and2.blif'
    name=f'controlled_graph_{family}_n{size}_w{width}_ideal'
    graph=BASE/'runs'/name/'rr_graph.xml'
    return common.run(name,[BINARY,arch,blif,'--pack','--device',f'controlled_{size}',
        '--route_chan_width',width,'--num_workers',1,'--clock_modeling','ideal','--write_rr_graph',graph],
        inputs=[BINARY,arch,blif],timeout=3600)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--size',type=int,default=25)
    parser.add_argument('--width',type=int,default=100);args=parser.parse_args()
    specs=[(f,args.size,args.width) for f in ['sb','cb_o','hybrid_o']]
    p=BASE/f'controlled_graph_n{args.size}_w{args.width}_protocol.json'
    if p.exists():raise FileExistsError(p)
    write_json(p,dict(utc=utc(),jobs=specs,clock_modeling='ideal',purpose='Check controlled architecture invariants before QoR experiments'))
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,specs))
