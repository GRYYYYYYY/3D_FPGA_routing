#!/usr/bin/env python3
"""Check every completed adapter attempt against the ORIGINAL paper graph."""
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import re

import check_route as cr
from compare_lazagna_graphs import records
from lazagna_common import ROOT, sha256, utc, write_json
from run_vpr import parse_metrics
from run_h3d_delay_study import route_body_hash
from validate_lazagna_vtr9_pilot import placements

BASE = ROOT/'results/architecture_flow_20261027'


def read(path): return json.loads(Path(path).read_text())


def group(family):
    cr.graph_records = records
    source = BASE/'runs'/f'placement_smoke_ex5p_{family}_paper_3d'
    graph = source/'rr_graph.xml'
    runs = [source]
    for tag in ['adapter_pilot','adapter_pilot_v2']:
        protocol = read(BASE/(tag+'_protocol.json'))
        for job in protocol['jobs']:
            if job['family'] != family: continue
            d = BASE/'runs'/job['name']
            if (d/'manifest.json').exists() and read(d/'manifest.json')['status'] == 'completed':
                runs.append(d)
    wanted_nodes, wanted_edges = set(), set()
    for d in runs:
        for net in cr.read_trace(d/'routed.route').values():
            previous = None
            for node in net['trace']:
                wanted_nodes.add(node.inode)
                if previous is not None and previous.switch != -1:
                    wanted_edges.add((previous.inode,node.inode,previous.switch))
                previous = node
    evidence = cr.read_graph_evidence(graph,wanted_nodes,wanted_edges)
    result = []
    for d in runs:
        m = read(d/'manifest.json');log = (d/'stdout.log').read_text();metrics = parse_metrics(log)
        assert metrics['native_full_check_passed'] and metrics['routing_success_reported'],d
        audit = cr.audit(graph,d/'routed.route',graph_evidence=evidence)
        assert audit['passed'],audit['errors']
        if d != source:
            assert sha256(d/'packed.net') == sha256(source/'packed.net')
            assert placements(d/'fixed.place') == placements(source/'placed.place')
            for path,digest in m['inputs'].items():
                if Path(path) != d/'fixed.place': assert sha256(path) == digest,path
        out = BASE/'adapter_validation'/f'{d.name}.json'
        write_json(out,dict(utc=utc(),metrics=metrics,independent_audit=audit,
            reference='Original paper RRG before schema adaptation',
            resource_measurement='Independent check validates real RR capacities; its CHANZ-only aggregate is not used as CB/SB physical-via occupancy',
            route_body_sha256=route_body_hash(d/'routed.route'),
            scc_oracle=re.findall(r'H3D_SCC_VALIDATED .*',log),
            delay_oracle=re.findall(r'H3D_EDGE_DELAY_VALIDATED .*',log)))
        result.append(d.name)
    print('original-graph audit',family,len(result),'routes passed',flush=True)
    return result


def main():
    out = BASE/'adapter_validation';out.mkdir(exist_ok=False)
    with ProcessPoolExecutor(max_workers=3) as pool: audited=sum(pool.map(group,['sb','cb_o','hybrid_o']),[])
    comparisons = []
    for family in ['sb','cb_o','hybrid_o']:
        for left,right in [('off','a0'),('budget1','geometry')]:
            a=BASE/'runs'/f'adapter_pilot_v2_{family}_{left}'/'routed.route'
            b=BASE/'runs'/f'adapter_pilot_v2_{family}_{right}'/'routed.route'
            same=route_body_hash(a)==route_body_hash(b)
            comparisons.append(dict(family=family,left=left,right=right,identical=same))
            assert same,(family,left,right)
        for arm in ['a0','off','geometry','delay','budget1','critical','delay_critical']:
            old=f'adapter_pilot_{family}_{arm}';new=f'adapter_pilot_v2_{family}_{arm}'
            assert new in audited
            if old in audited:
                same=route_body_hash(BASE/'runs'/old/'routed.route')==route_body_hash(BASE/'runs'/new/'routed.route')
                comparisons.append(dict(family=family,left=old,right=new,identical=same))
                assert same,(old,new)
        log=(BASE/'runs'/f'adapter_pilot_v2_{family}_geometry'/'stdout.log').read_text()
        assert re.search(r'H3D_SCC_VALIDATED connections=[1-9]',log)
        log=(BASE/'runs'/f'adapter_pilot_v2_{family}_delay'/'stdout.log').read_text()
        assert re.search(r'H3D_EDGE_DELAY_VALIDATED .*returned=[1-9]',log)
    refs=read(BASE/'historical_refs.json')
    assert all(sha256(ROOT/p)==h for p,h in refs.items())
    write_json(out/'summary.json',dict(utc=utc(),passed=True,audited_runs=audited,comparisons=comparisons,
        prior_attempt=read(BASE/'adapter_pilot_v1_closure.json'),historical_reference_files_unchanged=len(refs),
        scope='Correctness and implementation scaling only; no benchmark or architecture-ranking conclusion'))


if __name__ == '__main__': main()
