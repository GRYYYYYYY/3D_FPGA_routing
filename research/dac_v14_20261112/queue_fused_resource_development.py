#!/usr/bin/env python3
"""After paired integration gates, run own-current resource strategies to a local fixed menu."""
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from export_policy_analysis_pool import process_identity

q = D / 'fused_resource_development_01/queue'
q.mkdir(parents=True, exist_ok=False)
lock = (q / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
prior = D / 'export_policy_large_queue_01'
owner = read(prior / 'registration.json')
cases = read(D / 'uniform_feedback_resource_dev_01/queue/registration.json')['cases']
assert read(D / 'actual_route_tree_identity_validation_01.json')['passed']
files = [Path(__file__).resolve(), D / 'run_fused_resource_bundle_repair_v2.py', D / 'export_policy_analysis_pool.py',
         D / 'pool_state_evaluator_v7.py', D / 'endpoint_timing_policy_streaming_v2.py', D / 'actual_route_tree_identity.py',
         D / 'actual_route_tree_identity_validation_01.json', D / 'export_policy_stage_01/binding.json',
         D / 'fused_resource_actor_preparation_02.json', D / 'current_crossing_share_selector_v2.py',
         D / 'current_resource_bundle_v2.py', D / 'multiobjective_acceptance_v2.py', prior / 'registration.json',
         D / 'uniform_feedback_resource_dev_01/queue/registration.json']
bound = {str(path): sha(path) for path in files}
write(q / 'registration.json', dict(pid=os.getpid(), start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bound, cases=cases, prerequisite_owner=dict(pid=owner['pid'], start_ticks=owner['start_ticks']),
    question='Can the validated compact/fused backend sustain automatic own-current resource selection and exact physical/FULLSTA acceptance, and does continuation beyond the old two-accept pilot expose additional legal resource savings?',
    parameters=dict(bundle_size=8, rank_windows=3, minimum_margin_s=.2e-9, accepted_steps=0,
        zero_accepted_steps_means='Continue until no admissible move in the registered current three-window menu; not exhaustive or an overall research stop',
        root_CPD_cap='exact native full precision', wire='root+0.1percent', vertical='no root increase', graph_echo='compact'),
    native_control='Same pristine root per circuit, deterministic current selector, grouping, full device range, allowed tree scope, objective, physical/STA gates, fixed budgets and menu exhaustion rule; unrestricted native-only and paired-domain feedback then follow their own accepted states. Paired strategy evaluates both OFF/ON and may release failed domains; extra searches and failures are fully charged, not claimed equal compute.',
    reason_for_repeated_prefix='New backend actual-candidate integration and whole imported-workflow overhead test; original two-step prefix is a quality equivalence reference, never a borrowed time. New continuation has an explicit different local stopping rule and is a separate configuration.',
    limits=dict(combined_VPR_maximum=3, this_chain_parent_plus_child=2, current_timing_chain_maximum=1,
        child_seconds=1800, memory_bytes=64*1024**3, disk_reserve_bytes=80*1024**3),
    qualification='Independent development cohort from pristine strong A0 roots with uniform predeclared settings. Strong A0/R1/U/Tf remain in the joint population. Not broad frozen confirmation, not a history-best configuration or complete cold routing time. Previous jobs, artifacts and acceptance unchanged. Local failures preserved without ending other branches or the research goal.'))
write(q / 'status.json', dict(status='waiting_for_same_binary_large_export_proofs', observed_at=time.time()))
while True:
    actual = process_identity(owner['pid'])
    if not actual or actual['state'] == 'Z' or actual['start_ticks'] != owner['start_ticks']:
        break
    time.sleep(15)
assert (prior / 'completion.json').exists(), 'Prior owner ended without receipt; reconcile, no blind submission'
if not read(prior / 'completion.json')['passed']:
    write(q / 'completion.json', dict(passed=False, status='integration_prerequisite_not_passed_no_actor_submitted',
        source_sha256=bound, qualification='Inspect the concrete integration failure; no research goal stop.'))
    sys.exit(1)
for name in ['timing', 'resource']:
    assert read(D / ('export_policy_' + name + '_01/completion.json'))['passed']
started = time.monotonic()
results = {}
for name, case in cases.items():
    assert all(sha(path) == h for path, h in bound.items())
    output = q.parent / name
    command = [sys.executable, str(D / 'run_fused_resource_bundle_repair_v2.py'), '--initial-state', case['initial_state'],
        '--batch', str(output), '--full-graph-cache', case['full_graph_cache'], '--bundle-size', '8',
        '--domain-mode', case['domain_mode'], '--graph-echo', 'compact', '--accepted-steps', '0', '--rank-windows', '3']
    if case['domain_feedback']:
        command.append('--domain-feedback')
    t = time.monotonic()
    with (q / (name + '.log')).open('w') as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        write(q / 'status.json', dict(status='running', case=name, pid=child.pid,
            start_ticks=process_identity(child.pid)['start_ticks'], command=command))
        code = child.wait()
    receipt = output / 'completion.json'
    results[name] = dict(returncode=code, passed=code == 0 and receipt.exists() and read(receipt)['passed'],
        elapsed_seconds=time.monotonic() - t, completion=str(receipt))
    write(q / 'results.json', results)
write(q / 'completion.json', dict(passed=all(row['passed'] for row in results.values()), results=results,
    complete_imported_development_cohort_seconds=time.monotonic() - started,
    complete_single_configuration_algorithm_seconds=None, source_sha256=bound))
