#!/usr/bin/env python3
"""Execute only registered training cases, never select using held-out results."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import fcntl
import json
from pathlib import Path
import shutil
import traceback

import flatland_benchmark as study
import flatland_experiment_io as io
from lazagna_common import ROOT, sha256, utc, write_json

BASE = study.BASE
MIN_FREE_BYTES = 80 * 1024**3


def require_disk_space():
    free = shutil.disk_usage(BASE).free
    if free < MIN_FREE_BYTES:
        raise RuntimeError(f'Free space below training reserve: {free} bytes; minimum {MIN_FREE_BYTES}')


def require_observation(receipt):
    if receipt['status'] in ('thread_constraint_violated', 'thread_observation_missing',
                             'input_integrity_failed', 'launch_failed'):
        raise RuntimeError(f"Infrastructure failure in preserved receipt {receipt['name']}: {receipt['status']}")


def register():
    p = BASE/'training_jobs.json'
    protocol = study.read(BASE/'benchmark_protocol.json')
    jobs=[]
    for circuit in protocol['training']:
        for family in protocol['architectures']:
            for router,variant,config in [('A0',None,None)]+[
                ('R1',v,c) for c in range(8) for v in protocol['tuning']['variants']]:
                jobs.append(dict(circuit=circuit,family=family,seed=11,placement='p0',
                    router=router,variant=variant,config=config,width=100))
    assert sum(x['router']=='R1' for x in jobs)==576
    data=dict(protocol_sha256=sha256(BASE/'benchmark_protocol.json'),jobs=jobs,
        resource_amendment_sha256=sha256(BASE/'execution_resource_amendment.json'),
        source_sha256={str((Path(__file__).parent/f) if (Path(__file__).parent/f).exists() else (ROOT/'scripts'/f)):sha256((Path(__file__).parent/f) if (Path(__file__).parent/f).exists() else (ROOT/'scripts'/f)) for f in [
            'run_flatland_training.py','flatland_benchmark.py','flatland_experiment_io.py','process_tree_observer.py',
            'check_route.py','compare_lazagna_graphs.py','run_flatland_pack_census.py',
            'prepare_flatland_benchmark_models.py','select_flatland_configs.py']})
    if p.exists():
        old=study.read(p)
        for key,value in data.items():assert old[key]==value, f'Training registration changed: {key}'
    else:write_json(p,dict(utc=utc(),**data))
    return data


def run(pair):
    circuit,family=pair
    directory=BASE/'training_cases'/f'{circuit}_{family}'
    directory.mkdir(parents=True,exist_ok=True)
    result_path=directory/'result.json'
    if result_path.exists():
        previous=study.read(result_path)
        assert previous['status']=='completed',f'Prior failed/interrupted case requires a dated recovery decision: {directory}'
        return previous
    write_json(directory/'state.json',dict(utc=utc(),status='starting',circuit=circuit,family=family))
    receipts=[]
    try:
        ctx=study.context(circuit,family,11)
        require_disk_space()
        placed=study.placement(ctx,'training','p0')
        require_observation(placed)
        if placed['status']!='completed':
            result=dict(utc=utc(),status='placement_failed',receipt=placed['name'],
                registered_routes=33,unattempted_routes=33,reason='Shared P0 fixture failed; retain all planned descendants')
            write_json(result_path,result);return result
        specifications=[('A0',None,None)]+[('R1',v,c) for c in range(8) for v in ctx['protocol']['tuning']['variants']]
        for router,variant,config in specifications:
            require_disk_space()
            receipt=study.route(ctx,'training','p0',router,variant,config);receipts.append(receipt)
            require_observation(receipt)
            write_json(directory/'state.json',dict(utc=utc(),status='routing',circuit=circuit,family=family,
                completed_attempts=len(receipts),registered_routes=len(specifications),last=receipt['name']))
        validation=study.audit_batch(ctx,receipts,directory/'audit_summary.json')
        result=dict(utc=utc(),status='completed',circuit=circuit,family=family,size=ctx['size'],
            registered_routes=33,legal_routes=validation['legal_count'],failed_routes=validation['failed_count'])
    except Exception as error:
        result=dict(utc=utc(),status='error',circuit=circuit,family=family,attempted_routes=len(receipts),
            error=str(error),traceback=traceback.format_exc())
    write_json(result_path,result)
    print('training case',circuit,family,result['status'],flush=True)
    return result


def execute_cases(pairs, workers, runner=run):
    """Drain active cases but retain every not-yet-submitted case on error."""
    results=[]; submitted=0; stopped=False
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending={}
        def submit():
            nonlocal submitted
            pair=pairs[submitted];submitted+=1;pending[pool.submit(runner,pair)]=pair
        for _ in range(min(workers,len(pairs))):submit()
        while pending:
            done,_=wait(pending,return_when=FIRST_COMPLETED)
            for future in done:
                pair=pending.pop(future)
                try: result=future.result()
                except Exception as error:
                    result=dict(status='error',circuit=pair[0],family=pair[1],error=str(error),traceback=traceback.format_exc())
                results.append(result)
                if result['status']!='completed':stopped=True
            if not stopped:
                while len(pending)<workers and submitted<len(pairs):submit()
    return results,pairs[submitted:]


def main(circuits, workers=6):
    lock=(BASE/'training_runner.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    register();protocol=study.read(BASE/'benchmark_protocol.json')
    assert set(circuits)<=set(protocol['training'])
    # Check readiness before creating per-case state; never silently turn a
    # missing preparatory artifact into an algorithm routing failure.
    for c in circuits:
        for f in protocol['architectures']:study.context(c,f,11)
    pairs=[(c,f) for c in circuits for f in protocol['architectures']]
    assert 1 <= workers <= 6
    results,unstarted=execute_cases(pairs,workers)
    invocation=BASE/'training_invocations';invocation.mkdir(exist_ok=True)
    name='_'.join(circuits)
    output=invocation/f'{name}.json'
    if output.exists():raise FileExistsError(output)
    write_json(output,dict(utc=utc(),circuits=circuits,workers=workers,results=results,unstarted_pairs=unstarted,
        complete_suite=len(list((BASE/'training_cases').glob('*/result.json')))==18))
    io.seal_inputs(invocation/f'{name}_input_integrity.json')
    if any(x['status']!='completed' for x in results):raise RuntimeError('Training cases need diagnosis; see preserved receipts')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--circuits',nargs='+',required=True)
    p.add_argument('--workers',type=int,default=6);args=p.parse_args()
    main(args.circuits,args.workers)
