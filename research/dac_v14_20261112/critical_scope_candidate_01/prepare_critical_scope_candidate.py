#!/usr/bin/env python3
"""Build and bind an isolated diagnostic candidate after formal timing ends."""
import argparse
import fcntl
import os
import shutil
import signal
import subprocess
import time
from retained_prefix_workflow import D, read, write, sha, require_formal_terminal, source_files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='critical_scope_candidate_01')
    args = ap.parse_args()
    require_formal_terminal()
    lock = (D / 'retained_prefix_build.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    out = D / args.out
    out.mkdir(exist_ok=False)
    before = source_files()
    for name in ['h3d_fast_plan.cpp', 'h3d_fast_plan.h', 'route_common.cpp', 'route_common.h', 'route_net.tpp']:
        expected = read(D / 'critical_scope_implementation.json')['source_binding'][name]['after_sha256']
        assert before['vpr/src/route/' + name] == expected
    for relative in before:
        target = out / 'src' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(D / 'src' / relative, target)
    for name in ['retained_prefix_workflow.py', 'prepare_critical_scope_candidate.py',
                 'analyze_retained_prefix.py', 'test_retained_prefix_parser.py',
                 'retained_prefix_parser_validation.log', 'critical_scope_implementation.json',
                 'critical_scope_unbuilt.patch']:
        shutil.copy2(D / name, out / name)
    write(out / 'build_registration.json', dict(status='registered_before_build',
        source_sha256=before, builder_sha256=sha(__file__), pid=os.getpid(),
        start_ticks=open('/proc/self/stat').read().split(') ', 1)[1].split()[19],
        timeout_seconds=1800, per_process_memory_bytes=64 * 1024**3,
        disk_reserve_bytes=80 * 1024**3, native_route_calls=0,
        question='Compile refresh-only baseline opening credit; default-off reproduction and separate quality ablation required.'))
    started = time.monotonic()
    # The upstream wrapper reads SOURCE_DIR from PWD; subprocess cwd alone
    # does not update that inherited environment variable.
    build_environment = dict(os.environ, PWD=str(D / 'src'))
    with (out / 'build.log').open('w') as stream:
        process = subprocess.Popen(['prlimit', '--as=' + str(64 * 1024**3), '--', 'make', '-j8', 'vpr'],
                                   cwd=D / 'src', env=build_environment, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        timed_out = False
        try:
            rc = process.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            rc = process.returncode
    write(out / 'build_result.json', dict(returncode=rc, timed_out=timed_out,
        wall_seconds=time.monotonic() - started, source_unchanged=before == source_files()))
    assert rc == 0 and not timed_out and before == source_files(), 'Preserve failed build; use a new stage after diagnosis'
    (out / 'bin').mkdir()
    shutil.copy2(D / 'src/vpr/vpr', out / 'bin/vpr')
    shutil.copy2(D / 'src/build/CMakeCache.txt', out / 'CMakeCache.txt')
    assert b'VPR_H3D_LAYER_BB_CRITICALITY' in (out / 'bin/vpr').read_bytes()
    assert 'VTR_ASSERT_LEVEL:STRING=2' in (out / 'CMakeCache.txt').read_text()
    write(out / 'binding.json', dict(status='built_not_native_validated',
        source_sha256=before, binary_sha256=sha(out / 'bin/vpr'),
        cmake_cache_sha256=sha(out / 'CMakeCache.txt'), build_log_sha256=sha(out / 'build.log'),
        qualification='Frozen marginal-opening candidate. Native default-off reproduction and controlled quality ablation pending.'))
    print('Built candidate', out)


if __name__ == '__main__':
    main()
