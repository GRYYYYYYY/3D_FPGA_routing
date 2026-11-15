"""Find actual transaction origins when an earlier actor itself reused evidence.

Discovery grants no reuse permission: the existing exact native matcher must
still validate state, request, binary, objective, physical checks and timing.
"""
from pathlib import Path
from retained_prefix_workflow import read

def resolve(attempt_files,seed_batches=()):
    batches=[];seen=set()
    def add(path):
        path=Path(path).resolve()
        if path not in seen:
            seen.add(path);batches.append(path)
    for path in seed_batches:add(path)
    for path in attempt_files:
        for row in read(path):
            if row.get('evaluation'):add(Path(row['evaluation']).resolve().parent)
            failure=row.get('native_failure') or {}
            if failure.get('batch'):add(failure['batch'])
            elif failure.get('transaction'):add(failure['transaction'])
    return batches
