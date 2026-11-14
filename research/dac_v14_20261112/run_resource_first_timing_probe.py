#!/usr/bin/env python3
"""Use the sealed automatic resource-first phase, then timing under its tighter vertical cap."""
import fcntl
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from run_native_scope_policy_v4 import run_dir

b = D / 'resource_first_timing_dev_01'
q = b / 'queue'
q.mkdir(parents=True, exist_ok=False)
lock = (q / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
phase = D / 'uniform_feedback_resource_dev_01/bnn_A0_feedback_K8'
c = read(phase / 'completion.json')
assert c['passed'] and all(sha(p) == h for p, h in c['source_sha256'].items())
initial = Path(c['final_state'])
pristine = Path(c['initial_state'])
root = read(run_dir(pristine) / 'independent_audit.json')['physical_metrics']
assert read(initial / 'endpoint_vector.json')['constraints_sha256'] == read(pristine / 'endpoint_vector.json')['constraints_sha256']
assert c['final_CPD_s'] == read(pristine / 'endpoint_vector.json')['cpd_s']
limits = dict(wirelength=(root['planar_wirelength_excluding_sb_half_nodes'] * 1001 + 999) // 1000,
              SB_pairs=c['final_resources']['SB_pairs'], CB_sources=c['final_resources']['CB_sources'])
write(b / 'absolute_limits.json', limits)
files = [Path(__file__).resolve(), D / 'run_independent_critical_portfolio_v2.py', D / 'run_registered_independent_transactions.py',
         D / 'current_group_feedback_cached.py', D / 'current_native_reuse_resource.py', D / 'multiobjective_acceptance_v2.py',
         phase / 'completion.json', phase / 'registration.json', initial / 'completion.json', initial / 'endpoint_vector.json',
         pristine / 'completion.json', pristine / 'endpoint_vector.json', b / 'absolute_limits.json']
bound = {str(p): sha(p) for p in files}
write(q / 'registration.json', dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
      pristine_start=str(pristine), exact_reused_automatic_resource_phase=str(phase), timing_initial_state=str(initial),
      fixed_absolute_resource_limits=limits, source_sha256=bound,
      question='After automatic slack-based K8 release from pristine strong A0 saves15SB and1CB with flat CPD, can the current-STA timing selector reduce CPD while preserving that tighter79SB/5061CB envelope? Does ordering these mechanisms change the observed attainable quality?',
      controls='Existing timing-first then K8 trajectories are separately sealed. Do not claim exact phase commutation from equal resource deltas; this new timing phase selects its own current targets. This is a composition diagnostic, not a new frozen confirmation score.',
      qualification='Reuse the already fully sealed automatic first phase, never a manually supplied target or accepted timing prefix. Wire envelope is anchored at the ORIGINAL pristine root, not inflated by restarting0.1% at the resource successor. Every timing move has strict full-precision CPD gain and native/physical checks. Existing loaded large validation at most2VPR plus this serial chain at most1VPR; cold whole-algorithm time remains unknown.',
      limits=dict(native_VPR_this_chain=1, combined_native_VPR_maximum=3, child_seconds=1800, memory_bytes=64 * 1024**3, disk_reserve_bytes=80 * 1024**3)))
assert shutil.disk_usage(D).free >= 80 * 1024**3
command = [sys.executable, str(D / 'run_independent_critical_portfolio_v2.py'), '--initial-state', str(initial),
           '--batch', str(b / 'timing'), '--query-graph', str(D / 'bnn_physical_query_graph_01'),
           '--audit-cache', str(D / 'rr_audit_cache_bnn_01'), '--policy', 'timing_under_resources',
           '--budget-mode', 'explicit_absolute', '--fixed-limits', str(b / 'absolute_limits.json')]
for history in [D / 'strong_A0_timing_trajectories_01/strict', D / 'strong_A0_timing_trajectories_01/fixed_vertical']:
    for query in history.glob('round_*/feedback/capacity'):
        command += ['--reuse-query-batch', str(query)]
started = time.monotonic()
with (q / 'timing.log').open('w') as log:
    proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    write(q / 'status.json', dict(status='running_timing_under_original_root_wire_and_post_resource_vertical_caps', pid=proc.pid,
          start_ticks=Path('/proc', str(proc.pid), 'stat').read_text().split(') ', 1)[1].split()[19], observed_at=time.time(), command=command))
    code = proc.wait()
assert all(sha(p) == h for p, h in bound.items())
write(q / 'completion.json', dict(passed=code == 0 and (b / 'timing/completion.json').exists() and read(b / 'timing/completion.json')['passed'],
      returncode=code, complete_current_timing_segment_seconds=time.monotonic() - started,
      reused_resource_phase_creation_time_borrowed=False, complete_single_configuration_algorithm_seconds=None,
      source_sha256=bound, qualification='Composition probe terminal only; whole research continues. Native failures/rejections and phase/cost identities preserved.'))
