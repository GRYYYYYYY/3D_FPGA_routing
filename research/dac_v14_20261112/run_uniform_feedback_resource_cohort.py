#!/usr/bin/env python3
"""Prospective own-current native/feedback K8 from two pristine native roots."""
import fcntl
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from native_feedback_analysis_pool import process_identity

b = D / 'uniform_feedback_resource_dev_01'
queue = b / 'queue'
queue.mkdir(parents=True, exist_ok=False)
lock = (queue / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
proof = D / 'automatic_domain_release_dev_01/completion.json'
assert read(proof)['passed']
cases = {}
for circuit, source, cache in [
    ('eltwise_A0', D / 'native_endpoint_vector_dev_01/A0', D / 'full_route_graph_cache_e695_01'),
    ('bnn_A0', D / 'native_extra_opportunity_bnn_01/A0_observation', D / 'full_route_graph_cache_bnn_01'),
]:
    assert read(source / 'completion.json')['passed']
    for mode in ['native_only', 'feedback']:
        cases[circuit + '_' + mode + '_K8'] = dict(initial_state=str(source), full_graph_cache=str(cache),
            bundle_size=8, domain_mode='unrestricted' if mode == 'native_only' else 'paired',
            domain_feedback=mode == 'feedback',
            source_sha256={str(p): sha(p) for p in [source / 'completion.json', source / 'endpoint_vector.json', cache / 'completion.json']})
files = [Path(__file__).resolve(), D / 'run_pooled_feedback_bundle_repair.py',
         D / 'native_feedback_analysis_pool.py', D / 'pool_state_evaluator_v2.py',
         D / 'audit_native_feedback_objective_cached.py', D / 'audit_retained_crossing_domain.py',
         D / 'audit_failure_release_domain.py', D / 'current_crossing_share_selector_v2.py',
         D / 'current_resource_bundle_v2.py', D / 'multiobjective_acceptance_v2.py',
         D / 'domain_failure_release_stage_01/binding.json', proof]
bound = {str(p): sha(p) for p in files}
write(queue / 'registration.json', dict(pid=os.getpid(), start_ticks=process_identity(os.getpid())['start_ticks'],
      cases=cases, source_sha256=bound,
      question='Does automatic own-current K8 resource repair transfer from pristine strong native A0 roots, and what does selective native feedback add beyond the same-source/scope/objective/search/opportunity native-only strategy?',
      policy='Both circuits use K8 distinct-net rank windows, exact rootCPD cap, rootwire+0.1% and no vertical increase. Native-only and paired-feedback each reselect on their own committed states after divergence. Paired feedback evaluates OFF and ON at each current source, prefers admissible ON else OFF; releases failed net domains internally. No manual target list or accepted repair prefix.',
      local_probe=dict(accepted_steps=2, rank_windows=3),
      limits=dict(native_workers_at_once=1, child_seconds=1800, memory_bytes=64 * 1024**3, disk_reserve_bytes=80 * 1024**3),
      qualification='New independent development cohort after complete tiny/BNN validation. Original jobs and artifacts untouched. Same uniform parameters across these circuits, not yet broad confirmation or cold timing. No old-history time or per-circuit best configuration chosen. Completion of this local probe is not completion of research.'))
results = []
for name, case in cases.items():
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    assert all(sha(p) == h for p, h in bound.items())
    assert all(sha(p) == h for p, h in case['source_sha256'].items())
    command = [sys.executable, str(D / 'run_pooled_feedback_bundle_repair.py'), '--batch', str(b / name),
               '--initial-state', case['initial_state'], '--full-graph-cache', case['full_graph_cache'],
               '--bundle-size', '8', '--domain-mode', case['domain_mode']]
    if case['domain_feedback']:
        command.append('--domain-feedback')
    started = time.monotonic()
    with (queue / (name + '.log')).open('w') as log:
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        write(queue / 'status.json', dict(status='running', actor=name, pid=proc.pid,
              start_ticks=process_identity(proc.pid)['start_ticks'], observed_at=time.time(), command=command))
        code = proc.wait()
    result = dict(actor=name, returncode=code, complete_process_seconds=time.monotonic() - started)
    receipt = b / name / 'completion.json'
    result['passed'] = code == 0 and receipt.exists() and read(receipt)['passed']
    results.append(result)
    write(queue / 'steps.json', results)
    # A failed actor is recorded; independent remaining roots/arms still run.
write(queue / 'completion.json', dict(passed=all(r['passed'] for r in results), actors=results,
      source_sha256=bound, qualification='Uniform local development probe terminal; continuous research stays active. Interpret quality/resource/time and failures before selecting another intervention.'))
