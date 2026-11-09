#!/usr/bin/env python3
"""Aggregate only completed, independently audited registered evaluation roles."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re

from flatland_benchmark import BASE,read
from flatland_statistics import architecture_rankings,complete_circuits,dual,factorial_interaction,paired
from lazagna_common import ROOT,sha256,utc,write_json
from run_vpr import parse_metrics
from validate_lazagna_vtr9_pilot import placements


def guide_diagnostics(log):
    result={}
    for prefix,key in [('H3D_SCORE','guide_coverage'),('H3D_DELAY','delay_search'),('H3D_PLAN','planner'),('H3D_TREE','guide_tree')]:
        lines=re.findall(r'^'+prefix+r' (.*)$',log,re.MULTILINE)
        if lines:
            result[key]={k:float(v) if '.' in v else int(v)
                for k,v in re.findall(r'(\w+)=(\d+(?:\.\d+)?)',lines[-1])}
    return result


class Evidence:
    def __init__(self):
        self.hashes={};self.run_cache={};self.placements={};self.bindings={}

    def bind(self,path,expected=None):
        path=Path(path).resolve();key=str(path)
        identity=(path.stat().st_size,path.stat().st_mtime_ns,path.stat().st_ctime_ns)
        if key in self.hashes:
            old,digest=self.hashes[key];assert old==identity,f'Analysis input changed: {path}'
        else:
            digest=sha256(path)
            assert identity==(path.stat().st_size,path.stat().st_mtime_ns,path.stat().st_ctime_ns)
            self.hashes[key]=(identity,digest)
        if expected is not None:assert digest==expected,f'Hash mismatch: {path}'
        self.bindings[key]=digest
        return digest

    def coordinates(self,path):
        path=str(Path(path).resolve())
        self.bind(path)
        if path not in self.placements:self.placements[path]=placements(path)
        return self.placements[path]

    def run(self,name,job,flow,spec):
        d=BASE/'runs'/name;m=read(d/'manifest.json');self.bind(d/'manifest.json')
        expected={k:job[k] for k in ['circuit','family','seed','width']}
        expected.update(stage=job['phase'],placement=flow,operation='route',**spec)
        assert all(m['tags'].get(k)==v for k,v in expected.items()),(name,expected,m['tags'])
        protocol=read(BASE/'benchmark_protocol.json')
        binary=protocol['binaries']['R1' if spec['router']=='R1off' else spec['router']]
        assert m['command'][0]==binary['path']
        assert m['shared_inputs'][binary['path']]['sha256']==binary['sha256']
        self.bind(binary['path'],binary['sha256'])
        actual_env={k:v for k,v in m['environment'].items() if k.startswith('VPR_H3D_')}
        if spec['router']=='R1':
            expected_env=protocol['tuning']['variants'][spec['variant']][spec['config']]['environment']
        elif spec['router']=='R1off':
            expected_env=dict(VPR_H3D_MODE='off',VPR_H3D_REACHABILITY='scc',VPR_H3D_GRAPH_ENCODING='edge',VPR_H3D_STATS='1')
        else:expected_env={}
        assert actual_env==expected_env,(name,'algorithm environment mismatch')
        if name in self.run_cache:return self.run_cache[name]
        log=(d/'stdout.log').read_text(errors='replace')
        if 'stdout.log' in m.get('outputs',{}):self.bind(d/'stdout.log',m['outputs']['stdout.log']['sha256'])
        metrics=parse_metrics(log);assert metrics==m.get('metrics',metrics)
        result=dict(run=name,status=m['status'],metrics=metrics,physical_metrics={},process_wall_seconds=m.get('wall_seconds'),
            returncode=m.get('returncode'),manifest=str(d/'manifest.json'))
        if m['status']=='completed' and metrics['native_full_check_passed'] and metrics['routing_success_reported']:
            command=m['command'];assert command[command.index('--check_route')+1]=='full'
            audit=read(d/'independent_audit.json');self.bind(d/'independent_audit.json')
            assert audit['audit']['passed'] and audit['audit']['scope']=='directed_edges_tree_routed_resource_capacity'
            self.bind(d/'routed.route',audit['audit']['inputs']['route_sha256'])
            assert m['outputs']['routed.route']['sha256']==audit['audit']['inputs']['route_sha256']
            pair=read(d/'pair_check.json');self.bind(d/'pair_check.json');assert pair['passed']
            source=Path(pair['source'])
            self.bind(d/'packed.net',m['outputs']['packed.net']['sha256'])
            assert self.bind(source/'packed.net')==self.bind(d/'packed.net')
            assert self.coordinates(d/'placed.place')==self.coordinates(source/'placed.place')
            self.bind(d/'placed.place',m['outputs']['placed.place']['sha256'])
            if spec['router']=='R1off':
                # The disabled control copies A0's private inputs; follow that
                # explicit chain back to the common placement artifact.
                a0=self.run(source.name,job,flow,dict(router='A0',variant=None,config=None))
                if a0['status']=='legal':
                    off=read(d/'off_equivalence.json');self.bind(d/'off_equivalence.json')
                    assert off['off_equals_official_A0']
                    from run_h3d_delay_study import route_body_hash
                    assert route_body_hash(d/'routed.route')==route_body_hash(source/'routed.route')
                upstream=read(source/'pair_check.json');self.bind(source/'pair_check.json')
                assert upstream['passed']
                source=Path(upstream['source'])
            place_check=read(source/'placement_check.json');self.bind(source/'placement_check.json');assert place_check['passed']
            capacity=read(BASE/'capacity_selection.json')['circuits'][job['circuit']]
            assert place_check['packed_semantic']['semantic_sha256']==capacity['semantic_sha256']
            size=capacity['size'];assert size==m['tags']['size']
            model_path=BASE/'benchmark_models'/f"n{size}_w{job['width']}"/'manifest.json'
            model=read(model_path);self.bind(model_path);assert model['status']=='ready'
            fixture=model['fixtures'][job['family']];conversion=fixture['conversion']
            assert audit['audit']['inputs']['rr_graph_sha256']==conversion['source_graph_sha256']
            graph=fixture['original_graph'] if spec['router']=='B2' else conversion['graph']
            graph_hash=conversion['source_graph_sha256'] if spec['router']=='B2' else conversion['graph_sha256']
            assert command[command.index('--read_rr_graph')+1]==graph
            assert m['shared_inputs'][graph]['sha256']==graph_hash
            result.update(status='legal',physical_metrics=audit['physical_metrics'],size=size,
                graph_sha256=graph_hash,original_graph_sha256=conversion['source_graph_sha256'],
                placement_source=str(source),audit_route_summary=audit['audit']['route'])
            assert result['physical_metrics'] is not None
            assert metrics.get('critical_path_ns',0)>0
        else:
            result['failure_class']=failure_class(m,log)
        result.update(guide_diagnostics(log))
        self.run_cache[name]=result
        return result


def failure_class(manifest,log):
    if manifest['status']=='timeout':return 'process_timeout'
    if manifest['status']=='input_integrity_failed':return 'input_integrity_failure'
    if 'bad_alloc' in log or 'Cannot allocate memory' in log or 'cannot allocate memory' in log:return 'allocation_failure_under_registered_limit'
    if 'Failed to find device which satisfies resource requirements' in log:return 'device_capacity'
    if 'Routing failed' in log or 'routing failed' in log or 'Circuit is unroutable' in log:return 'routing_failure'
    if manifest['status']=='completed':return 'missing_native_full_or_success_evidence'
    return manifest['status']


def collect(evidence):
    plan=read(BASE/'evaluation_jobs.json');protocol=read(BASE/'benchmark_protocol.json')
    evidence.bind(BASE/'benchmark_protocol.json',plan['protocol_sha256'])
    evidence.bind(BASE/'selected_configs.json',plan['selection_sha256'])
    evidence.bind(BASE/'evaluation_jobs.json');evidence.bind(BASE/'capacity_selection.json')
    table={};rows=[];cases=[]
    for job in plan['jobs']:
        name=f"{job['phase']}_{job['circuit']}_s{job['seed']}_{job['family']}_w{job['width']}"
        d=BASE/'evaluation_cases'/name
        result=read(d/'result.json');evidence.bind(d/'result.json')
        assert result['status']=='completed' and result['job']==job,f'Unresolved case: {d}'
        registration=read(d/'registration.json');evidence.bind(d/'registration.json')
        assert registration['selection_sha256']==plan['selection_sha256']
        assert registration['jobs_sha256']==evidence.bind(BASE/'evaluation_jobs.json')
        cases.append(result)
        for flow,roles in job['roles'].items():
            actual=result['flows'][flow]
            assert actual['status'] in ('completed','placement_failed')
            for role,spec in roles.items():
                if actual['status']=='completed':
                    row=evidence.run(actual['roles'][role],job,flow,spec)
                else:
                    assert role in actual['unattempted_roles']
                    place_dir=BASE/'runs'/actual['receipt']
                    placement=read(place_dir/'manifest.json');evidence.bind(place_dir/'manifest.json')
                    expected={k:job[k] for k in ['circuit','family','seed','width']}
                    expected.update(stage=job['phase'],placement=flow,operation='placement')
                    assert all(placement['tags'].get(k)==v for k,v in expected.items())
                    assert placement['status'] not in ('completed','running','starting')
                    for filename,info in placement.get('outputs',{}).items():
                        evidence.bind(place_dir/filename,info['sha256'])
                    row=dict(status='placement_failed',run=None,metrics={},physical_metrics={},
                        failure_class='shared_placement_failed',placement_receipt=actual['receipt'])
                key=(job['phase'],job['family'],flow,role)
                table.setdefault(key,{})[(job['circuit'],job['seed'])]=row
                rows.append(dict(phase=job['phase'],circuit=job['circuit'],seed=job['seed'],family=job['family'],
                    width=job['width'],flow=flow,role=role,configuration=spec,**row))
    return protocol,table,rows,cases


def summarize(protocol,tables):
    circuits=protocol['heldout'];seeds=protocol['evaluation_seeds'];families=protocol['architectures']
    reference=tables['heldout','matched_2d','p0','A0']
    comparisons={};factorials={};rank_tables={};ablations={}
    for family in families:
        cells={f'{flow}_{role}':tables['heldout',family,flow,role] for flow in ['p0','p1'] for role in ['A0','R1']}
        rank_tables.update({(family,cell):table for cell,table in cells.items()})
        factorials[family]=factorial_interaction(cells,circuits,seeds)
        family_results={}
        for flow in ['p0','p1']:
            r1=tables['heldout',family,flow,'R1'];a0=tables['heldout',family,flow,'A0'];b2=tables['heldout',family,flow,'B2']
            family_results[flow]=dict(routing_dual=dual(r1,a0,reference,circuits,seeds),
                modern_lazagna_paired=paired(r1,b2,circuits,seeds),
                official_vs_modern=paired(a0,b2,circuits,seeds),
                planar_wirelength=paired(r1,a0,circuits,seeds,metric='planar_wirelength_excluding_sb_half_nodes'))
        family_results['placement_only']=paired(cells['p1_A0'],cells['p0_A0'],circuits,seeds)
        family_results['combined_flow_dual']=dual(cells['p1_R1'],cells['p0_A0'],reference,circuits,seeds)
        comparisons[family]=family_results
        ablation_tables={kind:{v:tables['heldout',family,'p1',kind+'_'+v] for v in protocol['tuning']['variants']}
                         for kind in ['fixed','tuned']}
        shared=complete_circuits([cells['p1_A0'],*[t for group in ablation_tables.values() for t in group.values()]],circuits,[21])
        ablations[family]=dict(common_complete_circuits=shared,
            individually_paired={kind:{v:paired(t,cells['p1_A0'],circuits,[21]) for v,t in group.items()} for kind,group in ablation_tables.items()},
            joint_cohort={kind:{v:paired(t,cells['p1_A0'],circuits,[21],cohort=shared) for v,t in group.items()} for kind,group in ablation_tables.items()})
    ranking=architecture_rankings(rank_tables,reference,circuits,seeds,families,['p0_A0','p0_R1','p1_A0','p1_R1'])
    width={}
    for family in families:
        width[family]={}
        for flow in ['p0','p1']:
            by_split={}
            for split,subset,seed in [('training',[c for c in protocol['width_sensitivity']['circuits'] if c in protocol['training']],11),
                                      ('heldout',[c for c in protocol['width_sensitivity']['circuits'] if c in protocol['heldout']],21)]:
                by_split[split]=dict(vs_official=paired(tables['width300',family,flow,'R1'],tables['width300',family,flow,'A0'],subset,[seed]),
                    vs_modern=paired(tables['width300',family,flow,'R1'],tables['width300',family,flow,'B2'],subset,[seed]))
            width[family][flow]=by_split
    return dict(heldout=comparisons,factorial_interactions=factorials,architecture_rankings=ranking,ablations=ablations,
        width300_sensitivity=width,scope_notes=dict(
            maximum='Dual headline values are bound to the same circuit/seed. Geomeans use a common complete cohort.',
            runtime='Parallel sweep timings are raw observations only; use serial_summary for performance conclusions.',
            paper_baseline='Published LaZagna VTR8.1 has a different author2D denominator; no direct absolute ratio is calculated.',
            physical='Derived common-plane architecture family; logical capacity matching does not establish equal area/power/via budgets.'))


def main(output):
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    evidence=Evidence();protocol,tables,rows,cases=collect(evidence)
    summary=summarize(protocol,tables)
    from analyze_flatland_diagnostics import summarize as diagnostics_summary
    summary['algorithm_diagnostics']=diagnostics_summary(rows)
    summary.update(utc=utc(),status='all_registered_evaluation_cases_resolved',
        planned_cases=len(cases),planned_roles=len(rows),unique_attempted_route_runs=len(evidence.run_cache),
        role_status_counts=dict(Counter(r['status'] for r in rows)),
        unique_run_status_counts=dict(Counter(r['status'] for r in evidence.run_cache.values())),
        analysis_source_sha256=sha256(__file__),statistics_source_sha256=sha256(ROOT/'scripts/flatland_statistics.py'),
        diagnostics_source_sha256=sha256(ROOT/'scripts/analyze_flatland_diagnostics.py'))
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/'summary.json',summary);write_json(output/'role_observations.json',dict(rows=rows))
    write_json(output/'input_bindings.json',dict(utc=utc(),sha256=evidence.bindings,
        note='Graph binaries are linked through validated conversion/audit hashes; final artifact closure must independently rehash all unique shared files.'))
    columns=['phase','circuit','seed','family','width','flow','role','run','status','failure_class','critical_path_ns',
        'router_seconds','process_wall_seconds','iterations','planar_wirelength_excluding_sb_half_nodes',
        'sb_pairs_used','sb_pair_net_occupancy','cb_crossing_output_sources_used','cb_crossing_output_source_net_occupancy']
    with (output/'observations.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        for row in rows:
            flat=dict(row,**row['metrics'],**row['physical_metrics'])
            writer.writerow({c:flat.get(c) for c in columns})
    print('Evaluation aggregation complete',len(cases),'planned cases;',len(rows),'roles')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=BASE/'evaluation_analysis')
    main(p.parse_args().output)
