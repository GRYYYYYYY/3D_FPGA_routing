#!/usr/bin/env python3
"""Analyze matched-width results without treating failed roles as successes."""
from collections import Counter,defaultdict
import math
from pathlib import Path

from analyze_flatland_evaluation import Evidence
from flatland_benchmark import BASE,read
from lazagna_common import sha256,utc,write_json
from run_paired_width_diagnostic import role_specs


def interaction(a100,r100,a300,r300):
    values=[a100,r100,a300,r300]
    if any(x is None or not math.isfinite(x) or x<=0 for x in values):return None
    old=r100/a100;new=r300/a300
    return dict(w100_r1_over_a0=old,w300_r1_over_a0=new,interaction_ratio=new/old,
        w100_improvement_percent=100*(1-old),w300_improvement_percent=100*(1-new))


def main():
    target=BASE/'paired_width_analysis';assert not target.exists()
    e=Evidence();plan=read(BASE/'paired_width_jobs.json');protocol=read(BASE/'paired_width_diagnostic_protocol.json')
    summary=read(BASE/'paired_width_summary.json');selection=read(BASE/'selected_configs.json')
    e.bind(BASE/'paired_width_jobs.json');e.bind(BASE/'paired_width_summary.json')
    e.bind(BASE/'paired_width_diagnostic_protocol.json',plan['protocol_sha256'])
    e.bind(BASE/'selected_configs.json',plan['selection_sha256'])
    e.bind(Path(__file__).parent/'run_paired_width_diagnostic.py',plan['source_sha256'])
    for path,digest in plan['primary_sha256'].items():e.bind(path,digest)
    assert read(BASE/'paired_width_input_integrity.json')['passed']
    e.bind(BASE/'paired_width_input_integrity.json')
    assert summary['registered_cases']==24 and summary['registered_roles']==144
    assert len(plan['jobs'])==len(summary['results'])==24 and not summary['unstarted_jobs']
    assert len(protocol['cases'])==12 and len(protocol['roles'])==144
    role_key=lambda r:tuple(r[k] for k in ('circuit','seed','size','family','flow','width','role'))
    expected_roles={role_key(r) for r in protocol['roles']}
    expanded_roles={role_key(dict(**job['case'],flow=job['flow'],width=width,role=role))
                    for job in plan['jobs'] for width in (100,300)
                    for role in ('A0','geometry_c0','selected_R1')}
    assert len(expected_roles)==len(expanded_roles)==144 and expected_roles==expanded_roles
    rows=[];interactions=[];seen=set()
    for job,result in zip(plan['jobs'],summary['results']):
        case=job['case'];flow=job['flow'];assert result['case']==case and result['flow']==flow
        key=(case['circuit'],case['family'],case['seed'],flow);assert key not in seen;seen.add(key)
        for index,width in enumerate((100,300)):
            model_path=BASE/'benchmark_models'/f"n{case['size']}_w{width}"/'manifest.json'
            e.bind(model_path,case['manifest_sha256'][index]);model=read(model_path)
            fixture=model['fixtures'][case['family']];conv=fixture['conversion']
            e.bind(conv['architecture'],case['native_architecture_sha256'])
            e.bind(fixture['architecture'],case['source_architecture_sha256'])
            e.bind(conv['graph'],case['native_graph_sha256'][index])
            e.bind(fixture['original_graph'],case['original_graph_sha256'][index])
        directory=BASE/'paired_width_cases'/f"{case['circuit']}_s{case['seed']}_{case['family']}_{flow}"
        assert read(directory/'result.json')==result;e.bind(directory/'result.json')
        registration=read(directory/'registration.json');e.bind(directory/'registration.json')
        assert registration['case']==case and registration['flow']==flow
        assert registration['registration_sha256']==sha256(BASE/'paired_width_jobs.json')
        place=BASE/'runs'/result['placement'];pm=read(place/'manifest.json');e.bind(place/'manifest.json')
        e.thread_and_dependency_evidence(place,pm)
        expected={'circuit':case['circuit'],'family':case['family'],'seed':case['seed'],
                  'width':100,'stage':'paired_width','placement':flow,'operation':'placement'}
        assert all(pm['tags'].get(k)==v for k,v in expected.items())
        if result['status']=='placement_failed':
            assert pm['status']!='completed' and result['unattempted_roles']==6
            for w in (100,300):
                for role in role_specs(selection,case['family']):
                    rows.append(dict(circuit=case['circuit'],family=case['family'],seed=case['seed'],
                        flow=flow,width=w,role=role,status='placement_failed',cpd_ns=None,run=None))
            for role in ('geometry_c0','selected_R1'):
                interactions.append(dict(circuit=case['circuit'],family=case['family'],seed=case['seed'],
                    flow=flow,role=role,status='incomplete',effect=None))
            continue
        assert result['status']=='completed' and pm['status']=='completed'
        check=read(place/'placement_check.json');e.bind(place/'placement_check.json');assert check['passed']
        for filename in ('packed.net','placed.place'):e.bind(place/filename,pm['outputs'][filename]['sha256'])
        effects={}
        for width in (100,300):
            cell=result['widths'][str(width)];audit=read(directory/f'audit_w{width}.json')
            e.bind(directory/f'audit_w{width}.json');assert audit['passed']
            assert cell['registered_roles']==3 and set(cell['roles'])=={'A0','geometry_c0','selected_R1'}
            assert cell['unique_runs']==len(set(cell['roles'].values()))
            assert cell['legal_runs']==audit['legal_count'] and cell['failed_runs']==audit['failed_count']
            assert cell['unique_runs']==audit['legal_count']+audit['failed_count']
            assert set(cell['roles'].values())=={x['name'] for g in ('legal','failed') for x in audit[g]}
            legal_names={x['name'] for x in audit['legal']}
            for role,spec in role_specs(selection,case['family']).items():
                name=cell['roles'][role];route_dir=BASE/'runs'/name
                pair=read(route_dir/'pair_check.json');e.bind(route_dir/'pair_check.json')
                assert pair['passed'] and Path(pair['source'])==place and pair['source_width']==100 and pair['target_width']==width
                router,variant,config=spec
                observed=e.run(name,dict(phase='paired_width',circuit=case['circuit'],family=case['family'],
                    seed=case['seed'],width=width),flow,dict(router=router,variant=variant,config=config))
                assert (observed['status']=='legal')==(name in legal_names)
                cp=observed['metrics'].get('critical_path_ns') if observed['status']=='legal' else None
                effects[width,role]=cp
                rows.append(dict(circuit=case['circuit'],family=case['family'],seed=case['seed'],
                    flow=flow,width=width,role=role,status=observed['status'],cpd_ns=cp,run=name,
                    failure_class=observed.get('failure_class')))
        for role in ('geometry_c0','selected_R1'):
            effect=interaction(effects[100,'A0'],effects[100,role],effects[300,'A0'],effects[300,role])
            interactions.append(dict(circuit=case['circuit'],family=case['family'],seed=case['seed'],
                flow=flow,role=role,status='complete' if effect else 'incomplete',effect=effect))
    assert len(rows)==144 and len(interactions)==48
    groups=defaultdict(list)
    training=set(read(BASE/'benchmark_protocol.json')['training'])
    for row in interactions:
        split='training' if row['circuit'] in training else 'heldout'
        groups[split,row['family'],row['flow'],row['role']].append(row)
    aggregated=[]
    for (split,family,flow,role),items in sorted(groups.items()):
        complete=[x['effect']['interaction_ratio'] for x in items if x['effect']]
        ratio=math.exp(sum(map(math.log,complete))/len(complete)) if complete else None
        aggregated.append(dict(split=split,family=family,flow=flow,role=role,registered_cases=len(items),
            complete_cases=len(complete),geomean_interaction_ratio=ratio))
    target.mkdir(exist_ok=False)
    write_json(target/'summary.json',dict(utc=utc(),status='complete',registered_roles=144,
        role_status_counts=dict(Counter(x['status'] for x in rows)),rows=rows,
        interactions=interactions,aggregated=aggregated,
        interpretation='Interaction is (R1/A0 at W300)/(R1/A0 at W100); below one means a stronger relative R1 effect at W300. This selected one-seed, four-circuit diagnostic changes resource graph as well as congestion and cannot establish the cause of historical results.',
        source_sha256=sha256(__file__)))
    write_json(target/'input_bindings.json',dict(utc=utc(),sha256=e.bindings))
    print('paired width analysis complete',len(rows),'registered role observations',flush=True)


if __name__=='__main__':main()
