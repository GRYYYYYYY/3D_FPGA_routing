#!/usr/bin/env python3
"""Execute the separately registered P1 balance sensitivity sequentially."""
import argparse
import fcntl
import shutil
import traceback

import flatland_benchmark as study
import flatland_experiment_io as io
from check_flatland_partition_balance import audit
from lazagna_common import ROOT, sha256, utc, write_json

BASE = study.BASE
MIN_FREE_BYTES = 80*1024**3


def require_disk_space():
    free=shutil.disk_usage(BASE).free
    if free<MIN_FREE_BYTES:raise RuntimeError(f'Free space below balance reserve: {free} bytes; minimum {MIN_FREE_BYTES}')


def require_observation(receipt):
    if receipt['status'] in ('thread_constraint_violated','thread_observation_missing',
                             'input_integrity_failed','launch_failed'):
        raise RuntimeError(f"Infrastructure failure in preserved receipt {receipt['name']}: {receipt['status']}")


def placement(ctx, stage, value):
    # This driver is deliberately single-threaded. The scoped adapter changes
    # only this process's call arguments, never the frozen shared source files.
    original = io.run

    def adapted(name, command, **kwargs):
        assert kwargs['tags']['operation'] == 'placement'
        assert kwargs['tags']['stage'] == stage
        assert '--partition_imbalance_ratio' not in command
        return original(name, [*command, '--partition_imbalance_ratio', str(value)], **kwargs)

    io.run = adapted
    try:
        return study.placement(ctx, stage, 'p1')
    finally:
        io.run = original


def run(job, selection, registration):
    stage = 'balance_' + job['placement_arm']
    ctx = study.context(job['circuit'], job['family'], job['seed'], job['width'])
    directory = BASE/'balance_cases'/study.prefix(ctx, stage, 'p1')
    directory.mkdir(parents=True, exist_ok=True)
    path = directory/'result.json'
    if path.exists():
        raise FileExistsError(f'Existing case requires explicit evidence review: {path}')
    write_json(directory/'registration.json', dict(job=job, registration_sha256=registration))
    result = dict(utc=utc(), job=job, status='running')
    try:
        require_disk_space()
        p = placement(ctx, stage, job['partition_argument'])
        require_observation(p)
        result['placement'] = p['name']
        if p['status'] != 'completed':
            result.update(status='placement_failed', unattempted_roles=job['routers'])
        else:
            evidence = BASE/'runs'/p['name']/'triton_evidence'
            check = audit(evidence/'triton_hypergraph.hgr',
                          evidence/'triton_hypergraph.hgr.part.2', 2, job['partition_argument'])
            write_json(directory/'balance_audit.json', check)
            result['balance'] = check
            if job['placement_arm'] == 'relative3' and not check['balanced']:
                result.update(status='balance_failed', unattempted_roles=job['routers'])
            else:
                chosen = selection['selections'][job['family']]['R1']
                routes = []
                for router in job['routers']:
                    require_disk_space()
                    routes.append(study.route(ctx, stage, 'p1', router,
                        chosen['variant'] if router == 'R1' else None,
                        chosen['config'] if router == 'R1' else None))
                    require_observation(routes[-1])
                result['roles'] = {r['tags']['router']: r['name'] for r in routes}
                result['route_audit'] = study.audit_batch(ctx, routes, directory/'route_audit.json')
                result['status'] = 'completed'
    except Exception as error:
        result.update(status='error', error=str(error), traceback=traceback.format_exc())
    write_json(path, result)
    return result


def main(circuits):
    locks = []
    for name in ['serial_runner.lock', 'training_runner.lock', 'evaluation_runner.lock']:
        lock = (BASE/name).open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(lock)
    protocol_path = BASE/'partition_balance_sensitivity_protocol.json'
    protocol = study.read(protocol_path)
    assert protocol['parent_protocol_sha256'] == sha256(BASE/'benchmark_protocol.json')
    selection = study.read(BASE/'selected_configs.json')
    assert selection['status'] == 'frozen_before_heldout'
    assert selection['protocol_sha256'] == protocol['parent_protocol_sha256']
    assert selection['training_jobs_sha256'] == sha256(BASE/'training_jobs.json')
    sources = study.read(BASE/'training_jobs.json')['source_sha256']
    for path, digest in sources.items():
        assert sha256(path) == digest, path
    binding = dict(protocol_sha256=sha256(protocol_path),
        selection_sha256=sha256(BASE/'selected_configs.json'), source_sha256=sha256(__file__),
        balance_checker_sha256=sha256(ROOT/'scripts/check_flatland_partition_balance.py'),
        shared_source_sha256=sources, minimum_free_bytes=MIN_FREE_BYTES, jobs=protocol['jobs'])
    registration = BASE/'partition_balance_sensitivity_jobs.json'
    if registration.exists():
        assert study.read(registration) == binding
    else:
        write_json(registration, binding)
    jobs = protocol['jobs']
    if circuits:
        assert set(circuits) <= {j['circuit'] for j in jobs}
        jobs = [j for j in jobs if j['circuit'] in circuits]
    for job in jobs:
        study.context(job['circuit'], job['family'], job['seed'], job['width'])
    results = []
    for job in jobs:
        result = run(job, selection, sha256(registration))
        results.append(result)
        if result['status'] == 'error':
            break
    directory = BASE/'balance_invocations'
    directory.mkdir(exist_ok=True)
    stem = '_'.join(circuits or ['all'])
    output = directory/(stem+'.json')
    assert not output.exists()
    write_json(output, dict(utc=utc(), results=results, unstarted_jobs=jobs[len(results):]))
    io.seal_inputs(directory/(stem+'_input_integrity.json'))
    assert all(r['status'] != 'error' for r in results), 'Preserved infrastructure failure requires diagnosis'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--circuits', nargs='+')
    main(parser.parse_args().circuits)
