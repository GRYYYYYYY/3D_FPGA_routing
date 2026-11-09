#!/usr/bin/env python3
"""Deduplicate audited heldout private route inputs, preserving paths and bytes."""
import collections
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import time

BASE = Path(__file__).resolve().parent.parent
RUNS = BASE / 'runs'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def main():
    locks = []
    for name in ('strict_continuation.lock', 'serial_runner.lock', 'training_runner.lock', 'evaluation_runner.lock'):
        f = (BASE / name).open('a')
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locks.append(f)
    candidates = json.loads((BASE / 'disk_recovery_dedup_candidates_20261105.json').read_text())
    allowed = set()
    for p in (BASE / 'evaluation_cases').glob('*/result.json'):
        result = json.loads(p.read_text())
        if result.get('status') != 'completed':
            continue
        for flow, row in result.get('flows', {}).items():
            if row.get('status') == 'completed' and (p.parent / (flow + '_audit_summary.json')).exists():
                allowed.update(row.get('roles', {}).values())
    shared_inodes = set()
    for p in RUNS.glob('*/manifest.json'):
        m = json.loads(p.read_text())
        if m.get('status') in ('starting', 'running'):
            raise RuntimeError('unresolved active manifest: ' + str(p))
        for name in m.get('shared_inputs', {}):
            try:
                s = os.stat(name)
                shared_inodes.add((s.st_dev, s.st_ino))
            except FileNotFoundError:
                raise RuntimeError('missing recorded shared input: ' + name)
    plan = []
    for group in candidates['groups']:
        members = [Path(x[0]).resolve() for x in group['paths'] if Path(x[0]).parent.name in allowed]
        by_inode = collections.defaultdict(list)
        for path in members:
            s = path.lstat()
            if not stat.S_ISREG(s.st_mode) or (s.st_dev, s.st_ino) in shared_inodes:
                continue
            by_inode[(s.st_dev, s.st_ino)].append(path)
        complete = [paths for paths in by_inode.values() if paths[0].stat().st_nlink == len(paths)]
        if len(complete) < 2:
            continue
        for paths in complete:
            if digest(paths[0]) != group['sha256']:
                raise RuntimeError('hash mismatch: ' + str(paths[0]))
        plan.append({'sha256': group['sha256'], 'bytes_each': group['bytes_each'],
                     'inode_groups': [[str(p) for p in paths] for paths in complete]})
    journal = BASE / 'disk_recovery_dedup_journal_20261105.jsonl'
    if journal.exists():
        raise FileExistsError(journal)
    with journal.open('x') as log:
        def record(value):
            log.write(json.dumps(value, sort_keys=True) + '\n'); log.flush(); os.fsync(log.fileno())
        record({'event':'validated', 'utc':time.time(), 'groups':plan})
        for group in plan:
            source = Path(group['inode_groups'][0][0]); os.chmod(source, 0o444)
            for paths in group['inode_groups'][1:]:
                for name in paths:
                    path = Path(name); temp = path.with_name('.' + path.name + '.recovery-dedup')
                    if temp.exists(): raise FileExistsError(temp)
                    record({'event':'before', 'source':str(source), 'path':str(path), 'sha256':group['sha256']})
                    os.link(source, temp); os.replace(temp, path)
                    if path.stat().st_ino != source.stat().st_ino: raise RuntimeError('inode mismatch')
                    record({'event':'after', 'source':str(source), 'path':str(path)})
        record({'event':'complete', 'utc':time.time()})
    print('completed groups', len(plan), 'potential GiB', round(sum(g['bytes_each'] * (len(g['inode_groups']) - 1) for g in plan) / 2**30, 2), flush=True)

if __name__ == '__main__': main()
