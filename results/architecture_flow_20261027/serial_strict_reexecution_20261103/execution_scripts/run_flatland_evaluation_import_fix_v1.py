#!/usr/bin/env python3
"""Registered held-out factorials, ablations, 2D references and width sensitivity."""
import argparse
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
import fcntl
import shutil
import traceback

import flatland_benchmark as study
import flatland_experiment_io as io
from lazagna_common import ROOT,sha256,utc,write_json
from deduplicate_training_route_inputs import link_group

BASE=study.BASE
MIN_FREE_BYTES=80*1024**3


def require_disk_space():
    free=shutil.disk_usage(BASE).free
    if free<MIN_FREE_BYTES:raise RuntimeError(f'Free space below evaluation reserve: {free} bytes; minimum {MIN_FREE_BYTES}')


def compact_completed_route_inputs(receipts,output):
    """Share byte-identical immutable route inputs only after their audit."""
    groups=defaultdict(list)
    for receipt in receipts:
        entry=receipt.get('outputs',{}).get('packed.net')
        if entry is not None:
            groups[entry['sha256']].append(BASE/'runs'/receipt['name']/'packed.net')
    candidates=[(digest,paths) for digest,paths in groups.items() if len(paths)>1]
    # Every group is fully checked before any file in this batch changes.
    for digest,paths in candidates:link_group(paths,digest,False)
    records=[link_group(paths,digest,True) for digest,paths in candidates]
    write_json(output,dict(utc=utc(),groups=records,saved_bytes=sum(x['saved_bytes'] for x in records),
        qualification='Only completed evaluation-route private packed.net outputs within one placement flow; audited first, byte-identical, immutable shared read-only. Source placement remains a separate file.'))
    return len(records)


def require_observation(receipt):
    if receipt['status'] in ('thread_constraint_violated','thread_observation_missing',
                             'input_integrity_failed','launch_failed'):
        raise RuntimeError(f"Infrastructure failure in preserved receipt {receipt['name']}: {receipt['status']}")


def roles(protocol,selections,family,seed,phase):
    if family=='matched_2d':return {'p0':{'A0':dict(router='A0',variant=None,config=None)}}
    selected=selections['selections'][family]
    chosen=selected['R1']
    result={f:dict(A0=dict(router='A0',variant=None,config=None),
        R1=dict(router='R1',variant=chosen['variant'],config=chosen['config']),
        B2=dict(router='B2',variant=None,config=None)) for f in ['p0','p1']}
    if phase=='heldout' and seed==21:
        for variant in protocol['tuning']['variants']:
            result['p1']['fixed_'+variant]=dict(router='R1',variant=variant,config=0)
            result['p1']['tuned_'+variant]=dict(router='R1',variant=variant,
                config=selected['per_variant'][variant]['selected'])
    return result


def register():
    protocol=study.read(BASE/'benchmark_protocol.json');selection=study.read(BASE/'selected_configs.json')
    assert selection['status']=='frozen_before_heldout'
    assert selection['protocol_sha256']==sha256(BASE/'benchmark_protocol.json')
    assert selection['training_jobs_sha256']==sha256(BASE/'training_jobs.json')
    preflight=BASE/'p1_training_preflight_state.json'
    assert study.read(preflight)['status']=='passed','P1 training-circuit packing/partition preflight is not complete'
    balance_review=BASE/'p1_training_partition_weight_review.json'
    if balance_review.exists():
        assert study.read(balance_review)['status']=='resolved', 'P1 partition balance diagnosis must be resolved before evaluation registration'
    shared_sources=study.read(BASE/'training_jobs.json')['source_sha256']
    for path,digest in shared_sources.items():
        assert sha256(path)==digest,f'Frozen shared implementation changed: {path}'
    jobs=[]
    for c in protocol['heldout']:
        for s in protocol['evaluation_seeds']:
            for f in [*protocol['architectures'],'matched_2d']:
                jobs.append(dict(phase='heldout',circuit=c,seed=s,family=f,width=100,
                                 roles=roles(protocol,selection,f,s,'heldout')))
    for c in protocol['width_sensitivity']['circuits']:
        s=11 if c in protocol['training'] else 21
        for f in protocol['architectures']:
            jobs.append(dict(phase='width300',circuit=c,seed=s,family=f,width=300,
                             roles=roles(protocol,selection,f,s,'width300')))
    data=dict(protocol_sha256=sha256(BASE/'benchmark_protocol.json'),selection_sha256=sha256(BASE/'selected_configs.json'),
        resource_amendment_sha256=sha256(BASE/'execution_resource_amendment.json'),
        evaluation_source_sha256=sha256(__file__),shared_source_sha256=shared_sources,
        p1_preflight_sha256=sha256(preflight),
        partition_balance_resolution_sha256=sha256(balance_review),
        partition_balance_sensitivity_protocol_sha256=sha256(BASE/'partition_balance_sensitivity_protocol.json'),
        route_input_compaction_source_sha256=sha256(Path(__file__).parent/'deduplicate_training_route_inputs.py'),
        route_input_compaction_policy='After flow route audit, use verified byte-identical read-only hardlinks for private packed.net outputs within that flow; do not change placement source or route evidence.',
        minimum_free_bytes=MIN_FREE_BYTES,jobs=jobs)
    path=BASE/'evaluation_jobs.json'
    if path.exists():
        old=study.read(path)
        for k,v in data.items():assert old[k]==v,f'Evaluation plan changed: {k}'
    else:write_json(path,dict(utc=utc(),**data))
    return data


def run(job):
    c,f,s,w,phase=(job[k] for k in ['circuit','family','seed','width','phase'])
    name=f'{phase}_{c}_s{s}_{f}_w{w}'
    directory=BASE/'evaluation_cases'/name;directory.mkdir(parents=True,exist_ok=True)
    path=directory/'result.json'
    if path.exists():
        old=study.read(path);assert old['status']=='completed',f'Recovery decision needed: {path}'
        return old
    write_json(directory/'registration.json',dict(utc=utc(),**job,
        jobs_sha256=sha256(BASE/'evaluation_jobs.json'),selection_sha256=sha256(BASE/'selected_configs.json')))
    rows={}
    try:
        ctx=study.context(c,f,s,w)
        for flow,arms in job['roles'].items():
            require_disk_space()
            place=study.placement(ctx,phase,flow)
            require_observation(place)
            if place['status']!='completed':
                rows[flow]=dict(status='placement_failed',receipt=place['name'],
                    unattempted_roles=list(arms),reason='Shared placement failed; all planned descendant roles retained')
                continue
            unique={};references={}
            for role,spec in arms.items():
                key=tuple(spec[k] for k in ['router','variant','config'])
                if key not in unique:
                    require_disk_space()
                    unique[key]=study.route(ctx,phase,flow,*key)
                    require_observation(unique[key])
                references[role]=unique[key]['name']
                write_json(directory/'state.json',dict(utc=utc(),status='routing',flow=flow,roles=references))
            validation=study.audit_batch(ctx,list(unique.values()),directory/f'{flow}_audit_summary.json')
            compact_completed_route_inputs(list(unique.values()),directory/f'{flow}_input_compaction.json')
            rows[flow]=dict(status='completed',roles=references,registered_roles=len(arms),
                unique_runs=len(unique),legal_runs=validation['legal_count'],failed_runs=validation['failed_count'])
        result=dict(utc=utc(),status='completed',job=job,flows=rows)
    except Exception as error:
        result=dict(utc=utc(),status='error',job=job,flows=rows,error=str(error),traceback=traceback.format_exc())
    write_json(path,result);print('evaluation case',name,result['status'],flush=True)
    return result


def execute_cases(jobs,workers,runner=run):
    """Drain active cases but stop new submissions on infrastructure errors."""
    results=[];submitted=0;stopped=False
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending={}
        def submit():
            nonlocal submitted
            job=jobs[submitted];submitted+=1;pending[pool.submit(runner,job)]=job
        for _ in range(min(workers,len(jobs))):submit()
        while pending:
            done,_=wait(pending,return_when=FIRST_COMPLETED)
            for future in done:
                job=pending.pop(future)
                try:result=future.result()
                except Exception as error:
                    result=dict(status='error',job=job,error=str(error),traceback=traceback.format_exc())
                results.append(result)
                if result['status']!='completed':stopped=True
            if not stopped:
                while len(pending)<workers and submitted<len(jobs):submit()
    return results,jobs[submitted:]


def main(phase,circuits,seeds,workers):
    assert 1<=workers<=6
    lock=(BASE/'evaluation_runner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    plan=register();jobs=[j for j in plan['jobs'] if j['phase']==phase]
    if circuits:
        assert set(circuits)<=set(j['circuit'] for j in jobs)
        jobs=[j for j in jobs if j['circuit'] in circuits]
    if seeds:
        assert set(seeds)<=set(j['seed'] for j in jobs)
        jobs=[j for j in jobs if j['seed'] in seeds]
    assert jobs
    for j in jobs:study.context(j['circuit'],j['family'],j['seed'],j['width'])
    results,unstarted=execute_cases(jobs,workers)
    directory=BASE/'evaluation_invocations';directory.mkdir(exist_ok=True)
    stem=phase+'_'+'_'.join(circuits or ['all'])+'_s'+'-'.join(map(str,seeds or [0]))
    output=directory/f'{stem}.json';assert not output.exists()
    write_json(output,dict(utc=utc(),phase=phase,workers=workers,results=results,
        planned_cases=len(jobs),unstarted_jobs=unstarted,
        failure_handling='Infrastructure errors stop new submissions and drain active cases; unstarted registered cases remain required. Normal routed/placement failures remain observations.'))
    io.seal_inputs(directory/f'{stem}_input_integrity.json')
    if any(x['status']!='completed' for x in results):raise RuntimeError('Preserved evaluation cases require diagnosis; unstarted jobs remain required')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['heldout','width300'],required=True)
    p.add_argument('--circuits',nargs='+');p.add_argument('--seeds',type=int,nargs='+')
    p.add_argument('--workers',type=int,default=6);a=p.parse_args()
    main(a.phase,a.circuits,a.seeds,a.workers)
