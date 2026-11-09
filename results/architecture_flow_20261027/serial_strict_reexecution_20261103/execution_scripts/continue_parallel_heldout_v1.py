#!/usr/bin/env python3
"""Resume immutable registered jobs after a controlled, case-complete drain."""
from contextlib import ExitStack
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from flatland_benchmark import BASE, read
from lazagna_common import ROOT, sha256, utc, write_json
import continue_strict_study as original
import continue_after_heldout_recovery_v1 as downstream
import run_flatland_evaluation_import_fix_v1 as evaluation
import flatland_experiment_io as io

SCRIPTS = Path(__file__).resolve().parent
AMENDMENT = BASE / 'parallel_resumption_amendment_20261106.json'
DIRECTORY = BASE / 'parallel_continuation_v1'


def seal_drained_invocation(output):
    """Reconstruct the interrupted invocation's immutable-input seal from receipts.

    No interrupted result or original invocation file is overwritten. Each
    retained file identity must agree with every original receipt using it.
    """
    registration_path = BASE / 'evaluation_invocations/heldout_unstarted_recovery_v1_1_registration.json'
    registration = read(registration_path)
    completed, unstarted, inputs, run_names = [], [], {}, set()
    for job in registration['jobs']:
        name = f"heldout_{job['circuit']}_s{job['seed']}_{job['family']}_w{job['width']}"
        case = BASE / 'evaluation_cases' / name
        result_path = case / 'result.json'
        if not result_path.exists():
            assert not case.exists(), f'Incomplete case directory after drain: {case}'
            unstarted.append(job)
            continue
        result = read(result_path)
        assert result['status'] == 'completed' and result['job'] == job, name
        completed.append(dict(case=name, result_sha256=sha256(result_path)))
        size = read(BASE / 'capacity_selection.json')['circuits'][job['circuit']]['size']
        for flow, row in result['flows'].items():
            run_names.add(f"heldout_{job['circuit']}_s{job['seed']}_{job['family']}_n{size}_w{job['width']}_{flow}_place")
            if row['status'] == 'completed':
                audit = read(case / (flow + '_audit_summary.json'))
                assert audit['passed']
                assert {r['name'] for group in ('legal', 'failed') for r in audit[group]} == set(row['roles'].values())
                run_names.update(row['roles'].values())
            else:
                assert row['status'] == 'placement_failed'
    for name in sorted(run_names):
        manifest = read(BASE / 'runs' / name / 'manifest.json')
        evaluation.require_observation(manifest)
        assert manifest['status'] in ('completed', 'failed', 'timeout'), name
        for path, info in manifest['shared_inputs'].items():
            if path in inputs:
                assert inputs[path] == info, f'Inconsistent frozen-input identities: {path}'
            inputs[path] = info
    checked = {}
    for path, info in inputs.items():
        before = io.identity(path)
        assert before == tuple(info['stat_identity']), f'Input identity changed after recorded attempt: {path}'
        digest = sha256(path)
        assert io.identity(path) == before and digest == info['sha256'], path
        checked[path] = dict(sha256=digest, stat_identity=before, passed=True)
    write_json(output, dict(utc=utc(), passed=True,
        registration_sha256=sha256(registration_path), completed=completed, unstarted_jobs=unstarted,
        checked_runs=sorted(run_names), inputs=checked,
        qualification='Post-drain independent reconstruction of the missing final seal from preserved terminal receipts; not an original supervisor-generated seal. Original interruption and registration are retained.'))


def main():
    owner_lock = (BASE / 'parallel_continuation.lock').open('a')
    fcntl.flock(owner_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    amendment = read(AMENDMENT)
    assert amendment['workers'] == 3
    assert not DIRECTORY.exists()
    DIRECTORY.mkdir()
    bindings = dict(read(BASE / 'post_heldout_continuation_v1/registration.json')['source_and_protocol_sha256'])
    original.verify(bindings)
    files = [Path(__file__), AMENDMENT, SCRIPTS / 'test_controlled_drain_v1.py',
             BASE / 'controlled_drain_validation_20261106.json']
    bindings.update({str(p): sha256(p) for p in files})
    assert read(BASE / 'controlled_drain_validation_20261106.json')['passed']
    stages = [(label, args[:-1] + ['3'] if label == 'width300' else args)
              for label, args in downstream.STAGES]
    downstream.STAGES = stages
    write_json(DIRECTORY / 'registration.json', dict(utc=utc(), workers=3,
        source_and_protocol_sha256=bindings, predecessor_processes=amendment['processes'], stages=stages,
        scope='Only scheduling concurrency changes. Algorithm, seeds, inputs, budgets and all registered cases remain fixed. Serial timing remains exclusive within the study.'))
    completed = []

    def state(status, **fields):
        write_json(DIRECTORY / 'state.json', dict(utc=utc(), supervisor_pid=os.getpid(),
            status=status, completed_stages=completed, **fields))

    env = os.environ.copy()
    env['PYTHONPATH'] = str(SCRIPTS) + os.pathsep + str(ROOT / 'scripts')
    env['PYTHONUNBUFFERED'] = '1'
    try:
        state('waiting_controlled_drain')
        for process in amendment['processes']:
            while original.identity(process['pid']) == process['start_ticks']:
                time.sleep(20)
        signal_receipt = read(BASE / 'parallel_resumption_signal_20261106.json')
        assert signal_receipt['pid'] == amendment['drain_pid'] and signal_receipt['signal'] == 'SIGINT'
        log = BASE / 'heldout_disk_recovery_queue_v2/unstarted.log'
        assert 'KeyboardInterrupt' in log.read_text(errors='replace')
        assert read(BASE / 'heldout_disk_recovery_queue_v2/state.json')['status'] == 'needs_diagnosis'
        assert read(BASE / 'post_heldout_continuation_v1/state.json')['status'] == 'needs_diagnosis'
        # Keep sole queue ownership while subordinate commands take their study locks.
        with ExitStack() as queue_locks:
            for name in ('heldout_recovery_queue.lock', 'post_heldout_continuation.lock'):
                handle = queue_locks.enter_context((BASE / name).open('a'))
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with ExitStack() as preflight_locks:
                for name in ('strict_continuation.lock', 'serial_runner.lock', 'training_runner.lock', 'evaluation_runner.lock'):
                    handle = preflight_locks.enter_context((BASE / name).open('a'))
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                state('verifying_drained_invocation')
                original.verify(bindings)
                original.quiescent()
                original.training_gate()
                evaluation.register()
                seal_drained_invocation(DIRECTORY / 'drained_input_integrity.json')
                assert not (BASE / 'evaluation_invocations/heldout_unstarted_recovery_v1_2_registration.json').exists()
            evaluation.require_disk_space()
            state('running_heldout', workers=3)
            with (DIRECTORY / 'heldout.log').open('x') as output:
                subprocess.run([sys.executable, str(SCRIPTS / 'recover_unstarted_heldout_v1.py'),
                                '--workers', '3'], cwd=ROOT, env=env, stdout=output,
                               stderr=subprocess.STDOUT, check=True)
            invocation = read(BASE / 'evaluation_invocations/heldout_unstarted_recovery_v1_2.json')
            assert invocation['workers'] == 3 and not invocation['unstarted_jobs']
            assert len(invocation['results']) == invocation['planned_cases'] == 78
            assert all(r['status'] == 'completed' for r in invocation['results'])
            assert read(BASE / 'evaluation_invocations/heldout_unstarted_recovery_v1_2_input_integrity.json')['passed']
            completed.append('heldout_resume')
            strict_lock = queue_locks.enter_context((BASE / 'strict_continuation.lock').open('a'))
            fcntl.flock(strict_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            original.quiescent()
            count = downstream.heldout_gate()
            write_json(DIRECTORY / 'heldout_gate.json', dict(utc=utc(), passed=True, cases=count))
            downstream.execute_stages(DIRECTORY, bindings, state, completed)
            state('awaiting_scientific_and_integrity_closure', report=str(BASE / 'report.html'))
    except BaseException as error:
        state('needs_diagnosis', error=str(error), traceback=traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
