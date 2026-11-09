#!/usr/bin/env python3
"""Validate native-placement pairs and modern LaZagna on original physical graphs."""
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

import check_route as cr
from compare_lazagna_graphs import records
from lazagna_common import ROOT,sha256,utc,write_json
from run_vpr import parse_metrics
from validate_lazagna_vtr9_pilot import placements

BASE=ROOT/'results/architecture_flow_20261027'


def run(family):
    cr.graph_records=records
    source=BASE/'runs'/f'placement_smoke_ex5p_{family}_paper_3d'
    graph=source/'rr_graph.xml'
    native_place=BASE/'runs'/f'crossflow_smoke_{family}_native_place_a0'/'placed.place'
    names=[f'crossflow_smoke_{family}_native_place_{a}' for a in ['a0','delay']]
    names.append(f'b2_shared_graph_smoke_{family}')
    metrics={}
    for name in names:
        d=BASE/'runs'/name;m=json.loads((d/'manifest.json').read_text())
        assert m['status']=='completed',name
        stats=parse_metrics((d/'stdout.log').read_text())
        assert stats['native_full_check_passed'] and stats['routing_success_reported'],name
        assert sha256(d/'packed.net')==sha256(source/'packed.net'),name
        reference=source/'placed.place' if name.startswith('b2_') else native_place
        observed=d/('fixed.place' if name.startswith('b2_') else 'placed.place')
        assert placements(observed)==placements(reference)
        audit=cr.audit(graph,d/'routed.route');assert audit['passed'],audit['errors']
        write_json(BASE/'crossflow_validation'/f'{name}.json',dict(utc=utc(),metrics=stats,audit=audit,
            statement='Audited against original paper graph; private placement coordinates and packed bytes match the intended factor row'))
        metrics[name]=stats
    for arm in ['a0','delay']:
        name=f'adapter_pilot_v2_{family}_{arm}'
        result=json.loads((BASE/'adapter_validation'/f'{name}.json').read_text())
        assert result['independent_audit']['passed'];metrics[name]=result['metrics']
    old,new=placements(source/'placed.place'),placements(native_place)
    assert set(old)==set(new)
    return dict(family=family,passed=True,metrics=metrics,blocks=len(old),
        placement_coordinates_changed=sum(old[k]!=new[k] for k in old),
        interpretation='One ex5p smoke input; compatibility/controls only, no benchmark advantage or architecture-ranking conclusion')


if __name__=='__main__':
    (BASE/'crossflow_validation').mkdir(exist_ok=False)
    with ProcessPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,['sb','cb_o','hybrid_o']))
    write_json(BASE/'crossflow_validation/summary.json',dict(utc=utc(),passed=True,results=results))
    print('Nine new crossflow/B2 routes audited; all three 2x2 smoke matrices validated')
