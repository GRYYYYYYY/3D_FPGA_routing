#!/usr/bin/env python3
"""Bounded, read-only account handoff check; never submits or recovers jobs."""
import datetime
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
SNAPSHOT = ROOT / 'docs/账号切换状态_2026-11-07.json'


def proc_record(pid):
    proc = Path('/proc') / str(pid)
    fields = (proc / 'stat').read_text().rsplit(') ', 1)[1].split()
    return dict(pid=pid, start_ticks=int(fields[19]), state=fields[0],
                ppid=int(fields[1]), session_id=int(fields[3]),
                command=(proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace'))


def main():
    snapshot = json.loads(SNAPSHOT.read_text())
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    same_host = os.uname().nodename == snapshot['hostname'] and boot == snapshot['boot_id']
    print('UTC:', datetime.datetime.now(datetime.timezone.utc).isoformat())
    print('Host:', os.uname().nodename, 'same recorded host and boot:', same_host)
    print('Snapshot UTC:', snapshot['utc'])
    print('Free GiB:', round(shutil.disk_usage(BASE).free / 2**30, 2), 'reserve: 80')
    live = []
    for recorded in snapshot['processes']:
        try:
            current = proc_record(recorded['pid'])
            match = same_host and all(current[k] == recorded[k] for k in ('start_ticks', 'command'))
            print('Recorded PID', current['pid'], 'state', current['state'], 'identity matches:', match)
            if match and current['state'] != 'Z':
                live.append(current['pid'])
        except (OSError, ValueError, IndexError) as error:
            print('Recorded PID', recorded['pid'], 'not observed:', type(error).__name__)
    seen = set()
    selected = []
    while live and len(seen) < 256:
        pid = live.pop()
        if pid in seen:
            continue
        seen.add(pid)
        try:
            row = proc_record(pid)
            comm = (Path('/proc') / str(pid) / 'comm').read_text().strip()
            if comm == 'vpr' or 'python' in row['command'].split(' ')[0]:
                selected.append({k: row[k] for k in ('pid', 'ppid', 'start_ticks', 'state')})
            for task in (Path('/proc') / str(pid) / 'task').iterdir():
                try:
                    live.extend(map(int, (task / 'children').read_text().split()))
                except OSError:
                    pass
        except (OSError, ValueError, IndexError):
            pass
    print('Live process tree:', json.dumps(selected))
    if live:
        print('Process scan bounded at 256 entries; remaining descendants were not inspected.')
    state = BASE / 'parallel_continuation_v1/state.json'
    print('Current coordinator state:', state.read_text().strip())
    print('Heldout result files:', len(list((BASE / 'evaluation_cases').glob('heldout_*/result.json'))), '/168 (includes failures)')
    for name in snapshot['in_progress_cases']:
        directory = BASE / 'evaluation_cases' / name
        print(name, 'case result exists:', (directory / 'result.json').exists())
        for path in sorted(directory.glob('*_audit_summary.json')):
            row = json.loads(path.read_text())
            print(' ', path.name, 'passed:', row.get('passed'),
                  'legal:', len(row.get('legal', [])), 'failed:', len(row.get('failed', [])))
    log = BASE / 'parallel_continuation_v1/heldout.log'
    if log.exists():
        with log.open('rb') as handle:
            handle.seek(max(0, log.stat().st_size - 8192))
            lines = handle.read(8192).decode(errors='replace').splitlines()
        print('Heldout log tail:\n' + '\n'.join(lines[-12:]))
    print('Read-only observation. No VPR during audits can be normal. Old queue needs_diagnosis is an expected historical drain state.')
    print('Different host, missing PID, or a stale phase timestamp alone does not establish that the original job stopped; reconcile before recovery.')


if __name__ == '__main__':
    main()
