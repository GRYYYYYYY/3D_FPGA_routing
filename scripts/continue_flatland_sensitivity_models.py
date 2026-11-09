#!/usr/bin/env python3
"""Prepare the remaining W300 models after six-worker training has finished."""
import fcntl
import os
import subprocess
import sys
import time

from flatland_benchmark import BASE,read
from lazagna_common import ROOT,sha256,utc,write_json
from flatland_low_concurrency_gate import ready as low_concurrency_ready


def state(**fields):
    write_json(BASE/'sensitivity_model_continuation_state.json',dict(utc=utc(),pid=os.getpid(),**fields))


def main():
    locks=[]
    for label in ['sensitivity_model_continuation','evaluation_runner','serial_runner']:
        handle=(BASE/(label+'.lock')).open('a');fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(handle)
    protocol=BASE/'sensitivity_model_continuation_protocol.json';assert not protocol.exists()
    wrapper=ROOT/'scripts/prepare_flatland_without_gc.py';wrapper_hash=sha256(wrapper)
    write_json(protocol,dict(utc=utc(),source_sha256=sha256(__file__),wrapper_sha256=wrapper_hash,
        gate_source_sha256=sha256(ROOT/'scripts/flatland_low_concurrency_gate.py'),
        sizes=[80,125],width=300,
        gate='Wait for all three softmax cases to complete their audit; the remaining attention cases and subsequent frozen training batches use at most three VPR slots.',
        concurrency='One preparation at a time: at most two graph VPRs plus three training VPRs plus one P1 preflight. Hold evaluation and serial locks until finished.'))
    try:
        while not low_concurrency_ready():
            state(status='waiting_for_training_to_need_at_most_three_slots');time.sleep(20)
        for size in [40,60]:
            while not (BASE/'benchmark_models'/f'n{size}_w300'/'manifest.json').exists():
                failure=BASE/'preparation_wrapper_runs'/f'n{size}_w300'/'failure.json'
                if failure.exists():raise RuntimeError(f'Existing W300 model failed: {failure}')
                state(status='waiting_existing_w300_models',size=size);time.sleep(20)
        for size in [80,125]:
            assert sha256(wrapper)==wrapper_hash
            state(status='preparing',size=size,width=300)
            with (BASE/f'benchmark_model_n{size}_w300_console.log').open('x') as log:
                subprocess.run([sys.executable,str(wrapper),'--size',str(size),'--width','300'],
                    cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        manifests={}
        for size in [40,60,80,125]:
            path=BASE/'benchmark_models'/f'n{size}_w300'/'manifest.json'
            assert read(path)['status']=='ready';manifests[str(path)]=sha256(path)
        state(status='completed',model_manifests=manifests)
    except Exception as error:
        state(status='error',error=str(error));raise


if __name__=='__main__':main()
