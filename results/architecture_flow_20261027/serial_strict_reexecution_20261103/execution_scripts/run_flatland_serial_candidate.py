#!/usr/bin/env python3
"""Candidate guarded serial repeats, gated on real workload verification."""
import fcntl
import os
from pathlib import Path
import shutil

import flatland_benchmark as study
import flatland_timing_io_candidate as io
from lazagna_common import ROOT,sha256,utc,write_json
from run_h3d_delay_study import route_body_hash
from validate_lazagna_vtr9_pilot import placements

BASE=study.BASE
MIN_FREE_BYTES=80*1024**3
# The shared operation functions resolve this module attribute at call time.
study.io=io


def require_disk_space():
    free=shutil.disk_usage(BASE).free
    if free<MIN_FREE_BYTES:raise RuntimeError(f'Free space below serial reserve: {free} bytes; minimum {MIN_FREE_BYTES}')


def require_observation(receipt):
    if receipt['status'] in ('thread_constraint_violated','thread_observation_missing',
                             'input_integrity_failed','launch_failed'):
        raise RuntimeError(f"Infrastructure failure in preserved receipt {receipt['name']}: {receipt['status']}")


def idle():
    running=[]
    for p in (BASE/'runs').glob('*/manifest.json'):
        m=study.read(p)
        if m['status'] in ('starting','running'):running.append(m['name'])
    if running:raise RuntimeError(f'Owned study jobs still active; serial timing cannot start: {running}')


def disabled(ctx,stage,flow,a0):
    source=BASE/'runs'/a0['name'];name=a0['name'].removesuffix('_a0')+'_r1off'
    if (previous:=study.existing(name)) is not None:return previous
    d=BASE/'runs'/name;d.mkdir(parents=True,exist_ok=False)
    for f in ['packed.net','placed.place']:shutil.copy2(source/f,d/f)
    binary=ctx['protocol']['binaries']['R1'];io.frozen_hash(binary['path'],binary['sha256'])
    command=[str(x).replace(str(source),str(d)) for x in a0['command']];command[0]=binary['path']
    # Match the active binary's diagnostics while disabling algorithm changes.
    env=dict(VPR_H3D_MODE='off',VPR_H3D_REACHABILITY='scc',VPR_H3D_GRAPH_ENCODING='edge',VPR_H3D_STATS='1')
    frozen=[*a0['shared_inputs'],binary['path'],source/'packed.net',source/'placed.place']
    result=io.run(name,command,frozen=frozen,private_inputs=[d/'packed.net',d/'placed.place'],environment=env,
        timeout=1800,tags=study.tags(ctx,stage,flow,operation='route',router='R1off',variant=None,config=None))
    pair=dict(packed_identical=sha256(d/'packed.net')==sha256(source/'packed.net'),
        placement_identical=placements(d/'placed.place')==placements(source/'placed.place'))
    write_json(d/'pair_check.json',dict(utc=utc(),passed=all(pair.values()),checks=pair,source=str(source)))
    assert all(pair.values())
    if result['status']=='completed' and a0['status']=='completed':
        same=route_body_hash(d/'routed.route')==route_body_hash(source/'routed.route')
        write_json(d/'off_equivalence.json',dict(utc=utc(),off_equals_official_A0=same))
        assert same,'Disabled current build differs from official A0; diagnose before runtime attribution'
    return result


def main():
    locks=[]
    for name in ['serial_runner.lock','training_runner.lock','evaluation_runner.lock']:
        lock=(BASE/name).open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(lock)
    validation=BASE/'seccomp_full_workload_validation.json'
    proof=study.read(validation)
    assert proof['status']=='passed' and set(proof['covered_workloads']) >= {'A0','R1','B2','P1'}
    assert proof['timing_runner_sha256']==sha256(io.__file__)
    assert proof['guard_sha256']==sha256(io.GUARD)
    for path,digest in proof['evidence_sha256'].items():assert sha256(path)==digest,path
    unfinished=[str(p.parent) for p in (BASE/'benchmark_models').glob('*/registration.json') if not (p.parent/'manifest.json').exists()]
    assert not unfinished,f'Model preparation still active/unresolved: {unfinished}'
    idle();p=study.read(BASE/'benchmark_protocol.json');selection=study.read(BASE/'selected_configs.json')
    require_disk_space()
    assert selection['status']=='frozen_before_heldout'
    assert selection['training_jobs_sha256']==sha256(BASE/'training_jobs.json')
    shared_sources=study.read(BASE/'training_jobs.json')['source_sha256']
    for path,digest in shared_sources.items():assert sha256(path)==digest,f'Frozen implementation changed: {path}'
    output=BASE/'serial_protocol.json'
    if output.exists():raise FileExistsError(output)
    write_json(output,dict(utc=utc(),protocol_sha256=sha256(BASE/'benchmark_protocol.json'),
        selection_sha256=sha256(BASE/'selected_configs.json'),source_sha256=sha256(__file__),
        timing_method='seccomp_guard_no_ptrace',guard_validation_sha256=sha256(validation),
        timing_runner_sha256=sha256(io.__file__),guard_sha256=sha256(io.GUARD),
        minimum_free_bytes=MIN_FREE_BYTES,
        shared_source_sha256=shared_sources,
        preregistered=p['runtime'],
        amendment='Add a disabled R1-binary control to each repeat before measuring any serial result',
        reason='Official A0 and R1 share compiler/IPO setting, but differ in optional frontend/interchange build flags. Report official baseline and same-build algorithm overhead separately.',
        off_control='VPR_H3D_MODE=off with matching edge/statistics instrumentation; require exact A0 route-body identity on successful pairs',
        setup='Repeat pack/partition/placement setup for each flow/repetition; assert cross-repeat placement coordinates identical before attributing router runtime',
        rotation='Rotate A0,R1,B2 order by repetition. Disabled build control runs after that triplet so it does not alter the preregistered triplet order.',
        isolation='No concurrent VPR/partition process owned by this study. Host is shared; load averages retained, no exclusive-host claim.'))
    all_results=[];first_places={}
    for c in p['runtime']['circuits']:
        seed=p['runtime']['seeds'][c]
        for family in p['runtime']['architectures']:
            ctx=study.context(c,family,seed);chosen=selection['selections'][family]['R1']
            for flow in ['p0','p1']:
                for repeat in range(3):
                    idle();stage=f'serial_r{repeat+1}'
                    require_disk_space()
                    placed=study.placement(ctx,stage,flow)
                    require_observation(placed)
                    if placed['status']!='completed':
                        all_results.append(dict(circuit=c,family=family,flow=flow,repeat=repeat+1,status='placement_failed',placement=placed['name']))
                        continue
                    d=BASE/'runs'/placed['name'];coordinates=placements(d/'placed.place')
                    key=(c,family,flow)
                    if key in first_places:assert coordinates==first_places[key],key
                    else:first_places[key]=coordinates
                    order=['A0','R1','B2'];order=order[repeat:]+order[:repeat]
                    runs={};loads={}
                    for router in order:
                        idle();loads[router]=os.getloadavg()
                        require_disk_space()
                        runs[router]=study.route(ctx,stage,flow,router,
                            chosen['variant'] if router=='R1' else None,chosen['config'] if router=='R1' else None)
                        require_observation(runs[router])
                    idle();loads['R1off']=os.getloadavg();require_disk_space();runs['R1off']=disabled(ctx,stage,flow,runs['A0'])
                    require_observation(runs['R1off'])
                    directory=BASE/'serial_cases'/f'{c}_{family}_{flow}_r{repeat+1}'
                    directory.mkdir(parents=True,exist_ok=False)
                    audit=study.audit_batch(ctx,list(runs.values()),directory/'audit_summary.json')
                    row=dict(circuit=c,family=family,flow=flow,repeat=repeat+1,status='completed',
                        placement=placed['name'],router_order=order+['R1off'],host_load_before=loads,
                        runs={k:v['name'] for k,v in runs.items()},legal=audit['legal_count'],failed=audit['failed_count'])
                    write_json(directory/'result.json',row);all_results.append(row)
                    write_json(BASE/'serial_progress.json',dict(utc=utc(),complete_repetitions=len(all_results),expected_repetitions=36))
    write_json(BASE/'serial_summary.json',dict(utc=utc(),results=all_results,expected_repetitions=36))
    io.seal_inputs(BASE/'serial_input_integrity.json')


if __name__=='__main__':main()
