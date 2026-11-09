#!/usr/bin/env python3
"""Matched-placement W100/W300 diagnostic, after the primary study only."""
import fcntl
from pathlib import Path
import shutil
import traceback

import flatland_benchmark as study
import flatland_experiment_io as io
from lazagna_common import sha256,utc,write_json
from validate_lazagna_vtr9_pilot import placements

BASE=study.BASE
STAGE='paired_width'
MIN_FREE_BYTES=80*1024**3


def require_disk_space():
    free=shutil.disk_usage(BASE).free
    if free<MIN_FREE_BYTES:raise RuntimeError(f'Free space below diagnostic reserve: {free} bytes; minimum {MIN_FREE_BYTES}')


def require_observation(receipt):
    if receipt['status'] in ('thread_constraint_violated','thread_observation_missing',
                             'input_integrity_failed','launch_failed'):
        raise RuntimeError(f"Infrastructure failure in preserved receipt {receipt['name']}: {receipt['status']}")


def role_specs(selection,family):
    selected=selection['selections'][family]['R1']
    return {'A0':('A0',None,None), 'geometry_c0':('R1','geometry',0),
            'selected_R1':('R1',selected['variant'],selected['config'])}


def primary_gate():
    paths={'training':BASE/'training_analysis/summary.json',
           'evaluation':BASE/'evaluation_analysis/summary.json',
           'serial':BASE/'serial_analysis/summary.json',
           'balance':BASE/'balance_analysis/summary.json',
           'selection':BASE/'selected_configs.json'}
    values={k:study.read(p) for k,p in paths.items()}
    assert values['training']['status']=='all_registered_training_attempts_accounted'
    assert values['training']['registered_attempts']==594
    assert values['evaluation']['status']=='all_registered_evaluation_cases_resolved'
    assert values['evaluation']['planned_cases']==180
    assert values['serial']['observed_repetitions']==36
    assert values['serial']['timing_method']=='seccomp_guard_no_ptrace' and values['serial']['isolation']['passed']
    assert values['balance']['status']=='complete' and len(values['balance']['observations'])==144
    assert values['selection']['status']=='frozen_before_heldout'
    assert values['selection']['training_jobs_sha256']==sha256(BASE/'training_jobs.json')
    assert values['selection']['protocol_sha256']==sha256(BASE/'benchmark_protocol.json')
    return values['selection'],{str(p):sha256(p) for p in paths.values()}


def contexts(case):
    contexts={w:study.context(case['circuit'],case['family'],case['seed'],w) for w in (100,300)}
    assert all(x['size']==case['size'] for x in contexts.values())
    for index,w in enumerate((100,300)):
        ctx=contexts[w];conv=ctx['fixture']['conversion']
        assert sha256(ctx['model_path'])==case['manifest_sha256'][index]
        assert sha256(conv['architecture'])==case['native_architecture_sha256']==conv['architecture_sha256']
        assert sha256(ctx['fixture']['architecture'])==case['source_architecture_sha256']==conv['source_architecture_sha256']
        assert conv['source_graph_sha256']==case['original_graph_sha256'][index]
        assert conv['graph_sha256']==case['native_graph_sha256'][index]
        io.frozen_hash(conv['graph'],conv['graph_sha256'])
        io.frozen_hash(ctx['fixture']['original_graph'],conv['source_graph_sha256'])
    return contexts


def route(ctx,flow,source,router,variant,config):
    """Route on ctx width while retaining the explicit W100 placement source."""
    source=Path(source)
    assert study.read(source/'placement_check.json')['passed']
    arm=router.lower() if router!='R1' else f'{variant}_c{config}'
    name=study.prefix(ctx,STAGE,flow)+'_'+arm
    d=BASE/'runs'/name;d.mkdir(parents=True,exist_ok=False)
    for filename in ('packed.net','placed.place'):shutil.copy2(source/filename,d/filename)
    info=ctx['protocol']['binaries'][router];binary=info['path'];io.frozen_hash(binary,info['sha256'])
    fixture=ctx['fixture'];arch=fixture['conversion']['architecture'];graph=fixture['conversion']['graph']
    command=[binary,arch,ctx['blif'],'--route','--analysis','--device','fixture',
        '--route_chan_width',ctx['width'],'--num_workers',1,'--seed',ctx['seed'],'--clock_modeling','ideal',
        '--check_route','full','--verify_file_digests','off','--read_rr_graph',graph,
        '--max_router_iterations',200,'--routing_failure_predictor','off','--timing_report_npaths',0,
        '--net_file',d/'packed.net','--place_file',d/'placed.place','--route_file',d/'routed.route',
        '--merge_constant_generators','off']
    env=ctx['protocol']['tuning']['variants'][variant][config]['environment'] if router=='R1' else {}
    frozen=[binary,arch,graph,ctx['blif'],source/'packed.net',source/'placed.place',ctx['model_path'],
            BASE/'benchmark_protocol.json',BASE/'capacity_selection.json',BASE/'selected_configs.json',
            BASE/'paired_width_diagnostic_protocol.json',BASE/'paired_width_jobs.json']
    result=io.run(name,command,frozen=frozen,private_inputs=[d/'packed.net',d/'placed.place'],
        environment=env,timeout=1800,tags=study.tags(ctx,STAGE,flow,operation='route',
            router=router,variant=variant,config=config))
    require_observation(result)
    checks={'packed_identical':sha256(d/'packed.net')==sha256(source/'packed.net'),
            'placement_identical':placements(d/'placed.place')==placements(source/'placed.place')}
    write_json(d/'pair_check.json',dict(utc=utc(),passed=all(checks.values()),checks=checks,
        source=str(source),source_width=100,target_width=ctx['width']))
    assert all(checks.values()),d
    return result


def run_case(case,flow,selection,registration_sha):
    name=f"{case['circuit']}_s{case['seed']}_{case['family']}_{flow}"
    directory=BASE/'paired_width_cases'/name;directory.mkdir(parents=True,exist_ok=False)
    write_json(directory/'registration.json',dict(utc=utc(),case=case,flow=flow,registration_sha256=registration_sha))
    outcome=dict(utc=utc(),case=case,flow=flow,status='starting',widths={})
    try:
        c=contexts(case);require_disk_space();place=study.placement(c[100],STAGE,flow);require_observation(place)
        outcome['placement']=place['name']
        if place['status']!='completed':
            outcome.update(status='placement_failed',unattempted_roles=6)
        else:
            source=BASE/'runs'/place['name']
            for width in (100,300):
                unique={};roles={}
                for role,spec in role_specs(selection,case['family']).items():
                    if spec not in unique:
                        require_disk_space();unique[spec]=route(c[width],flow,source,*spec)
                    roles[role]=unique[spec]['name']
                audit=study.audit_batch(c[width],list(unique.values()),directory/f'audit_w{width}.json')
                outcome['widths'][str(width)]=dict(roles=roles,registered_roles=3,
                    unique_runs=len(unique),legal_runs=audit['legal_count'],failed_runs=audit['failed_count'])
            outcome['status']='completed'
    except Exception as error:
        outcome.update(status='error',error=str(error),traceback=traceback.format_exc())
    write_json(directory/'result.json',outcome)
    print('paired width case',name,outcome['status'],flush=True)
    return outcome


def main():
    locks=[]
    for name in ('serial_runner.lock','training_runner.lock','evaluation_runner.lock'):
        handle=(BASE/name).open('a');fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(handle)
    selection,primary_hashes=primary_gate()
    protocol_path=BASE/'paired_width_diagnostic_protocol.json';protocol=study.read(protocol_path)
    assert protocol['status']=='design_registered_before_new_matched_width_runs'
    assert protocol['parent_protocol_sha256']==sha256(BASE/'benchmark_protocol.json')
    assert protocol['training_registration_sha256']==sha256(BASE/'training_jobs.json')
    assert len(protocol['cases'])==12 and len(protocol['roles'])==144
    jobs=[(case,flow) for case in protocol['cases'] for flow in ('p0','p1')]
    for case,_ in jobs:contexts(case)
    registration=BASE/'paired_width_jobs.json'
    if registration.exists():raise FileExistsError(registration)
    write_json(registration,dict(utc=utc(),protocol_sha256=sha256(protocol_path),primary_sha256=primary_hashes,
        selection_sha256=sha256(BASE/'selected_configs.json'),source_sha256=sha256(__file__),
        minimum_free_bytes=MIN_FREE_BYTES,jobs=[dict(case=c,flow=f) for c,f in jobs],registered_roles=144))
    results=[]
    for index,(case,flow) in enumerate(jobs):
        result=run_case(case,flow,selection,sha256(registration));results.append(result)
        if result['status']=='error':break
    summary=BASE/'paired_width_summary.json'
    write_json(summary,dict(utc=utc(),registered_cases=24,registered_roles=144,results=results,
        unstarted_jobs=[dict(case=c,flow=f) for c,f in jobs[len(results):]]))
    io.seal_inputs(BASE/'paired_width_input_integrity.json')
    assert len(results)==24 and all(x['status']!='error' for x in results)


if __name__=='__main__':main()
