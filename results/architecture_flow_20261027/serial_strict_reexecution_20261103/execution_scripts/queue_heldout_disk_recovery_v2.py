#!/usr/bin/env python3
"""Resume the two unresolved disk interruptions, then registered unstarted cases."""
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

from flatland_benchmark import BASE, read
from lazagna_common import ROOT, sha256, utc, write_json
import run_flatland_evaluation_import_fix_v1 as evaluation

SCRIPTS = Path(__file__).resolve().parent
REMAINING = ('heldout_lstm_s21_sb_w100', 'heldout_lstm_s21_hybrid_o_w100')
PRIOR_COMPLETED = ('heldout_lstm_s23_cb_o_w100', 'heldout_lstm_s23_sb_w100',
                   'heldout_lstm_s21_cb_o_w100')


def verified_case(name, version):
    directory = BASE / 'evaluation_cases' / name
    result = read(directory / 'result.json')
    recovery = directory / ('recovery_disk_reserve_' + version)
    assert result['status'] == 'completed' and read(recovery / 'input_integrity.json')['passed'], name
    assert (recovery / 'original_result.json').exists(), name
    assert result == read(recovery / 'recovered_result.json'), name


def main():
    queue_lock = (BASE / 'heldout_recovery_queue.lock').open('a')
    fcntl.flock(queue_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    evaluation.require_disk_space()
    evaluation.register()
    for name in PRIOR_COMPLETED:
        verified_case(name, 'v1')
    for name in REMAINING:
        result = read(BASE / 'evaluation_cases' / name / 'result.json')
        assert result['status'] == 'error' and result['error'].startswith('Free space below evaluation reserve:')
    out = BASE / 'heldout_disk_recovery_queue_v2'
    out.mkdir(exist_ok=False)
    files = [Path(__file__), SCRIPTS / 'recover_evaluation_case_v2.py',
             SCRIPTS / 'recover_evaluation_case_v1.py',
             SCRIPTS / 'recover_unstarted_heldout_v1.py',
             SCRIPTS / 'run_flatland_evaluation_import_fix_v1.py',
             BASE / 'evaluation_jobs.json', BASE / 'selected_configs.json',
             BASE / 'heldout_disk_recovery_queue_v1' / 'state.json']
    bindings = {str(p): sha256(p) for p in files}
    write_json(out / 'registration.json', dict(utc=utc(), owner_pid=os.getpid(),
        remaining=REMAINING, source_and_plan_sha256=bindings, workers=1,
        free_bytes=shutil.disk_usage(BASE).free, minimum_free_bytes=evaluation.MIN_FREE_BYTES,
        reason='Disk capacity restored; resume preserved receipts in separate recovery evidence directories'))
    completed = []

    def state(status, **extra):
        write_json(out / 'state.json', dict(utc=utc(), status=status,
                   completed=completed, owner_pid=os.getpid(), **extra))

    def verify_bindings():
        for path, digest in bindings.items():
            assert sha256(path) == digest, f'queue binding changed: {path}'

    env = os.environ.copy()
    env['PYTHONPATH'] = str(SCRIPTS) + os.pathsep + str(ROOT / 'scripts')
    env['PYTHONUNBUFFERED'] = '1'
    try:
        for name in REMAINING:
            verify_bindings()
            evaluation.require_disk_space()
            state('running_case', case=name)
            with (out / (name + '.log')).open('x') as log:
                subprocess.run([sys.executable, str(SCRIPTS / 'recover_evaluation_case_v2.py'), name],
                               cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            verified_case(name, 'v2')
            completed.append(name)
        verify_bindings()
        evaluation.require_disk_space()
        state('running_unstarted')
        with (out / 'unstarted.log').open('x') as log:
            subprocess.run([sys.executable, str(SCRIPTS / 'recover_unstarted_heldout_v1.py'),
                            '--workers', '1'], cwd=ROOT, env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True)
        state('heldout_recovery_complete')
    except BaseException as error:
        state('needs_diagnosis', error=str(error), traceback=traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
