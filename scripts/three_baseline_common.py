#!/usr/bin/env python3
"""Immutable receipts for the three-baseline comparison requested 2026-10-27."""
import os
from pathlib import Path
import signal
import subprocess
import time
from lazagna_common import ROOT, PYTHON, sha256, utc, write_json

BASE = ROOT / 'results/three_baselines_20261027'
OLD = ROOT / 'results/lazagna_reproduction'
MODERN = ROOT / 'artifacts/bin/lazagna-vtr9-port-buildfix/vpr'
A0 = ROOT / 'artifacts/bin/baseline/vpr'
A3 = ROOT / 'artifacts/bin/a4scc/vpr'
A3_ENV = {'VPR_H3D_MODE':'static', 'VPR_H3D_REACHABILITY':'scc', 'VPR_H3D_STATS':'1'}


def read(path):
    import json
    return json.loads(Path(path).read_text())


def run(name, command, *, inputs=(), environment=None, timeout=3600, cwd=None):
    directory = BASE / 'runs' / name
    directory.mkdir(parents=True, exist_ok=True)
    receipt = directory / 'manifest.json'
    if receipt.exists():
        raise RuntimeError(f'Existing run {name}')
    env = os.environ.copy()
    for key in list(env):
        if key.startswith('VPR_H3D_'):
            del env[key]
    env['PATH'] = str(PYTHON.parent) + os.pathsep + env['PATH']
    env.update(environment or {})
    command = list(map(str, command))
    data = dict(name=name, command=command, cwd=str(Path(cwd or directory).resolve()),
        inputs={str(Path(p).resolve()):sha256(p) for p in inputs}, environment=environment or {},
        start_utc=utc(), timeout_seconds=timeout, status='starting')
    write_json(receipt, data)
    started = time.monotonic()
    with (directory/'stdout.log').open('w') as out:
        proc = subprocess.Popen(['/usr/bin/time','-v','-o',str(directory/'time.txt'),*command],
            cwd=data['cwd'],env=env,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
        data.update(pid=proc.pid,status='running');write_json(receipt,data)
        try:
            code = proc.wait(timeout=timeout)
            status = 'completed' if code == 0 else 'failed'
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait()
            code,status = proc.returncode,'timeout'
    data.update(returncode=code,status=status,finish_utc=utc(),wall_seconds=time.monotonic()-started)
    write_json(receipt,data)
    print(name,status,flush=True)
    return data
