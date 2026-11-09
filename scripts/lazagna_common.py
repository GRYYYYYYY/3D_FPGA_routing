#!/usr/bin/env python3
"""Immutable run receipts for the separate LaZagna reproduction study."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/lazagna_reproduction'
PAPER = ROOT / 'vendor/LaZagna-paper'
PYTHON = ROOT / '.venv-lazagna/bin/python'


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    tmp.replace(path)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def run(name, command, *, cwd=None, timeout=7200, inputs=(), environment=None):
    directory = BASE / 'runs' / name
    directory.mkdir(parents=True, exist_ok=True)
    receipt = directory / 'manifest.json'
    if receipt.exists():
        raise RuntimeError(f'Refusing to replace existing run: {receipt}')
    command = list(map(str, command))
    cwd = Path(cwd or directory).resolve()
    records = {str(Path(p).resolve()): sha256(p) for p in inputs}
    env = os.environ.copy()
    env['PATH'] = str(PYTHON.parent) + os.pathsep + env['PATH']
    if environment:
        env.update(environment)
    data = dict(name=name, command=command, cwd=str(cwd), inputs=records,
                start_utc=utc(), timeout_seconds=timeout, status='starting',
                environment_overrides=environment or {}, python=str(PYTHON))
    write_json(receipt, data)
    started = time.monotonic()
    with (directory / 'stdout.log').open('w') as output:
        process = subprocess.Popen(['/usr/bin/time', '-v', '-o', str(directory / 'time.txt'),
                                    *command], cwd=cwd, env=env, stdout=output,
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
    return data
