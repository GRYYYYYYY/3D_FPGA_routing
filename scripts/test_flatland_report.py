#!/usr/bin/env python3
"""Exercise report tables on explicitly synthetic analysis fixtures."""
import copy
import argparse
from itertools import product
from pathlib import Path
import shutil

from lxml import etree

import test_flatland_analysis as fixture
from analyze_flatland_serial import comparisons
from flatland_benchmark import BASE,read
from lazagna_common import ROOT,sha256,utc,write_json
from render_flatland_report import document


def main(out):
    out=Path(out);out.mkdir(exist_ok=False)
    working=out/'fixtures';working.mkdir()
    shutil.copy2(BASE/'benchmark_protocol.json',working/'benchmark_protocol.json')
    fixture.BASE=working;captured=[];original=fixture.summarize
    def capture(*args):
        result=original(*args);captured.append(copy.deepcopy(result));return result
    fixture.summarize=capture;fixture.main()
    q=captured[0];q.update(planned_cases=180,planned_roles=1206,unique_attempted_route_runs=1000,
        role_status_counts=dict(legal=1206),unique_run_status_counts=dict(legal=1000))
    protocol=read(BASE/'benchmark_protocol.json');cases=[]
    for circuit,family,flow in product(protocol['runtime']['circuits'],protocol['architectures'],['p0','p1']):
        case=dict(circuit=circuit,family=family,flow=flow,split='training' if circuit in protocol['training'] else 'heldout',repeats=[])
        for repeat in range(1,4):
            setup=dict(status='completed',process_wall_seconds=10,packing_reported_seconds=2 if flow=='p1' else None,
                partition_wall_seconds=4 if flow=='p1' else None,placement_reported_seconds=3)
            routes={a:dict(status='legal',metrics=dict(critical_path_ns=10,router_seconds=2),process_wall_seconds=3)
                    for a in ['A0','B2','R1off','R1']}
            case['repeats'].append(dict(status='completed',repeat=repeat,setup=setup,routes=routes))
        cases.append(case)
    serial=dict(cases=cases,comparisons=comparisons(cases))
    selection=dict(selections={f:dict(R1=dict(variant='geometry',config=0),
        per_variant={v:dict(selected=0) for v in protocol['tuning']['variants']}) for f in protocol['architectures']})
    balance=dict(comparisons=[dict(split='heldout',width=100,family='sb',contrast='A0 relative3/literal',registered_pairs=2,legal_pairs=1,geomean_ratio=.875)])
    training=dict(registered_attempts=594,legal_attempts=592,groups=[
        dict(family='sb',router='R1',variant='delay',config=0,registered=6,legal=4,
             failure_counts=dict(allocation_failure_under_registered_limit=1,process_timeout=1))])
    html=document(dict(evaluation=q,serial=serial,protocol=protocol,selection=selection,observations=dict(rows=[]),balance=balance,training=training),[])
    html=html.replace('<body>','<body><p style="background:#ffcece;padding:30px;font-size:25px">SYNTHETIC STRUCTURE TEST — NOT RESEARCH RESULTS. Image links are not evaluated in this fixture.</p>',1)
    (out/'synthetic_report.html').write_text(html)
    tree=etree.HTML(html)
    assert len(tree.findall('.//table'))==20
    training_table=tree.xpath('//table[.//th[text()="合法/登记电路"]]')
    assert len(training_table)==1
    assert training_table[0].xpath('count(.//td[text()="4/6"])')==1
    assert 'allocation_failure_under_registered_limit: 1' in html and 'process_timeout: 1' in html
    assert '分区参数语义与独立敏感性对照' in html and '0.875000' in html
    assert len(tree.findall('.//img'))==5
    headings={''.join(node.itertext()) for node in tree.findall('.//h2')}
    assert {'实验范围与三套基线','固定布局下的布线收益','布局贡献、组合收益与架构排序',
        '超参数探索与消融','W300 固定参数敏感性','串行耗时与代价','失败与物理模型边界','可复核材料'}<=headings
    assert tree.xpath('count(//tr[td[text()="0.727273"]])')>0  # R1/B2 = 0.8/1.1
    routing_table=tree.xpath('//table[.//th[contains(text(),"CPD 改善：3D")]]')
    assert len(routing_table)==1
    assert routing_table[0].xpath('count(.//td[starts-with(text(),"+20.00% (")])')==6
    assert 'SYNTHETIC STRUCTURE TEST' in html
    write_json(out/'validation.json',dict(utc=utc(),passed=True,synthetic=True,
        report_source_sha256=sha256(ROOT/'scripts/render_flatland_report.py'),test_source_sha256=sha256(__file__),
        checks=['all completed analysis sections render','known paired ratios survive formatting','HTML tables and figure references present'],
        scope='Structure and formatting only; not a scientific result or a validation of actual formal experiment completeness.'))
    print('Synthetic report structure checks passed')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=BASE/'report_render_validation_v4')
    main(p.parse_args().output)
