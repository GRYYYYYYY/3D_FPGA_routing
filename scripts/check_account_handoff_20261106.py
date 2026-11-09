#!/usr/bin/env python3
"""Read-only check of the recorded account handoff; never starts or stops jobs."""
import datetime
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
SNAPSHOT = ROOT / 'docs/账号切换状态_2026-11-06.json'


def main():
    snapshot = json.loads(SNAPSHOT.read_text())
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    same_host = os.uname().nodename == snapshot['hostname'] and boot == snapshot['boot_id']
    print('UTC:', datetime.datetime.now(datetime.timezone.utc).isoformat())
    print('Host:', os.uname().nodename, 'same recorded host and boot:', same_host)
    print('Snapshot UTC:', snapshot['utc'])
    for record in snapshot['processes']:
        pid = record['pid']
        try:
            proc = Path('/proc') / str(pid)
            fields = (proc / 'stat').read_text().rsplit(') ', 1)[1].split()
            command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
            match = same_host and int(fields[19]) == record['start_ticks'] and command == record['command']
            print('Recorded PID', pid, 'state', fields[0], 'identity matches:', match)
        except (OSError, ValueError, IndexError) as error:
            print('Recorded PID', pid, 'not observed:', type(error).__name__)
    for relative in (
        'parallel_continuation_v1/state.json',
        'heldout_disk_recovery_queue_v2/state.json',
        'post_heldout_continuation_v1/state.json',
    ):
        path = BASE / relative
        try:
            print(relative, path.read_text().strip())
        except OSError as error:
            print(relative, type(error).__name__)
    print('Heldout result files:', len(list((BASE / 'evaluation_cases').glob('heldout_*/result.json'))), '/168')
    for path in sorted((BASE / 'runs').glob('heldout_reduction_layer_s21_sb_n125_w100_p1_*/manifest.json')):
        manifest = json.loads(path.read_text())
        print(path.parent.name, manifest['status'])
    print('This check is read-only. Missing PIDs on another host do not establish that the original jobs stopped.')


if __name__ == '__main__':
    main()
