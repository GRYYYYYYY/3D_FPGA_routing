#!/usr/bin/env python3
"""Preserve a demonstrated capacity failure and freeze effective packed inputs."""
import json
import xml.etree.ElementTree as ET

from lazagna_common import ROOT,sha256,utc,write_json
from prepare_flatland_benchmark_models import capacities,choose_size
from prepare_flatland_controlled_architectures import common_root
from run_flatland_pack_census import packed_summary
import three_baseline_common as common

BASE=ROOT/'results/architecture_flow_20261027'


def main():
    common.BASE=BASE
    output=BASE/'capacity_selection.json'
    if output.exists():raise FileExistsError(output)
    p=json.loads((BASE/'benchmark_protocol.json').read_text())
    census=json.loads((BASE/'pack_census_summary.json').read_text())['results']
    failed=[x for x in census if x['status']!='completed']
    assert len(census)==20 and [x['circuit'] for x in failed]==['gemm_layer']
    old=BASE/'runs/pack_census_gemm_layer_s11'
    log=(old/'stdout.log').read_text()
    assert 'required: io: 1800, clb: 35529, complex_dsp: 200' in log
    assert 'available io: 9472, clb: 32560, complex_dsp: 5624' in log
    amendment=BASE/'census_capacity_amendment.json'
    assert not amendment.exists()
    arch=BASE/'census_architecture_n200.xml';root=common_root('sb',200);ET.indent(root)
    ET.ElementTree(root).write(arch,encoding='utf-8',xml_declaration=True)
    write_json(amendment,dict(utc=utc(),protocol_sha256=sha256(BASE/'benchmark_protocol.json'),
        trigger='gemm_layer capacity failure at census150, including VPR internal retries',
        original_receipt=str(old/'manifest.json'),original_receipt_sha256=sha256(old/'manifest.json'),
        original_log_sha256=sha256(old/'stdout.log'),required_clbs=35529,available_clbs=32560,
        change='Retry only gemm_layer capacity census at registered side200; preserve original failure and all logs; use resulting packed artifact for subsequent fixed-input comparisons',
        scope='Capacity feasibility only; no placement/routing QoR has been used',
        architecture=str(arch),architecture_sha256=sha256(arch),source_sha256=sha256(__file__)))
    name='pack_census_gemm_layer_s11_n200';d=BASE/'runs'/name
    binary=p['binaries']['paper_buildfix']['path'];blif=p['benchmarks']['gemm_layer']['path']
    receipt=common.run(name,[binary,arch,blif,'--pack','--device','controlled_200',
        '--seed',11,'--num_workers',1,'--clock_modeling','ideal','--route_chan_width',100,'--net_file',d/'packed.net'],
        inputs=[binary,arch,blif],environment={'OMP_NUM_THREADS':'1'},timeout=3600)
    result=dict(circuit='gemm_layer',status=receipt['status'],receipt=str(d/'manifest.json'))
    if (d/'packed.net').exists():
        result.update(packed_summary(d/'packed.net'));result['packed_sha256']=sha256(d/'packed.net')
    write_json(d/'census.json',result)
    assert result['status']=='completed','Second capacity attempt retained; diagnose before extending scope'
    selected={}
    for circuit in p['benchmarks']:
        directory=d if circuit=='gemm_layer' else BASE/'runs'/f'pack_census_{circuit}_s11'
        record=json.loads((directory/'census.json').read_text());assert record['status']=='completed'
        size=choose_size(record['block_counts'],p);slots=capacities(size)
        selected[circuit]=dict(size=size,census=str(directory/'census.json'),census_sha256=sha256(directory/'census.json'),
            packed=str(directory/'packed.net'),packed_sha256=sha256(directory/'packed.net'),
            semantic_sha256=record['semantic_sha256'],blocks=record['blocks'],block_counts=record['block_counts'],
            expected_slots=slots,resource_utilizations={k:n/slots[k] for k,n in record['block_counts'].items()})
    write_json(output,dict(utc=utc(),status='frozen',protocol_sha256=sha256(BASE/'benchmark_protocol.json'),
        amendment_sha256=sha256(amendment),circuits=selected,
        sizes=sorted({x['size'] for x in selected.values()}),attempted_census_runs=21,
        successful_census_runs=20,failed_census_runs=1,
        gate='Exact generated-grid capacities must equal these expectations before formal routing'))
    print('Capacity selection frozen', {c:x['size'] for c,x in selected.items()},flush=True)


if __name__=='__main__':main()
