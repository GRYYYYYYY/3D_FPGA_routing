#!/usr/bin/env python3
"""Single owner for the two independent paired backend validation cases."""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from export_policy_analysis_pool import process_identity

q = D / 'export_policy_large_queue_01'
q.mkdir(exist_ok=False)
lock = (q / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
assert read(D / 'export_policy_tiny_01/completion.json')['passed']
files = [Path(__file__).resolve(), D / 'validate_export_policy_large.py', D / 'export_policy_tiny_01/completion.json',
         D / 'export_policy_analysis_pool.py', D / 'pool_state_evaluator_v7.py', D / 'export_policy_stage_01/binding.json']
bound = {str(p): sha(p) for p in files}
write(q / 'registration.json', dict(pid=os.getpid(), start_ticks=process_identity(os.getpid())['start_ticks'],
      source_sha256=bound, cases=['timing', 'resource'],
      question='Validate optional full graph-text export and CPD-changing fused FULLSTA without changing live research batches.',
      limits=dict(combined_VPR_maximum=3, this_chain_loaded_parent_plus_child=2,
                  other_registered_quality_chain_maximum=1),
      qualification='Independent new backend experiment. One owner, sequential cases. A local case failure is preserved and does not end research or prevent the other independent case.'))
started = time.monotonic()
results = {}
for case in ['timing', 'resource']:
    assert all(sha(p) == h for p, h in bound.items())
    command = [sys.executable, str(D / 'validate_export_policy_large.py'), '--case', case]
    t = time.monotonic()
    with (q / (case + '.log')).open('w') as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        write(q / 'status.json', dict(case=case, pid=child.pid, start_ticks=process_identity(child.pid)['start_ticks'], command=command))
        code = child.wait()
    receipt = D / ('export_policy_' + case + '_01/completion.json')
    results[case] = dict(returncode=code, passed=code == 0 and receipt.exists() and read(receipt)['passed'],
                         elapsed_seconds=time.monotonic() - t, completion=str(receipt))
    write(q / 'results.json', results)
write(q / 'completion.json', dict(passed=all(r['passed'] for r in results.values()), results=results,
      complete_queue_seconds=time.monotonic() - started, source_sha256=bound,
      complete_single_configuration_algorithm_seconds=None))
