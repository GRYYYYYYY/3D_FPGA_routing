#!/usr/bin/env python3
"""Analyze completed serial repeats, including failures and setup accounting."""
import argparse
from collections import Counter
from datetime import datetime
from itertools import product
from pathlib import Path
import re
from statistics import median

from analyze_flatland_evaluation import Evidence,failure_class
from flatland_benchmark import BASE,read
from flatland_statistics import geomean
from lazagna_common import ROOT,sha256,utc,write_json


def setup(evidence,name,circuit,family,flow,repeat,seed):
    d=BASE/'runs'/name;m=read(d/'manifest.json');evidence.bind(d/'manifest.json')
    evidence.thread_and_dependency_evidence(d,m)
    expected=dict(circuit=circuit,family=family,placement=flow,stage=f'serial_r{repeat}',
                  seed=seed,width=100,operation='placement')
    assert all(m['tags'].get(k)==v for k,v in expected.items())
    for f,info in m.get('outputs',{}).items():evidence.bind(d/f,info['sha256'])
    log=(d/'stdout.log').read_text(errors='replace')
    row=dict(run=name,status=m['status'],process_wall_seconds=m.get('wall_seconds'))
    for stage in ['Packing','Placement']:
        matches=re.findall(r'^# '+stage+r' took ([\d.]+) seconds',log,re.MULTILINE)
        row[stage.lower()+'_reported_seconds']=float(matches[-1]) if matches else None
    if m['status']!='completed':
        row['failure_class']=failure_class(m,log);return row
    check=read(d/'placement_check.json');evidence.bind(d/'placement_check.json');assert check['passed']
    if flow=='p1':
        td=d/'triton_evidence';part=read(td/'manifest.json');evidence.bind(td/'manifest.json')
        assert part['returncode']==0 and part['output_valid'] and part['partition_seed']==1
        for f,k in [('triton_hypergraph.hgr','input_sha256'),('triton_hypergraph.hgr.part.2','output_sha256'),
                    ('run_triton_part.tcl','tcl_sha256')]:evidence.bind(td/f,part[k])
        row.update(partition_wall_seconds=part['wall_seconds'],partition_sizes=part['part_sizes'])
    else:row['partition_wall_seconds']=None
    return row


def comparisons(cases,routers=('A0','B2','R1off')):
    result={}
    for base in routers:
        rows=[]
        for case in cases:
            paired=[r for r in case['repeats'] if r['status']=='completed'
                    and all(r['routes'][a]['status']=='legal' for a in ['R1',base])]
            row={k:case[k] for k in ['circuit','family','flow','split']}
            row.update(registered_repeats=3,paired_legal_repeats=len(paired))
            if len(paired)==3:
                for label,key in [('router','router_seconds'),('route_process','process_wall_seconds')]:
                    def timing(r,arm):
                        run=r['routes'][arm]
                        value=run['metrics'][key] if label=='router' else run[key]
                        assert value>0
                        return value
                    a=median(timing(r,'R1') for r in paired);b=median(timing(r,base) for r in paired)
                    row[label]=dict(r1_median_seconds=a,baseline_median_seconds=b,ratio=a/b,
                        overhead_percent=100*(a/b-1),speedup=b/a,
                        r1_range_seconds=[min(timing(r,'R1') for r in paired),max(timing(r,'R1') for r in paired)],
                        baseline_range_seconds=[min(timing(r,base) for r in paired),max(timing(r,base) for r in paired)])
            rows.append(row)
        groups={}
        for split in ['training','heldout']:
            for flow in ['p0','p1']:
                subset=[r for r in rows if r['split']==split and r['flow']==flow]
                complete=[r for r in subset if r['paired_legal_repeats']==3]
                groups[split+'_'+flow]=dict(registered_architecture_cases=len(subset),
                    complete_architecture_cases=len(complete),
                    router_geomean_ratio=geomean(r['router']['ratio'] for r in complete),
                    route_process_geomean_ratio=geomean(r['route_process']['ratio'] for r in complete))
        result['R1_over_'+base]=dict(per_case=rows,by_split_flow=groups)
    return result


def check_overlap(evidence,names):
    intervals=[]
    for path in (BASE/'runs').glob('*/manifest.json'):
        m=read(path)
        if m.get('start_utc') and m.get('finish_utc'):
            intervals.append((datetime.fromisoformat(m['start_utc']),datetime.fromisoformat(m['finish_utc']),m['name'],path))
    by_name={r[2]:r for r in intervals}
    for name in names:
        start,end,_,path=by_name[name];evidence.bind(path)
        overlaps=[r[2] for r in intervals if r[2]!=name and max(start,r[0])<min(end,r[1])]
        assert not overlaps,(name,'Study-owned process interval overlap',overlaps)
    return dict(passed=True,checked_serial_processes=len(names),
        scope='No overlapping registered study process intervals; this does not establish exclusive use of the shared host.')


def main(output):
    output=Path(output);assert not output.exists()
    evidence=Evidence();protocol=read(BASE/'benchmark_protocol.json');registration=read(BASE/'serial_protocol.json')
    assert registration['timing_method']=='seccomp_guard_no_ptrace'
    evidence.bind(BASE/'benchmark_protocol.json',registration['protocol_sha256'])
    evidence.bind(BASE/'selected_configs.json',registration['selection_sha256'])
    evidence.bind(BASE/'serial_protocol.json');evidence.bind(BASE/'serial_summary.json')
    evidence.bind(BASE/'serial_input_integrity.json');assert read(BASE/'serial_input_integrity.json')['passed']
    selection=read(BASE/'selected_configs.json');summary=read(BASE/'serial_summary.json')
    expected={(c,f,flow,r) for c,f,flow,r in product(protocol['runtime']['circuits'],
        protocol['runtime']['architectures'],['p0','p1'],range(1,4))}
    actual={(r['circuit'],r['family'],r['flow'],r['repeat']) for r in summary['results']}
    assert actual==expected and len(actual)==len(summary['results'])==summary['expected_repetitions']==36
    groups={};all_names=set();positions={}
    for row in summary['results']:
        c,f,flow,repeat=(row[k] for k in ['circuit','family','flow','repeat']);seed=protocol['runtime']['seeds'][c]
        key=(c,f,flow);all_names.add(row['placement'])
        place=setup(evidence,row['placement'],c,f,flow,repeat,seed)
        observed=dict(repeat=repeat,status=row['status'],setup=place,routes={})
        if row['status']=='completed':
            assert place['status']=='completed'
            casepath=BASE/'serial_cases'/f'{c}_{f}_{flow}_r{repeat}'/'result.json'
            evidence.bind(casepath);assert read(casepath)==row
            coords=evidence.coordinates(BASE/'runs'/row['placement']/'placed.place')
            if key in positions:assert positions[key]==coords
            else:positions[key]=coords
            observed['host_load_before']=row['host_load_before'];observed['router_order']=row['router_order']
            chosen=selection['selections'][f]['R1']
            for arm,name in row['runs'].items():
                all_names.add(name)
                spec=dict(router=arm,variant=chosen['variant'] if arm=='R1' else None,
                    config=chosen['config'] if arm=='R1' else None)
                run=evidence.run(name,dict(phase=f'serial_r{repeat}',circuit=c,family=f,seed=seed,width=100),flow,spec)
                observed['routes'][arm]=run
                if run['status']=='legal':
                    run['setup_plus_route_process_seconds']=place['process_wall_seconds']+run['process_wall_seconds']
        else:assert row['status']=='placement_failed' and place['status']!='completed'
        group=groups.setdefault(key,dict(circuit=c,family=f,flow=flow,
            split='training' if c in protocol['training'] else 'heldout',repeats=[]))
        group['repeats'].append(observed)
    isolation=check_overlap(evidence,all_names);cases=list(groups.values())
    result=dict(utc=utc(),timing_method='seccomp_guard_no_ptrace',expected_repetitions=36,observed_repetitions=len(summary['results']),
        status_counts=dict(Counter(r['status'] for r in summary['results'])),
        comparisons=comparisons(cases),cases=cases,isolation=isolation,
        limitations=[
            'Inference is limited to the registered spmv and robot_rl subset. Training and held-out results stay separate.',
            'Use medians over all three successful repeats before forming ratios; incomplete repeats remain in coverage counts.',
            'P0 reuses census packing; P1 repacks to populate criticalities. Setup sums are flow-specific observed costs, not equal-work cross-flow end-to-end speedups.',
            'Serial runs exclude overlapping study jobs, not unrelated activity on the shared host.',
            'R1/A0 compares a separately built serial official-source derivative; R1/R1off isolates algorithm overhead within the current build.',
            'Inherited seccomp filter denies clone3 and kills CLONE_THREAD callers; the filter and supervisor have overhead, and workload equivalence is limited to validated samples.'],
        source_sha256=sha256(__file__),evidence_source_sha256=sha256(Path(__file__).parent/'analyze_flatland_evaluation.py'))
    output.mkdir(parents=True,exist_ok=False);write_json(output/'summary.json',result)
    write_json(output/'input_bindings.json',dict(utc=utc(),sha256=evidence.bindings))
    print('Serial aggregation complete:',len(summary['results']),'registered repetitions',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=BASE/'serial_analysis')
    main(p.parse_args().output)
