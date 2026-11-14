#!/usr/bin/env python3
"""Reserve one later large integration owner without disturbing the current quality cohort."""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from candidate_full_sta_analysis_pool import process_identity

b = D / 'candidate_full_sta_bnn_queue_01'
b.mkdir(exist_ok=False)
lock = (b / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
prior = D / 'uniform_feedback_resource_dev_01/queue'
owner = read(prior / 'registration.json')
assert read(D / 'candidate_full_sta_tiny_01/completion.json')['passed']
files = [Path(__file__).resolve(), D / 'validate_candidate_full_sta_bnn.py', D / 'candidate_full_sta_analysis_pool.py',
         D / 'pool_state_evaluator_v3.py', D / 'candidate_full_sta_stage_01/binding.json',
         D / 'candidate_full_sta_tiny_01/completion.json', D / 'candidate_observation_view_validation_01/completion.json', prior / 'registration.json']
bound = {str(p): sha(p) for p in files}
write(b / 'registration.json', dict(pid=os.getpid(), start_ticks=process_identity(os.getpid())['start_ticks'],
      prior_owner=dict(pid=owner['pid'], start_ticks=owner['start_ticks'], registration=str(prior / 'registration.json')),
      source_sha256=bound, after=str(prior),
      qualification='Single new large validation owner after original quality cohort terminal; no two simultaneous large loaded contexts. Prior actor failures are evidence, not an automatic overall research stop or reason to rerun completed jobs.'))
write(b / 'status.json', dict(status='waiting_for_original_uniform_quality_owner', observed_at=time.time()))
while True:
    actual = process_identity(owner['pid'])
    if not actual or actual['state'] == 'Z' or actual['start_ticks'] != owner['start_ticks']:
        break
    time.sleep(15)
assert (prior / 'completion.json').exists(), 'Owner terminal without receipt: inspect; do not blindly resubmit'
assert all(sha(p) == h for p, h in bound.items())
with (b / 'validation.log').open('w') as log:
    proc = subprocess.Popen([sys.executable, str(D / 'validate_candidate_full_sta_bnn.py')], stdout=log, stderr=subprocess.STDOUT)
    write(b / 'status.json', dict(status='running_large_actual_candidate_validation', pid=proc.pid,
          start_ticks=process_identity(proc.pid)['start_ticks'], observed_at=time.time()))
    code = proc.wait()
write(b / 'completion.json', dict(passed=code == 0, returncode=code, source_sha256=bound,
      qualification='Independent real-candidate integration terminal, not overall research completion or formal cold-runtime evidence. Preserve failures and actual candidate/source identities.'))
