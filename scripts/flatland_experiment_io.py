#!/usr/bin/env python3
"""Isolated experiment receipts with checked immutable-input hash reuse."""
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

from lazagna_common import ROOT, PYTHON, sha256, utc, write_json
from run_vpr import parse_metrics

BASE = ROOT/'results/architecture_flow_20261027'
ADDRESS_SPACE_BYTES = 64*1024**3
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
        execution_limit=dict(address_space_bytes=ADDRESS_SPACE_BYTES, enforcement='/usr/bin/prlimit --as=soft:hard, inherited by children'))
    write_json(receipt, data)
    started = time.monotonic()
    with (directory/'stdout.log').open('x') as output:
        try:
            proc = subprocess.Popen(['/usr/bin/time', '-v', '-o', str(directory/'time.txt'),
                '/usr/bin/prlimit', f'--as={ADDRESS_SPACE_BYTES}:{ADDRESS_SPACE_BYTES}', '--', *command],
                cwd=directory, env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        except OSError as error:
            data.update(status='launch_failed', error=str(error), finish_utc=utc())
            write_json(receipt, data); return data
        data.update(status='running', process_group_id=proc.pid); write_json(receipt, data)
        try:
            code = proc.wait(timeout=timeout); status = 'completed' if code == 0 else 'failed'
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL); proc.wait()
            code, status = proc.returncode, 'timeout'
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
