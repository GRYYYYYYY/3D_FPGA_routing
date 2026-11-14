#!/usr/bin/env python3
"""Single validation owner: finish the registered build, then tiny and real BNN gates."""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from native_feedback_analysis_pool import process_identity

b = D / 'candidate_full_sta_tiny_queue_01'
b.mkdir(exist_ok=False)
lock = (b / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
prior = D / 'candidate_full_sta_stage_01'
owner = read(prior / 'registration.json')
files = [Path(__file__).resolve(), D / 'validate_candidate_full_sta_tiny.py',D/'candidate_full_sta_analysis_pool.py',prior/'registration.json']
bound = {str(p): sha(p) for p in files}
write(b / 'registration.json', dict(pid=os.getpid(), start_ticks=process_identity(os.getpid())['start_ticks'],
      prior_owner=owner, source_sha256=bound,
      question='Validate actual candidate/source native FULLSTA and separate-LOAD exactness on the small existing two-layer fixture. Temporary at most4total native processes, tiny parent/child each2GiB alongside the original large cohort; no second large context before original owner terminal.',
      qualification='Single owner; no resubmission or modification of original experiments. Local build/test terminal is not termination of research.'))
write(b / 'status.json', dict(status='waiting_for_registered_build', observed_at=time.time()))
while True:
    live = process_identity(owner['pid'])
    if not live or live['state'] == 'Z' or live['start_ticks'] != owner['start_ticks']:
        break
    time.sleep(10)
assert read(prior / 'build_result.json')['returncode'] == 0
assert read(prior / 'binding.json')['status'] == 'built_not_native_validated'
records = []
for script in ['validate_candidate_full_sta_tiny.py']:
    assert all(sha(p) == h for p, h in bound.items())
    started = time.monotonic()
    with (b / (script + '.log')).open('w') as out:
        proc = subprocess.Popen([sys.executable, str(D / script)], stdout=out, stderr=subprocess.STDOUT)
        write(b / 'status.json', dict(status='running', script=script, pid=proc.pid,
              start_ticks=process_identity(proc.pid)['start_ticks'], observed_at=time.time()))
        code = proc.wait()
    records.append(dict(script=script, returncode=code, complete_process_seconds=time.monotonic() - started))
    write(b / 'steps.json', records)
    if code:
        break
write(b / 'completion.json', dict(passed=len(records) == 1 and all(r['returncode'] == 0 for r in records),
      steps=records, source_sha256=bound,
      qualification='Independent new implementation validation; actual route quality and workload timing analyzed separately. Research stays active.'))
