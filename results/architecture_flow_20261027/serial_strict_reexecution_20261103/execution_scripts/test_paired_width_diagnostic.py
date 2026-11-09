#!/usr/bin/env python3
"""Synthetic success/failure denominator checks for matched-width analysis."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import analyze_paired_width_diagnostic as analysis
import run_paired_width_diagnostic as runner
from lazagna_common import sha256


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value))


class FakeEvidence:
    """Exercise aggregation only; this fixture does not validate real hashes."""
    def __init__(self):self.bindings={}
    def bind(self,path,expected=None):return expected
    def thread_and_dependency_evidence(self,*args):pass
    def run(self,name,job,flow,spec):
        value=10 if spec['router']=='A0' or job['width']==300 else 9
        return dict(status='legal',metrics=dict(critical_path_ns=value))


def fixture(root,original,protocol,benchmark,success):
    analysis.BASE=root
    (root/'benchmark_models').symlink_to((original/'benchmark_models').resolve(),target_is_directory=True)
    write(root/'benchmark_protocol.json',benchmark)
    write(root/'paired_width_diagnostic_protocol.json',protocol)
    selection={'selections':{f:{'R1':{'variant':'geometry','config':0}} for f in benchmark['architectures']}}
    write(root/'selected_configs.json',selection)
    jobs=[{'case':c,'flow':f} for c in protocol['cases'] for f in ('p0','p1')]
    runner=Path(analysis.__file__).parent/'run_paired_width_diagnostic.py'
    plan={'jobs':jobs,'protocol_sha256':sha256(root/'paired_width_diagnostic_protocol.json'),
          'selection_sha256':sha256(root/'selected_configs.json'),'source_sha256':sha256(runner),'primary_sha256':{}}
    write(root/'paired_width_jobs.json',plan);results=[]
    for job in jobs:
        case=job['case'];flow=job['flow']
        name=f"{case['circuit']}_s{case['seed']}_{case['family']}_{flow}"
        place=root/'runs'/('place_'+name);place.mkdir(parents=True)
        tags=dict(circuit=case['circuit'],family=case['family'],seed=case['seed'],width=100,
                  stage='paired_width',placement=flow,operation='placement')
        metadata=dict(status='completed' if success else 'failed',tags=tags,outputs={})
        if success:
            for filename in ('packed.net','placed.place'):
                (place/filename).write_text(filename)
                metadata['outputs'][filename]={'sha256':sha256(place/filename)}
            write(place/'placement_check.json',{'passed':True})
        write(place/'manifest.json',metadata)
        case_dir=root/'paired_width_cases'/name;widths={}
        if success:
            for width in (100,300):
                names=[f'{name}_{width}_a0',f'{name}_{width}_r1']
                roles={'A0':names[0],'geometry_c0':names[1],'selected_R1':names[1]}
                for run in names:write(root/'runs'/run/'pair_check.json',dict(passed=True,source=str(place),source_width=100,target_width=width))
                write(case_dir/f'audit_w{width}.json',dict(passed=True,legal_count=2,failed_count=0,
                      legal=[{'name':n} for n in names],failed=[]))
                widths[str(width)]=dict(roles=roles,registered_roles=3,unique_runs=2,legal_runs=2,failed_runs=0)
        result=dict(case=case,flow=flow,status='completed' if success else 'placement_failed',
                    placement=place.name,widths=widths)
        if not success:result['unattempted_roles']=6
        results.append(result)
        write(case_dir/'registration.json',dict(case=case,flow=flow,registration_sha256=sha256(root/'paired_width_jobs.json')))
        write(case_dir/'result.json',result)
    write(root/'paired_width_summary.json',dict(registered_cases=24,registered_roles=144,results=results,unstarted_jobs=[]))
    write(root/'paired_width_input_integrity.json',{'passed':True})
    with patch.object(analysis,'Evidence',FakeEvidence):analysis.main()
    result=json.loads((root/'paired_width_analysis/summary.json').read_text())
    assert len(result['rows'])==144 and len(result['interactions'])==48
    assert result['role_status_counts']==({'legal':144} if success else {'placement_failed':144})
    assert all(x['registered_cases']==2 and x['complete_cases']==(2 if success else 0) for x in result['aggregated'])
    if success:assert all(abs(x['effect']['interaction_ratio']-10/9)<1e-12 for x in result['interactions'])
    else:assert all(x['status']=='incomplete' and x['effect'] is None for x in result['interactions'])


def main():
    original=analysis.BASE
    protocol=json.loads((original/'paired_width_diagnostic_protocol.json').read_text())
    benchmark=json.loads((original/'benchmark_protocol.json').read_text())
    assert analysis.interaction(10,None,10,9) is None
    with TemporaryDirectory(prefix='paired_width_analysis_test_') as tmp:
        for success in (False,True):
            root=Path(tmp)/str(success);root.mkdir();fixture(root,original,protocol,benchmark,success)
        runner.BASE=Path(tmp)/'runner';runner.BASE.mkdir();case=protocol['cases'][0];calls=[]
        def fake_route(ctx,flow,source,*spec):
            calls.append((ctx['width'],str(source),spec))
            return {'name':str(ctx['width'])+str(spec),'status':'completed'}
        def fake_audit(ctx,runs,out):return {'legal_count':len(runs),'failed_count':0}
        selection={'selections':{case['family']:{'R1':{'variant':'geometry','config':0}}}}
        with patch.object(runner,'contexts',return_value={100:{'width':100},300:{'width':300}}),\
             patch.object(runner.study,'placement',return_value={'name':'fixed_placement','status':'completed'}) as place,\
             patch.object(runner,'route',side_effect=fake_route),patch.object(runner.study,'audit_batch',side_effect=fake_audit):
            result=runner.run_case(case,'p0',selection,'fixture')
            assert result['status']=='completed' and len(calls)==4 and len({x[1] for x in calls})==1
            assert [x[0] for x in calls]==[100,100,300,300] and place.call_args.args[0]['width']==100
            assert result['widths']['100']['roles']['geometry_c0']==result['widths']['100']['roles']['selected_R1']
        with patch.object(runner,'contexts',return_value={100:{},300:{}}),\
             patch.object(runner.study,'placement',return_value={'name':'failed','status':'failed'}),\
             patch.object(runner,'route') as route:
            failed=runner.run_case(case,'p1',selection,'fixture')
            assert failed['status']=='placement_failed' and failed['unattempted_roles']==6 and not route.called
    print('matched-width aggregation: 144 roles and 48 interactions preserved in success/failure fixtures')


if __name__=='__main__':main()
