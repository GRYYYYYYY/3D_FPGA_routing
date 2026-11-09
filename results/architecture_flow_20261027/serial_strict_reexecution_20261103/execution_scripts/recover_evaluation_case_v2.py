#!/usr/bin/env python3
"""Resume disk-reserve recovery in a new evidence directory, preserving v1."""
import argparse
from contextlib import ExitStack
import fcntl
import json
import os
from pathlib import Path
import shutil
import time

import flatland_benchmark as study
import run_flatland_evaluation_import_fix_v1 as evaluation
from lazagna_common import sha256, utc, write_json

BASE = study.BASE

def main(name):
    with ExitStack() as locks:
        for lockname in ('strict_continuation.lock', 'serial_runner.lock', 'training_runner.lock', 'evaluation_runner.lock'):
            lock = locks.enter_context((BASE / lockname).open('a'))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return recover_locked(name)

def recover_locked(name):
    case = BASE / 'evaluation_cases' / name
    result_path = case / 'result.json'
    original = study.read(result_path)
    assert original['status'] == 'error' and original['error'].startswith('Free space below evaluation reserve:')
    job = original['job']
    assert name == f"{job['phase']}_{job['circuit']}_s{job['seed']}_{job['family']}_w{job['width']}"
    plan = study.read(BASE / 'evaluation_jobs.json')
    assert job in plan['jobs']
    assert sha256(BASE / 'benchmark_protocol.json') == plan['protocol_sha256']
    assert sha256(BASE / 'selected_configs.json') == plan['selection_sha256']
    assert sha256(BASE / 'execution_resource_amendment.json') == plan['resource_amendment_sha256']
    for path, expected in plan['shared_source_sha256'].items():
        assert sha256(Path(path)) == expected, 'Frozen shared implementation changed: ' + path
    registration = study.read(case / 'registration.json')
    assert registration['jobs_sha256'] == sha256(BASE / 'evaluation_jobs.json')
    assert registration['selection_sha256'] == sha256(BASE / 'selected_configs.json')
    prior = case / 'recovery_disk_reserve_v1'
    prior_hashes = {str(p): sha256(p) for p in sorted(prior.rglob('*')) if p.is_file()}
    if prior.exists():
        old_registration = study.read(prior / 'registration.json')
        assert old_registration['original_sha256'] == sha256(result_path)
        assert old_registration['jobs_sha256'] == sha256(BASE / 'evaluation_jobs.json')
        assert old_registration['job'] == job
        assert old_registration['source_sha256'] == sha256(Path(__file__).with_name('recover_evaluation_case_v1.py'))
        assert sha256(prior / 'original_result.json') == sha256(result_path)
    recovery = case / 'recovery_disk_reserve_v2'
    recovery.mkdir(exist_ok=False)
    archived = recovery / 'original_result.json'
    if archived.exists():
        assert sha256(archived) == sha256(result_path)
    else:
        shutil.copy2(result_path, archived)
        assert sha256(archived) == sha256(result_path)
    write_json(recovery / 'registration.json', dict(utc=utc(), original_sha256=sha256(archived),
        jobs_sha256=sha256(BASE / 'evaluation_jobs.json'), source_sha256=sha256(__file__),
        prior_evidence_sha256=prior_hashes, job=job))
    ctx = study.context(job['circuit'], job['family'], job['seed'], job['width'])
    rows = dict(original.get('flows', {}))
    checkpoint = recovery / 'completed_flows.json'
    if (prior / 'completed_flows.json').exists():
        saved = study.read(prior / 'completed_flows.json')['flows']
        for flow, row in rows.items():
            assert saved.get(flow) == row
        rows = saved
    for flow, arms in job['roles'].items():
        if flow in rows:
            continue
        # Detect partial finalization before starting any additional solver.
        for suffix in ('_audit_summary.json', '_input_compaction.json'):
            if (case / (flow + suffix)).exists():
                raise RuntimeError('Partial audit/compaction requires reconciliation: ' + str(case))
        for spec in arms.values():
            arm = spec['router'].lower() if spec['router'] != 'R1' else f"{spec['variant']}_c{spec['config']}"
            run_name = study.prefix(ctx, job['phase'], flow) + '_' + arm
            if (BASE / 'runs' / run_name / 'independent_audit.json').exists():
                raise RuntimeError('Existing independent audit requires reconciliation: ' + run_name)
        evaluation.require_disk_space()
        place = study.placement(ctx, job['phase'], flow)
        evaluation.require_observation(place)
        if place['status'] != 'completed':
            rows[flow] = dict(status='placement_failed', receipt=place['name'], unattempted_roles=list(arms),
                              reason='Shared placement failed; all planned descendant roles retained')
            continue
        unique = {}; refs = {}
        for role, spec in arms.items():
            key = tuple(spec[k] for k in ('router', 'variant', 'config'))
            if key not in unique:
                evaluation.require_disk_space()
                unique[key] = study.route(ctx, job['phase'], flow, *key)
                evaluation.require_observation(unique[key])
            refs[role] = unique[key]['name']
            write_json(recovery / 'state.json', dict(utc=utc(), flow=flow, roles=refs))
        audit = case / (flow + '_audit_summary.json')
        compaction = case / (flow + '_input_compaction.json')
        if audit.exists() or compaction.exists():
            raise RuntimeError('Partial audit/compaction requires manual reconciliation: ' + str(case))
        # Avoid overwriting evidence left by a prior incomplete audit.
        for receipt in unique.values():
            if (BASE / 'runs' / receipt['name'] / 'independent_audit.json').exists():
                raise RuntimeError('Existing independent audit requires reconciliation: ' + receipt['name'])
        validation = study.audit_batch(ctx, list(unique.values()), audit)
        evaluation.compact_completed_route_inputs(list(unique.values()), compaction)
        rows[flow] = dict(status='completed', roles=refs, registered_roles=len(arms),
                          unique_runs=len(unique), legal_runs=validation['legal_count'],
                          failed_runs=validation['failed_count'])
        write_json(recovery / 'completed_flows.json', dict(utc=utc(), flows=rows))
    for path, digest in prior_hashes.items():
        assert sha256(path) == digest, 'Prior recovery evidence changed: ' + path
    evaluation.io.seal_inputs(recovery / 'input_integrity.json')
    result = dict(utc=utc(), status='completed', job=job, flows=rows,
                  recovery=dict(original_result_sha256=sha256(archived), source_sha256=sha256(__file__), evidence_directory=str(recovery)))
    write_json(recovery / 'recovered_result.json', result)
    assert sha256(archived) == sha256(result_path)
    # Publish only after all registered roles and audits are resolved; preserve original in recovery/.
    temp = case / '.recovered_result_v2.json'
    if temp.exists(): raise FileExistsError(temp)
    write_json(temp, result)
    os.replace(temp, result_path)
    print('recovered', name, flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('case'); args = parser.parse_args()
    main(args.case)
