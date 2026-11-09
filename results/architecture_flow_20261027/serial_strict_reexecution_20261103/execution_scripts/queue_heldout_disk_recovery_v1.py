#!/usr/bin/env python3
"""Continue registered disk-reserve recovery after the current owner exits."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from flatland_benchmark import BASE, read
from lazagna_common import ROOT, sha256, utc, write_json
from continue_strict_study import identity

SCRIPTS = Path(__file__).resolve().parent
CURRENT = 'heldout_lstm_s23_sb_w100'
REMAINING = ('heldout_lstm_s21_cb_o_w100', 'heldout_lstm_s21_sb_w100',
             'heldout_lstm_s21_hybrid_o_w100')

def verified_case(name):
    directory = BASE / 'evaluation_cases' / name
    result = read(directory / 'result.json')
    seal = read(directory / 'recovery_disk_reserve_v1' / 'input_integrity.json')
    assert result['status'] == 'completed' and seal['passed'], name
    assert (directory / 'recovery_disk_reserve_v1' / 'original_result.json').exists(), name

def main(pid, start_ticks):
    queue_lock = (BASE / 'heldout_recovery_queue.lock').open('a')
    fcntl.flock(queue_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert identity(pid) == start_ticks, 'registered recovery process is not live'
    cmdline = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    assert any(x.endswith(b'/recover_evaluation_case_v1.py') for x in cmdline)
    assert CURRENT.encode() in cmdline
    out = BASE / 'heldout_disk_recovery_queue_v1'
    out.mkdir(exist_ok=False)
    files = [Path(__file__), SCRIPTS / 'recover_evaluation_case_v1.py',
             SCRIPTS / 'recover_unstarted_heldout_v1.py',
             SCRIPTS / 'run_flatland_evaluation_import_fix_v1.py',
             BASE / 'evaluation_jobs.json', BASE / 'selected_configs.json']
    bindings = {str(p): sha256(p) for p in files}
    write_json(out / 'registration.json', dict(utc=utc(), owner_pid=pid,
        owner_start_ticks=start_ticks, current=CURRENT, remaining=REMAINING,
        source_and_plan_sha256=bindings, workers=1))
    completed = []
    def state(status, **extra):
        write_json(out / 'state.json', dict(utc=utc(), status=status,
                   completed=completed, **extra))
    def verify_bindings():
        for path, digest in bindings.items():
            assert sha256(path) == digest, f'queue binding changed: {path}'
    env = os.environ.copy()
    env['PYTHONPATH'] = str(SCRIPTS) + os.pathsep + str(ROOT / 'scripts')
    env['PYTHONUNBUFFERED'] = '1'
    try:
        state('waiting_for_owner', owner_pid=pid, owner_start_ticks=start_ticks)
        while identity(pid) == start_ticks:
            time.sleep(20)
        verify_bindings()
        verified_case(CURRENT)
        for name in REMAINING:
            verify_bindings()
            assert read(BASE / 'evaluation_cases' / name / 'result.json')['status'] == 'error'
            state('running_case', case=name)
            with (out / (name + '.log')).open('x') as log:
                subprocess.run([sys.executable, str(SCRIPTS / 'recover_evaluation_case_v1.py'), name],
                               cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            verified_case(name)
            completed.append(name)
        verify_bindings()
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
    main(int(sys.argv[1]), int(sys.argv[2]))
