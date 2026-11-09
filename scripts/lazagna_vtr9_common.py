#!/usr/bin/env python3
"""Separate, immutable receipts for the pinned VTR9-port pilot study."""
import os
from pathlib import Path
import signal
import subprocess
import time

from lazagna_common import ROOT, PYTHON, sha256, utc, write_json

BASE = ROOT / 'results/lazagna_vtr9_port'
SOURCE = ROOT / 'vendor/lazagna-vtr9-src'
LAZAGNA = ROOT / 'vendor/LaZagna'
COMMIT = '5abd3acaa603e037ec390fa545b04301f13d57e0'


def run(name, command, *, inputs=(), cwd=None, timeout=1800):
    directory = BASE / 'runs' / name
    directory.mkdir(parents=True, exist_ok=True)
    receipt = directory / 'manifest.json'
    if receipt.exists():
        raise RuntimeError(f'Refusing to replace {receipt}')
    command = list(map(str, command))
    env = os.environ.copy()
    env['PATH'] = str(PYTHON.parent) + os.pathsep + env['PATH']
    # Prevent an inherited experimental H3D setting from contaminating controls.
    removed = {k: env.pop(k) for k in list(env) if k.startswith('VPR_H3D_')}
    data = dict(name=name, command=command, cwd=str(Path(cwd or directory).resolve()),
                inputs={str(Path(p).resolve()): sha256(p) for p in inputs},
                start_utc=utc(), timeout_seconds=timeout, status='starting',
                removed_h3d_environment=removed, python=str(PYTHON))
    write_json(receipt, data)
    started = time.monotonic()
    with (directory / 'stdout.log').open('w') as output:
        process = subprocess.Popen(['/usr/bin/time', '-v', '-o', str(directory / 'time.txt'),
                                    *command], cwd=data['cwd'], env=env, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        data.update(pid=process.pid, status='running')
        write_json(receipt, data)
        try:
            code = process.wait(timeout=timeout)
            status = 'completed' if code == 0 else 'failed'
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            code, status = process.returncode, 'timeout'
    data.update(status=status, returncode=code, finish_utc=utc(),
                wall_seconds=time.monotonic() - started)
    write_json(receipt, data)
    print(name, status, flush=True)
    return data
