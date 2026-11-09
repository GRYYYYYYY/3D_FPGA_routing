#!/usr/bin/env python3
"""Freeze failure-aware selections using registered training cases only."""
import math
from pathlib import Path

from flatland_benchmark import BASE,read
from lazagna_common import ROOT,sha256,utc,write_json


def geomean(values):
    if not values or any(not math.isfinite(x) or x<=0 for x in values):return None
    return math.exp(sum(map(math.log,values))/len(values))


def choose(candidates):
    """Input order breaks final ties; every candidate maps case to legal metrics."""
    best_count=max(len(c['cases']) for c in candidates)
    tied=[c for c in candidates if len(c['cases'])==best_count]
    common=set.intersection(*(set(c['cases']) for c in tied))
    common=sorted(common)
    scored=[]
    for order,candidate in enumerate(candidates):
        cpd=geomean([candidate['cases'][k]['critical_path_ns'] for k in common]) if len(candidate['cases'])==best_count else None
        timing=geomean([candidate['cases'][k].get('router_seconds',0) for k in common]) if len(candidate['cases'])==best_count else None
        score=(-len(candidate['cases']),cpd if cpd is not None else math.inf,
               timing if timing is not None else math.inf,order)
        scored.append((score,candidate))
    selected=min(scored,key=lambda pair:pair[0])[1]
    return dict(selected=selected['id'],maximum_legal_count=best_count,complete_common_cases=common,
        ranking=[dict(id=c['id'],legal_count=len(c['cases']),
            comparison_geomean_cpd=score[1] if math.isfinite(score[1]) else None,
            comparison_geomean_router_seconds=score[2] if math.isfinite(score[2]) else None)
            for score,c in sorted(scored,key=lambda pair:pair[0])])


def main():
    output=BASE/'selected_configs.json'
    if output.exists():raise FileExistsError(output)
    protocol=read(BASE/'benchmark_protocol.json');variants=list(protocol['tuning']['variants'])
    selections={};bindings={};recorded_routes=0
    for family in protocol['architectures']:
        records={v:{i:{} for i in range(8)} for v in variants}
        for circuit in protocol['training']:
            d=BASE/'training_cases'/f'{circuit}_{family}'
            result=read(d/'result.json')
            assert result['status']=='completed',f'Unresolved training infrastructure/placement case: {d}'
            audit=read(d/'audit_summary.json');assert audit['passed'] and audit['registered_route_count']==33
            recorded_routes+=audit['registered_route_count']
            bindings[str(d/'audit_summary.json')]=sha256(d/'audit_summary.json')
            for row in audit['legal']:
                manifest=BASE/'runs'/row['name']/'manifest.json';m=read(manifest);tags=m['tags']
                assert tags['circuit']==circuit and tags['family']==family and tags['stage']=='training' and tags['seed']==11
                if tags['router']=='R1':records[tags['variant']][tags['config']][circuit]=row['metrics']
                bindings[str(manifest)]=sha256(manifest)
        per_variant={};overall=[]
        for variant in variants:
            chosen=choose([dict(id=i,cases=records[variant][i]) for i in range(8)])
            per_variant[variant]=chosen
            overall.append(dict(id=variant,cases=records[variant][chosen['selected']]))
        final=choose(overall);variant=final['selected'];config=per_variant[variant]['selected']
        selections[family]=dict(per_variant=per_variant,overall=final,
            R1=dict(variant=variant,config=config,environment=protocol['tuning']['variants'][variant][config]['environment']))
    assert recorded_routes==594
    write_json(output,dict(utc=utc(),status='frozen_before_heldout',protocol_sha256=sha256(BASE/'benchmark_protocol.json'),
        training_jobs_sha256=sha256(BASE/'training_jobs.json'),selection_source_sha256=sha256(__file__),
        selections=selections,evidence_sha256=bindings,registered_R1_routes=576,registered_A0_routes=18,
        interpretation='Training selection only. Held-out outcomes must not change these configs or the preregistered reporting denominator.'))
    print('Frozen per-architecture configs', {f:x['R1'] for f,x in selections.items()})


if __name__=='__main__':main()
