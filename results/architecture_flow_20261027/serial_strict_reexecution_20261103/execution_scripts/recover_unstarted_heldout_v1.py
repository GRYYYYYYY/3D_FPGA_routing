#!/usr/bin/env python3
"""Run previously unstarted registered heldout cases, preserving old invocation."""
import argparse
from contextlib import ExitStack
import fcntl
from pathlib import Path

import flatland_benchmark as study
import run_flatland_evaluation_import_fix_v1 as evaluation
from lazagna_common import sha256, utc, write_json

BASE = study.BASE

def main(workers):
    assert 1 <= workers <= 6
    with ExitStack() as stack:
        for name in ('strict_continuation.lock', 'serial_runner.lock', 'training_runner.lock', 'evaluation_runner.lock'):
            lock = stack.enter_context((BASE/name).open('a'))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        plan = evaluation.register()
        prior = BASE/'evaluation_invocations'/'heldout_all_s0.json'
        invocation = study.read(prior)
        assert invocation['phase'] == 'heldout'
        jobs = invocation['unstarted_jobs']
        assert jobs and all(j in plan['jobs'] and j['phase'] == 'heldout' for j in jobs)
        assert len({(j['circuit'], j['seed'], j['family'], j['width']) for j in jobs}) == len(jobs)
        for j in jobs:
            name = f"heldout_{j['circuit']}_s{j['seed']}_{j['family']}_w{j['width']}"
            result = BASE/'evaluation_cases'/name/'result.json'
            if result.exists():
                old = study.read(result)
                assert old['status'] == 'completed' and old['job'] == j, f'unresolved earlier attempt: {result}'
        folder = BASE/'evaluation_invocations'
        index = 1
        while ((folder/f'heldout_unstarted_recovery_v1_{index}.json').exists() or
               (folder/f'heldout_unstarted_recovery_v1_{index}_registration.json').exists()):
            index += 1
        output = folder/f'heldout_unstarted_recovery_v1_{index}.json'
        registration = folder/f'heldout_unstarted_recovery_v1_{index}_registration.json'
        write_json(registration, dict(utc=utc(), previous_invocation_sha256=sha256(prior),
                   evaluation_jobs_sha256=sha256(BASE/'evaluation_jobs.json'), source_sha256=sha256(__file__),
                   workers=workers, jobs=jobs))
        results, unstarted = evaluation.execute_cases(jobs, workers)
        write_json(output, dict(utc=utc(), phase='heldout', workers=workers, results=results,
                   planned_cases=len(jobs), unstarted_jobs=unstarted, registration_sha256=sha256(registration)))
        evaluation.io.seal_inputs(folder/f'heldout_unstarted_recovery_v1_{index}_input_integrity.json')
        if unstarted or any(r['status'] != 'completed' for r in results):
            raise RuntimeError('Unstarted recovery stopped; retained invocation requires diagnosis')
        print('previously unstarted heldout cases resolved', len(results), flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--workers', type=int, default=1)
    main(parser.parse_args().workers)
