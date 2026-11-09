"""Verify SIGINT drains an active execute_cases worker without killing its child."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

WORKER = r'''
from pathlib import Path
import subprocess,sys,time
from run_flatland_evaluation_import_fix_v1 import execute_cases
root=Path(sys.argv[1])
def run(job):
    if job == 2:
        (root/'unexpected_second_job').write_text('started')
    child=subprocess.Popen([sys.executable,'-c',
        'from pathlib import Path; import time,sys; p=Path(sys.argv[1]); '
        '(p/"child_started").write_text("yes"); time.sleep(2); '
        '(p/"child_finished").write_text("yes")',str(root)],start_new_session=True)
    (root/'child_pid').write_text(str(child.pid))
    child.wait(timeout=10)
    assert child.returncode==0
    (root/'case_completed').write_text('completed')
    return {'status':'completed','job':job}
execute_cases([1,2],1,runner=run)
'''


def main():
    with tempfile.TemporaryDirectory(prefix='controlled_drain_test_') as tmp:
        root = Path(tmp)
        with (root/'log').open('w') as log:
            proc = subprocess.Popen([sys.executable, '-c', WORKER, str(root)],
                                    stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=True)
            try:
                deadline = time.monotonic() + 10
                while not (root/'child_started').exists():
                    assert proc.poll() is None, (root/'log').read_text()
                    assert time.monotonic() < deadline
                    time.sleep(.02)
                os.kill(proc.pid, signal.SIGINT)
                time.sleep(.1)
                assert proc.poll() is None, 'supervisor exited before draining its active worker'
                assert not (root/'case_completed').exists()
                proc.wait(timeout=10)
                assert proc.returncode != 0
                assert (root/'child_finished').exists()
                assert (root/'case_completed').exists()
                assert not (root/'unexpected_second_job').exists()
                assert 'KeyboardInterrupt' in (root/'log').read_text()
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait()
        print('PASS: active child and full case finish; second case is not submitted; original interruption remains visible')


if __name__ == '__main__':
    main()
