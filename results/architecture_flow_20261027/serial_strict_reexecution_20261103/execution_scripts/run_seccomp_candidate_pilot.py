#!/usr/bin/env python3
"""Compare a no-ptrace guarded VPR route with its traced diagnostic fixture.

This is a pilot, not the registered serial timing study.  The shared locks
prevent it from consuming a VPR slot during training/evaluation/timing.
"""
import fcntl
from pathlib import Path
import shutil

import flatland_benchmark as study
import flatland_timing_io_candidate as timing
from lazagna_common import sha256,utc,write_json
from run_h3d_delay_study import route_body_hash
from validate_lazagna_vtr9_pilot import placements


def main():
    base=study.BASE
    locks=[]
    for name in ('serial_runner.lock','training_runner.lock','evaluation_runner.lock'):
        handle=(base/name).open('a')
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        locks.append(handle)
    reference=base/'runs/strict_binding_pilot_spmv_s11_sb_n40_w100_p0_a0'
    fixture=base/'runs/strict_binding_pilot_spmv_s11_sb_n40_w100_p0_place'
    previous=study.read(reference/'manifest.json')
    assert previous['status']=='completed' and previous['metrics']['native_full_check_passed']
    guard=Path(__file__).with_name('seccomp_thread_guard').resolve()
    directory=base/'runs/seccomp_pilot_spmv_s11_sb_n40_w100_p0_a0'
    directory.mkdir(parents=True,exist_ok=False)
    for name in ('packed.net','placed.place'):shutil.copy2(fixture/name,directory/name)
    command=[x.replace(str(reference),str(directory)) for x in previous['command']]
    assert command[0]==previous['command'][0]
    for path,record in previous['shared_inputs'].items():
        timing.frozen_hash(path,record['sha256'])
    sources=[guard,Path(__file__),reference/'manifest.json',reference/'routed.route',
             fixture/'packed.net',fixture/'placed.place',base/'benchmark_protocol.json',
             base/'runtime_dependency_binding.json',*previous['shared_inputs']]
    write_json(directory/'registration.json',dict(utc=utc(),sources={str(p):sha256(p) for p in sources},
        qualification='Non-ptrace diagnostic pilot on one A0 route; not a timing result.'))
    data=timing.run(directory.name,command,frozen=sources,
        private_inputs=[directory/'packed.net',directory/'placed.place'],timeout=1800,
        tags=dict(circuit='spmv',family='sb',seed=11,width=100,stage='seccomp_pilot',
                  placement='p0',operation='route',router='A0'))
    observation=data['process_tree_observation'];metrics=data['metrics']
    assert data['status']=='completed' and observation['samples']>0 and not observation['violation_observed']
    assert metrics['native_full_check_passed'] and metrics['routing_success_reported']
    assert sha256(directory/'packed.net')==sha256(fixture/'packed.net')
    assert placements(directory/'placed.place')==placements(fixture/'placed.place')
    write_json(directory/'pair_check.json',dict(utc=utc(),passed=True,source=str(fixture)))
    ctx=study.context('spmv','sb',11,100)
    audit=study.audit_batch(ctx,[data],directory/'pilot_audit.json')
    assert audit['legal_count']==1 and audit['failed_count']==0
    timing.seal_inputs(directory/'input_integrity.json')
    same=route_body_hash(directory/'routed.route')==route_body_hash(reference/'routed.route')
    assert same and metrics['critical_path_ns']==previous['metrics']['critical_path_ns']
    write_json(directory/'pilot_comparison.json',dict(utc=utc(),passed=True,route_body_identical=same,
        cpd_ns=metrics['critical_path_ns'],reference=str(reference),
        caveat='One route only; other binaries, P1 partitioning, wider graphs and timing impact remain unverified.'))
    print('no-ptrace seccomp candidate route pilot passed',flush=True)


if __name__=='__main__':main()
