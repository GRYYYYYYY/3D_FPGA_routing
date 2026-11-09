#!/usr/bin/env python3
"""Isolated experiment receipts with checked immutable-input hash reuse."""
import os
import json
from pathlib import Path
import signal
import subprocess
import threading
import time

from lazagna_common import ROOT, PYTHON, sha256, utc, write_json
from run_vpr import parse_metrics
from process_tree_observer import ProcessTreeObserver

BASE = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/results/architecture_flow_20261027/serial_strict_reexecution_20261103')
ADDRESS_SPACE_BYTES = 64*1024**3
STRACE = ROOT/'results/architecture_flow_20261027/single_thread_candidate_20261103/deps/strace_root/usr/bin/strace'
_cache = {}
_lock = threading.Lock()


def identity(path):
    s = Path(path).stat()
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def frozen_hash(path, expected=None):
    """Hash once per supervisor; refuse any later change to a shared input."""
    path = str(Path(path).resolve())
    with _lock:
        before = identity(path)
        if path in _cache:
            previous, digest = _cache[path]
            if before != previous: raise RuntimeError(f'Frozen input changed: {path}')
        else:
            digest = sha256(path)
            if before != identity(path): raise RuntimeError(f'Input changed during hashing: {path}')
            _cache[path] = (before, digest)
        if expected is not None and expected != digest: raise RuntimeError(f'Input hash mismatch: {path}')
        return dict(sha256=digest, stat_identity=before)


def run(name, command, *, frozen=(), private_inputs=(), environment=None, timeout=1800, tags=None):
    """Run one private process group and preserve failures without retries."""
    directory = BASE/'runs'/name
    directory.mkdir(parents=True, exist_ok=True)
    receipt = directory/'manifest.json'
    if receipt.exists(): raise FileExistsError(receipt)
    command = list(map(str, command))
    shared = {str(Path(p).resolve()): frozen_hash(p) for p in frozen}
    # Bind the preregistered resolved dynamic dependencies as well as binaries.
    dependency_file = BASE/'runtime_dependency_binding.json'
    dependency_binding = json.loads(dependency_file.read_text())
    if dependency_binding.get('missing'):
        raise RuntimeError('Runtime dependency binding contains unresolved libraries')
    shared[str(dependency_file.resolve())] = frozen_hash(dependency_file)
    for path, expected in dependency_binding['sha256'].items():
        shared[path] = frozen_hash(path, expected)
    mutable = {str(Path(p).resolve()): sha256(p) for p in private_inputs}
    env = os.environ.copy()
    for key in list(env):
        if key.startswith('VPR_H3D_'): del env[key]
    env['PATH'] = str(PYTHON.parent)+os.pathsep+env['PATH']
    overrides = dict(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    overrides.update(environment or {}); env.update(overrides)
    data = dict(name=name, command=command, cwd=str(directory), shared_inputs=shared,
        private_input_sha256=mutable, environment=overrides, timeout_seconds=timeout,
        tags=tags or {}, start_utc=utc(), status='starting', supervisor_pid=os.getpid(),
        runner_sha256=frozen_hash(__file__)['sha256'],
        execution_limit=dict(address_space_bytes=ADDRESS_SPACE_BYTES, core_dump_bytes=0,
            enforcement='/usr/bin/prlimit --as=soft:hard --core=0:0, inherited by children'))
    data['thread_tracer'] = frozen_hash(STRACE)
    write_json(receipt, data)
    started = time.monotonic()
    with (directory/'stdout.log').open('x') as output:
        try:
            proc = subprocess.Popen([str(STRACE), '-f', '-qq', '-s', '128', '-e', 'trace=clone,clone3',
                '-o', str(directory/'thread_syscalls.log'), '--',
                '/usr/bin/time', '-v', '-o', str(directory/'time.txt'),
                '/usr/bin/prlimit', f'--as={ADDRESS_SPACE_BYTES}:{ADDRESS_SPACE_BYTES}', '--core=0:0', '--', *command],
                cwd=directory, env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        except OSError as error:
            data.update(status='launch_failed', error=str(error), finish_utc=utc())
            write_json(receipt, data); return data
        data.update(status='running', process_group_id=proc.pid); write_json(receipt, data)
        observer = ProcessTreeObserver(proc.pid)
        observer.start()
        try:
            code = proc.wait(timeout=timeout); status = 'completed' if code == 0 else 'failed'
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL); proc.wait()
            code, status = proc.returncode, 'timeout'
        finally:
            thread_observation = observer.stop()
    data['process_tree_observation'] = thread_observation
    data['execution_status'] = status
    trace_path = directory/'thread_syscalls.log'
    if trace_path.exists():
        trace = trace_path.read_text(errors='replace')
        thread_attempts = sum('CLONE_THREAD' in line for line in trace.splitlines())
        data['thread_syscall_trace'] = dict(sha256=sha256(trace_path),
            clone_thread_flag_lines=thread_attempts,
            qualification='strace follows descendants; any CLONE_THREAD attempt is conservatively flagged even if the syscall failed. Ptrace changes timing; external/unsupported syscall coverage is not assumed.')
    else:
        thread_attempts = None
        data['thread_syscall_trace'] = dict(error='trace file missing')
    if thread_observation['violation_observed'] or thread_attempts:
        status = 'thread_constraint_violated'
    elif thread_attempts is None or thread_observation['samples'] == 0 or not thread_observation['processes']:
        status = 'thread_observation_missing'
    data.update(status=status, returncode=code, finish_utc=utc(), wall_seconds=time.monotonic()-started,
                metrics=parse_metrics((directory/'stdout.log').read_text(errors='replace')))
    changed = [p for p, h in shared.items() if identity(p) != tuple(h['stat_identity'])]
    if changed: data.update(status='input_integrity_failed', changed_inputs=changed)
    data['outputs'] = {p.name: dict(sha256=sha256(p), bytes=p.stat().st_size)
        for p in [directory/f for f in ['packed.net', 'placed.place', 'routed.route', 'stdout.log', 'time.txt']] if p.exists()}
    write_json(receipt, data)
    print(name, data['status'], flush=True)
    return data


def seal_inputs(output):
    """Full final rehash makes cached checks explicit and independently reviewable."""
    with _lock: entries = dict(_cache)
    results = {}
    for path, (previous, expected) in entries.items():
        actual = sha256(path)
        results[path] = dict(sha256=actual, stat_identity=identity(path), passed=actual == expected and identity(path) == previous)
    write_json(output, dict(utc=utc(), inputs=results, passed=all(x['passed'] for x in results.values())))
    if not all(x['passed'] for x in results.values()): raise RuntimeError('Frozen input finalization failed')
