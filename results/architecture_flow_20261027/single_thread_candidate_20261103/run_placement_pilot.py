#!/usr/bin/env python3
"""Independent P1 pilot: compare a serial-Tatum build to a registered input.

Thread sampling observes the VPR process only, not its OpenROAD subprocesses;
sampling cannot exclude short-lived threads between observations.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

root = Path(__file__).resolve().parents[3]
base = root / 'results/architecture_flow_20261027'
original = base / 'runs/balance_relative3_spmv_s11_sb_n40_w100_p1_place/manifest.json'
out = Path(__file__).parent / 'placement_pilot_spmv_sb_w100'
out.mkdir(exist_ok=False)
old = json.loads(original.read_text())
binary = Path(__file__).parent / 'build/vpr/vpr'
cmd = list(old['command']); cmd[0] = str(binary)
for option, filename in [('--net_file', 'packed.net'), ('--place_file', 'placed.place')]:
    cmd[cmd.index(option) + 1] = str(out / filename)
env = dict(os.environ); env.update(old['environment'])
def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()
def write(name, data):
    (out / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
write('registration.json', dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    binary=str(binary), binary_sha256=digest(binary), original_manifest=str(original),
    original_manifest_sha256=digest(original), command=cmd, environment=old['environment'],
    address_space_limit_bytes=68719476736, timeout_seconds=3600, sample_interval_seconds=0.01,
    scope='P1 VPR-process sampling, diagnostic pilot; no statistical or full-process proof'))
start = time.monotonic(); samples = 0; peak = 0; histogram = {}; timed_out = False
with (out / 'stdout.log').open('w') as log:
    proc = subprocess.Popen(['/usr/bin/prlimit', '--as=68719476736:68719476736', '--', *cmd],
                            cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
    while proc.poll() is None:
        try:
            status = Path(f'/proc/{proc.pid}/status').read_text()
            value = int(next(x for x in status.splitlines() if x.startswith('Threads:')).split()[1])
            peak = max(peak, value); histogram[str(value)] = histogram.get(str(value), 0) + 1; samples += 1
        except (OSError, StopIteration, ValueError):
            pass
        if time.monotonic() - start > 3600:
            import signal
            os.killpg(proc.pid, signal.SIGTERM); timed_out = True; break
        time.sleep(0.01)
    code = proc.wait()
write('result.json', dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    returncode=code, timeout=timed_out, wall_seconds=time.monotonic()-start,
    vpr_thread_samples=samples, maximum_observed_vpr_threads=peak, histogram=histogram,
    output_sha256={p.name:digest(p) for p in [out/'packed.net',out/'placed.place',out/'stdout.log'] if p.exists()},
    limitations=['VPR PID only; child process threads not sampled', 'polling may miss short-lived threads',
                 'one circuit and one architecture; no proof for all cases']))
print('pilot returncode', code, 'samples', samples, 'peak VPR threads', peak, flush=True)
