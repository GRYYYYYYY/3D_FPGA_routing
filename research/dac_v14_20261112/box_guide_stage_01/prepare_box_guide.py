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
    ap.add_argument('--out', default='box_guide_stage_01')
    args = ap.parse_args()
    require_formal_terminal()
    lock = (D / 'retained_prefix_build.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    out = D / args.out
    out.mkdir(exist_ok=False)
    def sources():
        found=source_files();found['vpr/src/route/serial_connection_router.cpp']=sha(D/'src/vpr/src/route/serial_connection_router.cpp');return found
    before = sources()
    for name,v in read(D/'box_guide_implementation_01/binding.json')['source_binding'].items():
        assert before['vpr/src/route/'+name]==v['after_sha256']
    for relative in before:
        target = out / 'src' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(D / 'src' / relative, target)
    for name in ['retained_prefix_workflow.py','prepare_box_guide.py','box_guide_experiment_01.json']:
        shutil.copy2(D/name,out/name)
    shutil.copytree(D/'box_guide_implementation_01',out/'implementation')
    write(out / 'build_registration.json', dict(status='registered_before_build',
        source_sha256=before, builder_sha256=sha(__file__), pid=os.getpid(),
        start_ticks=open('/proc/self/stat').read().split(') ', 1)[1].split()[19],
        timeout_seconds=1800, per_process_memory_bytes=64 * 1024**3,
        disk_reserve_bytes=80 * 1024**3, native_route_calls=0,
        question='Build read-only actual pushed-seed and native BB search diagnostic; both flag0 frozen control reproduction and flag1 exact native effects required.'))
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
        wall_seconds=time.monotonic() - started, source_unchanged=before == sources()))
    assert rc == 0 and not timed_out and before == sources(), 'Preserve failed build; use a new stage after diagnosis'
    (out / 'bin').mkdir()
    shutil.copy2(D / 'src/vpr/vpr', out / 'bin/vpr')
    shutil.copy2(D / 'src/build/CMakeCache.txt', out / 'CMakeCache.txt')
    assert b'VPR_H3D_BOX_GUIDE_ADMISSION' in (out / 'bin/vpr').read_bytes()
    assert 'VTR_ASSERT_LEVEL:STRING=2' in (out / 'CMakeCache.txt').read_text()
    write(out / 'binding.json', dict(status='built_not_native_validated',
        source_sha256=before, binary_sha256=sha(out / 'bin/vpr'),
        cmake_cache_sha256=sha(out / 'CMakeCache.txt'), build_log_sha256=sha(out / 'build.log'),
        qualification='Frozen read-only domain-trace candidate; flag0/1 native route/guide/cost equivalence pending.'))
    print('Built candidate', out)


if __name__ == '__main__':
    main()
