#!/usr/bin/env python3
"""One owner waits for the registered routes, then audits and collects them."""
import fcntl
import os
import subprocess
import time
from three_baseline_common import BASE, ROOT, PYTHON, read, sha256, utc, write_json


def main():
    lock = (BASE/'finisher_owner.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state_path = BASE/'finisher_state.json'
    assert not state_path.exists()
    state = dict(owner_pid=os.getpid(), started_utc=utc(), stage='waiting_for_routes',
                 scripts={str(ROOT/'scripts'/name): sha256(ROOT/'scripts'/name)
                          for name in ('validate_three_baselines.py', 'collect_three_baselines.py')})
    write_json(state_path, state)
    while read(BASE/'route_state.json')['stage'] != 'finished':
        time.sleep(10)
    for stage, name in [('auditing', 'validate_three_baselines.py'), ('collecting', 'collect_three_baselines.py')]:
        state.update(stage=stage, updated_utc=utc());write_json(state_path, state)
        command=[str(PYTHON), '-u', str(ROOT/'scripts'/name)]
        assert sha256(command[-1]) == state['scripts'][command[-1]]
        with (BASE/(stage+'.log')).open('w') as stream:
            process=subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT)
            state['child_pid']=process.pid;write_json(state_path,state)
            code=process.wait()
        if code:
            state.update(stage='failed', failed_step=stage, returncode=code, finished_utc=utc())
            write_json(state_path,state)
            raise RuntimeError(f'{stage} failed: see {stage}.log')
        print(stage, 'completed', flush=True)
    state.update(stage='finished', finished_utc=utc());write_json(state_path,state)


if __name__ == '__main__':
    main()
