#!/usr/bin/env python3
"""Continue the frozen training budget after the current small-device batch."""
import fcntl
import os
import subprocess
import sys
import time

from flatland_benchmark import BASE,read
from lazagna_common import ROOT,sha256,utc,write_json


def state(**fields):write_json(BASE/'training_continuation_state.json',dict(utc=utc(),supervisor_pid=os.getpid(),**fields))


def wait_for_integrity(label):
    result=BASE/'training_invocations'/f'{label}.json'
    integrity=BASE/'training_invocations'/f'{label}_input_integrity.json'
    while not integrity.exists():
        if result.exists() and any(r['status']!='completed' for r in read(result)['results']):
            raise RuntimeError(f'Previous batch needs diagnosis: {result}')
        state(status='waiting_training_batch',batch=label);time.sleep(20)
    assert read(integrity)['passed']
    assert all(r['status']=='completed' for r in read(result)['results'])


def wait_for_models(circuits):
    sizes=sorted({read(BASE/'capacity_selection.json')['circuits'][c]['size'] for c in circuits})
    while True:
        missing=[n for n in sizes if not (BASE/'benchmark_models'/f'n{n}_w100'/'manifest.json').exists()]
        active=[]
        for p in (BASE/'runs').glob('controlled_graph_*/manifest.json'):
            m=read(p)
            if m['status'] in ('starting','running'):active.append(m['name'])
        for n in missing:
            p=BASE/f'benchmark_model_n{n}_w100_console.log'
            if p.exists():
                with p.open('rb') as stream:
                    stream.seek(max(0,p.stat().st_size-4096));tail=stream.read().decode(errors='replace')
                if 'Traceback (most recent call last)' in tail:raise RuntimeError(f'Model preparation failed: {p}')
        if not missing and not active:return
        state(status='waiting_models',circuits=circuits,missing_sizes=missing,active_graph_jobs=active);time.sleep(20)


def main():
    lock=(BASE/'training_continuation.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    protocol=BASE/'training_continuation_protocol.json'
    assert not protocol.exists()
    batches=[(['attention_layer','softmax'],6),(['bnn'],3),(['gemm_layer'],3)]
    write_json(protocol,dict(utc=utc(),source_sha256=sha256(__file__),initial_batch='eltwise_layer_spmv',
        batches=[dict(circuits=c,workers=w) for c,w in batches],
        contract='Wait for previous input-integrity seal and ready physical models; stop on infrastructure error; never start held-out runs or change registered hyperparameters'))
    try:
        wait_for_integrity('eltwise_layer_spmv')
        for circuits,workers in batches:
            wait_for_models(circuits);state(status='running_training',circuits=circuits,workers=workers)
            subprocess.run([sys.executable,str(ROOT/'scripts/run_flatland_training.py'),
                '--circuits',*circuits,'--workers',str(workers)],cwd=ROOT,check=True)
            wait_for_integrity('_'.join(circuits))
        state(status='selecting_using_training_only')
        subprocess.run([sys.executable,str(ROOT/'scripts/select_flatland_configs.py')],cwd=ROOT,check=True)
        state(status='training_and_selection_complete',selection=str(BASE/'selected_configs.json'))
    except Exception as error:
        state(status='error',error=str(error));raise


if __name__=='__main__':main()
