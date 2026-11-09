#!/usr/bin/env python3
"""Diagnostic P1 run sampling VPR and descendants; polling is not tracing."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

root = Path(__file__).resolve().parents[3]
base = root / 'results/architecture_flow_20261027'
oldpath = base / 'runs/balance_relative3_spmv_s11_hybrid_o_n40_w100_p1_place/manifest.json'
old = json.loads(oldpath.read_text())
out = Path(__file__).parent / 'process_tree_pilot_spmv_hybrid_w100'
out.mkdir(exist_ok=False)
binary = Path(__file__).parent / 'build/vpr/vpr'
command = list(old['command']); command[0] = str(binary)
for option, name in [('--net_file', 'packed.net'), ('--place_file', 'placed.place')]:
    command[command.index(option)+1] = str(out/name)
env = dict(os.environ); env.update(old['environment'])
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
(out/'registration.json').write_text(json.dumps(dict(
    utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command,
    binary_sha256=sha(binary), original_manifest_sha256=sha(oldpath),
    environment=old['environment'], interval_seconds=0.01, timeout_seconds=3600,
    limits='Recursive /proc children polling can miss transient processes or threads.'), indent=2)+'\n')
observed = {}; samples = 0; start = time.monotonic(); timed_out = False
with (out/'stdout.log').open('w') as log:
    proc = subprocess.Popen(['/usr/bin/prlimit','--as=68719476736:68719476736','--',*command],
                            cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
    while proc.poll() is None:
        pending = [proc.pid]; seen = set(); samples += 1
        while pending:
            pid = pending.pop()
            if pid in seen: continue
            seen.add(pid); path = Path('/proc')/str(pid)
            try:
                status = (path/'status').read_text().splitlines()
                fields = dict(x.split(':',1) for x in status if ':' in x)
                name = fields['Name'].strip(); threads = int(fields['Threads'].strip())
                cmdline = (path/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace').strip()
                stat = (path/'stat').read_text(); start_ticks = stat[stat.rfind(')')+2:].split()[19]
                key = f'{pid}:{start_ticks}'
                item = observed.setdefault(key,dict(pid=pid,name=name,cmdline=cmdline,peak_threads=0,samples=0))
                item['peak_threads'] = max(item['peak_threads'],threads); item['samples'] += 1
                for task in (path/'task').iterdir():
                    try: pending.extend(int(x) for x in (task/'children').read_text().split())
                    except (OSError, ValueError): pass
            except (OSError, KeyError, ValueError, IndexError): pass
        if time.monotonic()-start > 3600:
            os.killpg(proc.pid,signal.SIGTERM);timed_out=True;break
        time.sleep(0.01)
    code = proc.wait()
result = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),returncode=code,
              timeout=timed_out,wall_seconds=time.monotonic()-start,samples=samples,
              observed_processes=list(observed.values()),
              max_observed_threads=max((x['peak_threads'] for x in observed.values()),default=0),
              limitations=['Polling can miss short-lived threads/processes',
                           'One circuit/architecture; not universal evidence',
                           'Threads in unrelated shared-host processes not included'])
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('returncode',code,'samples',samples,'processes',len(observed),
      'peak',result['max_observed_threads'],flush=True)
