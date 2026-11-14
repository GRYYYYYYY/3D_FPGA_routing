#!/usr/bin/env python3
"""Resume the original current-STA plan after correcting only the anchor identity guard."""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from candidate_full_sta_analysis_pool import process_identity

b = D / 'resource_first_timing_resume_01'
q = b / 'queue'
q.mkdir(parents=True, exist_ok=False)
lock = (q / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
prior = D / 'resource_first_timing_dev_01/timing'
prior_queue = prior.parent / 'queue'
reg = read(prior_queue / 'registration.json')
actual = process_identity(reg['pid'])
assert not actual or actual['state'] == 'Z' or actual['start_ticks'] != reg['start_ticks']
assert read(prior / 'completion.json')['operator_stop'] == 'transaction_preparation_failed'
proof = D / 'native_problem_identity_validation_01/completion.json'
assert read(proof)['passed']
anchor = Path(read(prior / 'registration.json')['initial_state'])
limits = prior.parent / 'absolute_limits.json'
files = [Path(__file__).resolve(), D / 'run_independent_critical_portfolio_v3.py', D / 'prepare_native_group_step_v2.py',
         D / 'native_problem_identity.py', proof, prior / 'registration.json', prior / 'resume_state.json',
         prior / 'completion.json', prior / 'steps.json', limits]
bound = {str(p): sha(p) for p in files}
write(q / 'registration.json', dict(pid=os.getpid(), start_ticks=process_identity(os.getpid())['start_ticks'],
      prior=str(prior), source_sha256=bound,
      question='Continue the already selected second current-STA step after distinguishing exact physical/effective input identity from observer/runtime provenance.',
      preserved='Same original resource root, immutable2061627wire/79SB/5061CB limits, proposal ranking, native search kernel/objective, current-STA target updates and full-precision CPD/hold/native/physical acceptance. First accepted step and completed selector/query/portfolio evidence are reused; no repeated native transaction.',
      change='New transaction preparation guard checks exact architecture/circuit/RRG/packing/placement bytes, normalized effective parameters and constraints. Runtime/observer/history are separately hashed provenance. Three physical-mismatch controls pass; real failed plan now prepares with0native.',
      qualification='Independent recovery version, not an in-place edit of the completed failed batch or one synthetic cold timing point. Saved accepted state/budgets/visited set preserved. No research date/count/matrix stop.',
      limits=dict(native_VPR_this_chain=1, child_seconds=1800, memory_bytes=64 * 1024**3, disk_reserve_bytes=80 * 1024**3)))
command = [sys.executable, str(D / 'run_independent_critical_portfolio_v3.py'), '--initial-state', str(anchor),
           '--batch', str(b / 'timing'), '--query-graph', str(D / 'bnn_physical_query_graph_01'),
           '--audit-cache', str(D / 'rr_audit_cache_bnn_01'), '--policy', 'timing_under_resources',
           '--budget-mode', 'explicit_absolute', '--fixed-limits', str(limits), '--resume-from', str(prior)]
started = time.monotonic()
with (q / 'timing.log').open('w') as log:
    proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    write(q / 'status.json', dict(status='resuming_own_current_timing_same_absolute_budgets', pid=proc.pid,
          start_ticks=process_identity(proc.pid)['start_ticks'], command=command, observed_at=time.time()))
    code = proc.wait()
receipt = b / 'timing/completion.json'
write(q / 'completion.json', dict(passed=code == 0 and receipt.exists() and read(receipt)['passed'], returncode=code,
      complete_resume_segment_seconds=time.monotonic() - started, complete_single_configuration_algorithm_seconds=None,
      historical_creation_time_borrowed=False, source_sha256=bound,
      qualification='Resume segment only; old failed/accepted work preserved separately. Continuous goal remains active regardless of this operator outcome.'))
