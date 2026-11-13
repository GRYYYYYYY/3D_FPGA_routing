#!/usr/bin/env python3
"""Resume deferred-content hashing after the registered coordinator stops.

Writes only a new paper/build audit directory. Never invokes a solver.
"""
from pathlib import Path
import hashlib, json, os, sys, datetime

P = Path(__file__).resolve().parent
AUDIT = P / 'data/closed_metadata_audit.json'
RECORDS = P / 'data/closed_metadata_records.jsonl'
OUT = P / 'build/deferred_file_integrity'
HANDLES = [(3764138, 1876532964), (2567402, 1899451207)]

def ensure_queue_stopped():
    for pid, start in HANDLES:
        try:
            fields = (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()
        except FileNotFoundError:
            continue
        if int(fields[19]) == start and fields[0] != 'Z':
            raise RuntimeError(f'Registered coordinator/executor {pid} is still alive; defer this audit')

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def identity(path):
    s = Path(path).stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]

def main():
    ensure_queue_stopped()  # Before opening outputs or reading deferred contents.
    audit_bytes = AUDIT.read_bytes()
    audit = json.loads(audit_bytes)
    assert hashlib.sha256(RECORDS.read_bytes()).hexdigest() == audit['records_sha256']
    rows = [json.loads(line) for line in RECORDS.read_text().splitlines()]
    rows = [row for row in rows if row['status'] == 'deferred_large_file']
    assert len(rows) == audit['deferred_unique_files'] and all(len(r['expected_sha256']) == 1 for r in rows)
    registration = dict(source_audit_sha256=hashlib.sha256(audit_bytes).hexdigest(),
                        source_records_sha256=audit['records_sha256'], planned=len(rows),
                        scope='Previously deferred closed-stage input files only; excludes paired_width and semantic re-audit.')
    OUT.mkdir(parents=True, exist_ok=True)
    registration_path, log_path = OUT/'registration.json', OUT/'results.jsonl'
    if registration_path.exists():
        if json.loads(registration_path.read_text()) != registration:
            raise RuntimeError('Existing registration differs; preserve it and investigate')
    else:
        with registration_path.open('x') as f:
            json.dump(registration, f, indent=2); f.write('\n')
    done = []
    if log_path.exists():
        with log_path.open() as f:
            done = [json.loads(line) for line in f]
        for index, result in enumerate(done):
            if index >= len(rows) or result['paths'] != rows[index]['paths'] or result['expected_sha256'] != rows[index]['expected_sha256'][0]:
                raise RuntimeError('Existing results are not the registered prefix; preserve and investigate')
    with log_path.open('a') as f:
        for row in rows[len(done):]:
            ensure_queue_stopped()
            paths = row['paths']; expected = row['expected_sha256'][0]
            try:
                before = [identity(path) for path in paths]
                actual = digest(Path(paths[0]))
                after = [identity(path) for path in paths]
                passed = before == after and all(x == row['identity'] for x in before) and actual == expected
                result = dict(paths=paths, expected_sha256=expected, sha256=actual, passed=passed,
                              identity_matches_registered=all(x == row['identity'] for x in before), identity_stable=before == after)
            except OSError as error:
                result = dict(paths=paths, expected_sha256=expected, passed=False, error=str(error))
            f.write(json.dumps(result) + '\n'); f.flush(); os.fsync(f.fileno())
            done.append(result)
            if len(done) % 100 == 0: print('checked', len(done), '/', len(rows), flush=True)
    summary = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   passed=len(done) == len(rows) and all(x['passed'] for x in done),
                   checked=len(done), failed=sum(not x['passed'] for x in done),
                   registration=registration, results_sha256=digest(log_path),
                   limitations=['Does not re-run route/graph semantic checks.', 'Does not include paired_width artifacts.'])
    summary_path = OUT/'summary.json'
    if summary_path.exists():
        raise RuntimeError('Summary already exists; preserve the earlier result')
    with summary_path.open('x') as f: json.dump(summary, f, indent=2); f.write('\n')
    print('finished', summary['checked'], 'failed', summary['failed'])
    return 0 if summary['passed'] else 1

if __name__ == '__main__':
    try: sys.exit(main())
    except (RuntimeError, AssertionError) as error:
        print('audit not started or interrupted:', error, file=sys.stderr); sys.exit(2)
