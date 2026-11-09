#!/usr/bin/env python3
"""Check P1 packing control on a real training circuit before held-out work."""
import fcntl
import os
import time
import traceback

import flatland_benchmark as study
import flatland_experiment_io as io
from lazagna_common import ROOT,sha256,utc,write_json
from flatland_low_concurrency_gate import ready as low_concurrency_ready

BASE=study.BASE


def state(**fields):write_json(BASE/'p1_training_preflight_state.json',dict(utc=utc(),pid=os.getpid(),**fields))


def main():
    lock=(BASE/'p1_training_preflight.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    path=BASE/'p1_training_preflight_protocol.json';assert not path.exists()
    frozen=study.read(BASE/'training_jobs.json')['source_sha256']
    write_json(path,dict(utc=utc(),source_sha256=sha256(__file__),shared_source_sha256=frozen,
        gate_source_sha256=sha256(ROOT/'scripts/flatland_low_concurrency_gate.py'),
        circuit='spmv',family='sb',seed=11,width=100,flow='p1',
        gate='Wait for all three audited softmax cases; at most three attention/subsequent training VPRs remain. One extra VPR plus at most two W300 graph VPRs keeps the total at most six.',
        purpose='Packing semantic/real TritonPart integration validation on a training circuit; no held-out observations or configuration selection.'))
    try:
        while not low_concurrency_ready():
            state(status='waiting_for_training_to_need_at_most_three_slots');time.sleep(20)
        for p,digest in frozen.items():assert sha256(p)==digest,p
        state(status='running_spmv_p1_placement')
        ctx=study.context('spmv','sb',11,100)
        result=study.placement(ctx,'training_p1_preflight','p1')
        assert result['status']=='completed',result['status']
        d=BASE/'runs'/result['name'];check=study.read(d/'placement_check.json');assert check['passed']
        part=study.read(d/'triton_evidence/manifest.json');assert part['returncode']==0 and part['output_valid']
        io.seal_inputs(BASE/'p1_training_preflight_input_integrity.json')
        state(status='passed',placement=result['name'],placement_check_sha256=sha256(d/'placement_check.json'),
            actual_partition_manifest_sha256=sha256(d/'triton_evidence/manifest.json'))
    except Exception as error:
        state(status='error',error=str(error),traceback=traceback.format_exc());raise


if __name__=='__main__':main()
