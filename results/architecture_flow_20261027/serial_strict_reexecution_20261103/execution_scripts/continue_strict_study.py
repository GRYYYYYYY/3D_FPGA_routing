#!/usr/bin/env python3
"""Advance locked research stages only after the exact training owner exits.

This coordinator does not declare scientific completion; it stops at the
first failed command or missing gate and preserves all existing evidence.
"""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from flatland_benchmark import BASE,read
from lazagna_common import ROOT,sha256,utc,write_json

SCRIPTS=Path(__file__).resolve().parent
STAGES=[
    ('training_dedup_dry_run',['deduplicate_training_route_inputs.py']),
    ('training_dedup_apply',['deduplicate_training_route_inputs.py','--apply']),
    ('selection',['select_flatland_configs.py']),
    ('training_analysis',['analyze_flatland_training.py']),
    ('seccomp_workload_pilot',['run_seccomp_full_workload_pilot.py']),
    ('heldout',['run_flatland_evaluation.py','--phase','heldout','--workers','6']),
    ('width300',['run_flatland_evaluation.py','--phase','width300','--workers','6']),
    ('serial',['run_flatland_serial_candidate.py']),
    ('balance',['run_flatland_balance_sensitivity.py']),
    ('evaluation_analysis',['analyze_flatland_evaluation.py']),
    ('serial_analysis',['analyze_flatland_serial_candidate.py']),
    ('balance_analysis',['analyze_flatland_balance_sensitivity.py']),
    ('figures',['render_flatland_figures.py']),
    ('report',['render_flatland_report.py']),
]


def identity(pid):
    try:
        text=Path(f'/proc/{pid}/stat').read_text();fields=text[text.rindex(')')+2:].split()
        if fields[0]=='Z':return None
        return int(fields[19])
    except FileNotFoundError:return None


def verify(bindings):
    for path,digest in bindings.items():
        assert sha256(path)==digest,f'Frozen continuation input changed: {path}'


def training_gate():
    protocol=read(BASE/'benchmark_protocol.json');plan=read(BASE/'training_jobs.json')
    assert len(plan['jobs'])==594
    total=0
    for circuit in protocol['training']:
        for family in protocol['architectures']:
            d=BASE/'training_cases'/f'{circuit}_{family}'
            result=read(d/'result.json');audit=read(d/'audit_summary.json')
            assert result['status']=='completed' and result['registered_routes']==33,d
            assert audit['passed'] and audit['registered_route_count']==33
            assert result['legal_routes']==audit['legal_count']==len(audit['legal'])
            assert result['failed_routes']==audit['failed_count']==len(audit['failed'])
            assert audit['legal_count']+audit['failed_count']==33
            total+=33
    assert total==594
    stem='_'.join(protocol['training']);folder=BASE/'training_invocations'
    invocation=read(folder/(stem+'.json'));seal=read(folder/(stem+'_input_integrity.json'))
    assert invocation['complete_suite'] and not invocation['unstarted_pairs']
    assert len(invocation['results'])==18 and all(x['status']=='completed' for x in invocation['results'])
    assert seal['passed']
    assert read(BASE/'p1_training_preflight_state.json')['status']=='passed'
    assert read(BASE/'p1_training_partition_weight_review.json')['status']=='resolved'


def quiescent():
    active=[]
    for p in (BASE/'runs').glob('*/manifest.json'):
        if read(p)['status'] in ('starting','running'):active.append(p.parent.name)
    assert not active,f'Unresolved owned process receipts: {active}'


def main(pid,start_ticks):
    lock=(BASE/'strict_continuation.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert identity(pid)==start_ticks,'Training owner is not live with the registered identity'
    command=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    assert any(x.endswith(b'/run_flatland_training.py') for x in command)
    for c in read(BASE/'benchmark_protocol.json')['training']:assert c.encode() in command
    directory=BASE/'strict_continuation';directory.mkdir(exist_ok=False)
    completed=[];state_path=directory/'state.json'
    def state(status,**fields):
        write_json(state_path,dict(utc=utc(),supervisor_pid=os.getpid(),status=status,
                                   completed_stages=completed,**fields))
    try:
        outputs=['selected_configs.json','training_analysis','seccomp_full_workload_validation.json',
                 'evaluation_jobs.json','serial_protocol.json','partition_balance_sensitivity_jobs.json',
                 'evaluation_analysis','serial_analysis','balance_analysis','figures','report.html',
                 'training_deduplication_dry_run.json','training_deduplication_applied.json']
        for name in outputs:assert not (BASE/name).exists(),f'Existing output requires review: {name}'
        files={SCRIPTS/args[0] for _,args in STAGES}
        files.update(SCRIPTS/name for name in ('continue_strict_study.py','flatland_benchmark.py',
            'flatland_experiment_io.py','flatland_timing_io_candidate.py','process_tree_observer.py',
            'flatland_statistics.py','analyze_flatland_diagnostics.py','deduplicate_training_route_inputs.py',
            'seccomp_thread_guard','seccomp_thread_guard.c'))
        files.update(ROOT/'scripts'/name for name in ('lazagna_common.py','run_vpr.py',
            'validate_lazagna_vtr9_pilot.py','run_h3d_delay_study.py','check_route.py',
            'compare_lazagna_graphs.py','check_flatland_partition_balance.py'))
        files.update(BASE/name for name in ('execution_contract.json','benchmark_protocol.json',
            'training_jobs.json','execution_resource_amendment.json','runtime_dependency_binding.json',
            'partition_balance_sensitivity_protocol.json','p1_training_preflight_state.json',
            'p1_training_partition_weight_review.json','seccomp_guard_unit_validation.json'))
        bindings={str(p):sha256(p) for p in files}
        bindings.update(read(BASE/'training_jobs.json')['source_sha256']);verify(bindings)
        write_json(directory/'registration.json',dict(utc=utc(),training_owner_pid=pid,
            training_owner_start_ticks=start_ticks,source_and_protocol_sha256=bindings,stages=STAGES,
            contract='Wait for exact owner, require all 594 role audits and input seal, stop at first failed stage; source-derived builds and guarded timing remain explicitly qualified.'))
        while identity(pid)==start_ticks:
            state('waiting_training_owner',training_owner_pid=pid,training_owner_start_ticks=start_ticks)
            time.sleep(30)
        verify(bindings);training_gate();quiescent()
        env=os.environ.copy();env['PYTHONPATH']=str(SCRIPTS)+os.pathsep+str(ROOT/'scripts')
        env['PYTHONUNBUFFERED']='1'
        for label,args in STAGES:
            verify(bindings);quiescent()
            if label=='heldout':
                assert read(BASE/'training_analysis/summary.json')['status']=='all_registered_training_attempts_accounted'
                assert read(BASE/'selected_configs.json')['status']=='frozen_before_heldout'
                assert read(BASE/'seccomp_full_workload_validation.json')['status']=='passed'
            cmd=[sys.executable,str(SCRIPTS/args[0]),*args[1:]]
            state('running_stage',stage=label,command=cmd)
            with (directory/(label+'.log')).open('x') as log:
                subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            completed.append(label);state('stage_completed',stage=label)
        state('awaiting_scientific_and_integrity_closure',report=str(BASE/'report.html'))
    except BaseException as error:
        state('needs_diagnosis',error=str(error),traceback=traceback.format_exc())
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--training-pid',type=int,required=True)
    parser.add_argument('--training-start-ticks',type=int,required=True);args=parser.parse_args()
    main(args.training_pid,args.training_start_ticks)
