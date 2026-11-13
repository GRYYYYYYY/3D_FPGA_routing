#!/usr/bin/env python3
"""Single deterministic owner: formal completion -> build -> two diagnostic pairs."""
from pathlib import Path
import fcntl
import os
import shutil
import socket
import subprocess
import time
from retained_prefix_workflow import D, read, write, sha, require_formal_terminal, source_files


def ticks(pid):
    return Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()[19]


def same_owner(pid, start):
    try:
        return ticks(pid) == start
    except FileNotFoundError:
        return False


def main():
    lock = (D / 'retained_prefix_pipeline.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    out = D / 'retained_prefix_pipeline_01'
    out.mkdir(exist_ok=False)
    state_path = out / 'state.json'
    dependency = read(D / 'formal_timing_active.json')
    assert same_owner(dependency['pid'], dependency['start_ticks']), 'Register against a verified live owner'
    scripts = ['queue_retained_prefix.py', 'retained_prefix_workflow.py', 'prepare_retained_prefix_candidate.py',
               'run_retained_prefix.py', 'analyze_retained_prefix.py', 'retained_prefix_implementation.json',
               'test_retained_prefix_parser.py', 'retained_prefix_parser_validation.log', 'retained_prefix_unbuilt.patch']
    bindings = {str(D / p): sha(D / p) for p in scripts}
    source_binding = source_files()
    python = str(D.parents[1] / '.venv-lazagna/bin/python')
    stage = 'retained_prefix_candidate_01'
    cases = [('eltwise_layer', 'retained_prefix_eltwise_dev_01'),
             ('tpu_like.small.os', 'retained_prefix_tpu_dev_01')]
    assert not (D / stage).exists() and all(not (D / b).exists() for _, b in cases)
    (out / 'inputs').mkdir()
    for name in scripts:
        shutil.copy2(D / name, out / 'inputs' / name)
    for relative in source_binding:
        target = out / 'source_before_build' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(D / 'src' / relative, target)
    write(out / 'identity.json', dict(pid=os.getpid(), start_ticks=ticks(os.getpid()), host=socket.gethostname(),
        dependency=dependency, script_bindings=bindings, source_sha256=source_binding,
        cases=cases, stage=stage, registered_at=time.time(),
        policy='Wait only on exact live formal owner, then require completion/seal. No automatic retries or restarts. '
               'Build fixed diagnostic source and validate default-off/trace-on separately for each registered seed. '
               'Any source drift, failed command or reproduction gate returns to main-model diagnosis; research remains active. '
               'luna delegation unavailable; deterministic supervisor only, no model-switch claim.'))
    write(state_path, dict(status='waiting_for_formal_owner', observed_live=True, dependency=dependency, time=time.time()))
    while same_owner(dependency['pid'], dependency['start_ticks']):
        time.sleep(30)
    try:
        require_formal_terminal()
        assert source_files() == source_binding, 'Diagnostic source changed while queued'
        assert all(sha(Path(p)) == h for p, h in bindings.items()), 'Pipeline scripts changed while queued'

        def run_step(label, command):
            assert all(sha(Path(p)) == h for p, h in bindings.items())
            with (out / f'{label}.log').open('x') as log:
                process = subprocess.Popen(command, cwd=D.parents[1], stdout=log,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                write(state_path, dict(status='running_step', step=label, command=command,
                      child_pid=process.pid, child_start_ticks=ticks(process.pid), time=time.time()))
                rc = process.wait()
            assert rc == 0, f'{label} returned {rc}; inspect preserved log'

        run_step('build', [python, str(D / 'prepare_retained_prefix_candidate.py'), '--out', stage])
        for circuit, batch in cases:
            run_step(batch, [python, str(D / 'run_retained_prefix.py'), '--out', batch,
                             '--circuit', circuit, '--stage', stage])
            assert read(D / batch / 'completion.json')['gate_passed'], f'{batch} reproduction gate failed'
            run_step(batch + '_analysis', [python, str(D / 'analyze_retained_prefix.py'),
                '--control', str(D / batch / 'runs' / f'{circuit}_C'),
                '--trace', str(D / batch / 'runs' / f'{circuit}_T'),
                '--out', str(D / batch / 'retained_prefix_mechanisms.json')])
        write(state_path, dict(status='pipeline_complete_requires_scientific_analysis', time=time.time(),
                              research_complete=False, cases=cases))
    except Exception as error:
        write(state_path, dict(status='terminal_requires_diagnosis', error=repr(error), time=time.time(),
                              research_complete=False, automatic_retry=False))
        raise


if __name__ == '__main__':
    main()
