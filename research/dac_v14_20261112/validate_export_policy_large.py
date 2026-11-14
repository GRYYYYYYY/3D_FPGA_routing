#!/usr/bin/env python3
"""Paired graph-text export, including an actual CPD-changing fused transaction."""
import argparse
import collections
import fcntl
import os
import resource
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from export_policy_analysis_pool import NativeAnalysisPool
from pool_state_evaluator_v7 import PoolStateEvaluator
from run_native_scope_policy_v4 import run_dir
from endpoint_timing_policy_streaming_v2 import load, compare, decide as timing_decide
from coordinated_repair_tree import from_trace
sys.path.insert(0, str(D.parents[1] / 'scripts'))
from check_route import read_trace

p = argparse.ArgumentParser()
p.add_argument('--case', choices=['timing', 'resource'], required=True)
a = p.parse_args()
b = D / ('export_policy_' + a.case + '_01')
b.mkdir(exist_ok=False)
lock = (b / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
started = time.monotonic()
resource.setrlimit(resource.RLIMIT_AS, (64 * 1024**3, 64 * 1024**3))
assert read(D / 'export_policy_tiny_01/completion.json')['passed']
if a.case == 'resource':
    original_tx = D / 'automatic_domain_release_dev_01/round_000/candidate_00'
    oldrole = read(original_tx / 'registration.json')['roles']['automatic_release']
    reference = Path(read(D / 'automatic_domain_release_dev_01/completion.json')['final_state'])
    order = [True, False]
else:
    original_tx = D / 'resource_first_timing_dev_01/timing/round_000/proposal_01/transaction'
    oldrole = read(original_tx / 'registration.json')['roles']['current_group']
    reference = original_tx / 'current_group_evaluation'
    order = [False, True]
initial = Path(oldrole['state'])
source = run_dir(initial)
assert oldrole['fixed_target_paths'] is False
command = list(read(source / 'manifest.json')['command'])
command[0] = str(D / 'export_policy_stage_01/bin/vpr')
if '--route' in command:
    command.remove('--route')
for flag, name in [('--net_file', 'packed.net'), ('--place_file', 'placed.place'), ('--route_file', 'routed.route')]:
    command[command.index(flag) + 1] = str(source / name)
if '--verify_route_file_switch_id' not in command:
    command += ['--verify_route_file_switch_id', 'on']
static = [Path(command[1]), Path(command[2]), Path(command[command.index('--read_rr_graph') + 1]), source / 'packed.net', source / 'placed.place']
guard = D.parents[1] / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard'
files = [Path(__file__).resolve(), D / 'export_policy_analysis_pool.py', D / 'pool_state_evaluator_v7.py',
         D / 'endpoint_timing_policy_streaming_v2.py', D / 'audit_native_feedback_objective_cached.py',
         D / 'audit_failure_release_domain.py', D / 'export_policy_stage_01/binding.json',
         D / 'export_policy_tiny_01/completion.json', original_tx / 'registration.json',
         initial / 'completion.json', initial / 'endpoint_vector.json', reference / 'completion.json',
         reference / 'endpoint_vector.json', source / 'routed.route', Path(oldrole['request'])]
if a.case == 'resource':
    files.append(Path(oldrole['crossing_domain']))
bound = {str(path): sha(path) for path in files}
write(b / 'registration.json', dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
      source_sha256=bound, case=a.case, initial_state=str(initial), reference_state=str(reference),
      order=['full' if v else 'compact' for v in order],
      question='Does omitting unused full timing graph text preserve actual source/candidate/restored FULL and fresh STA, every frontier/constraint byte, native search and physical candidate, including a real CPD-changing transaction?',
      qualification='New independent same-binary paired engineering experiment, original quality batch untouched. Full/compact use exactly the same physical inputs, scope, request, objective and acceptance. Native startup is prewarmed and recorded separately. Component timing only, no cold whole-algorithm speedup claim. Two extra native LOAD jobs are validation controls, not algorithm calls.',
      limits=dict(child_seconds=1800, memory_bytes=64 * 1024**3, disk_reserve_bytes=80 * 1024**3, combined_VPR_maximum=3)))
tx = b / 'transaction'
tx.mkdir()
request = tx / 'request.txt'
shutil.copy2(oldrole['request'], request)
domain = None
if a.case == 'resource':
    domain = tx / 'domain.txt'
    shutil.copy2(oldrole['crossing_domain'], domain)
role = dict(oldrole, request=str(request), domain_failure_release=a.case == 'resource',
            source_sha256={str(path): sha(path) for path in [initial / 'completion.json', initial / 'endpoint_vector.json', source / 'routed.route', request] + ([domain] if domain else [])})
if domain:
    role['crossing_domain'] = str(domain)
write(tx / 'registration.json', dict(roles={'observed': role}, source_sha256={str(b / 'registration.json'): sha(b / 'registration.json')}))
costs = []
def record(tag, start, **extra):
    costs.append(dict(tag=tag, complete_component_seconds=time.monotonic() - start, **extra))
    write(b / 'process_costs.json', costs)
def invoke(script, args, tag):
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    t = time.monotonic()
    with (b / (tag + '.log')).open('w') as log:
        child = subprocess.Popen([sys.executable, str(D / script), *map(str, args)], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(b / 'active_child.json', dict(pid=child.pid, start_ticks=Path('/proc', str(child.pid), 'stat').read_text().split(') ', 1)[1].split()[19], tag=tag))
        try:
            code = child.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            raise
    record(tag, t, returncode=code)
    assert code == 0, tag
def same_vector(left, right):
    return all(left[k] == right[k] for k in ['cpd_s', 'setup', 'hold', 'constraints_sha256']) and list(map(tuple, left['endpoint_ids'])) == list(map(tuple, right['endpoint_ids']))
def structure(path):
    return {n: from_trace(x['trace'], collections.defaultdict(float)) if x['trace'] else None for n, x in read_trace(path).items()}
def physical(state):
    r = read(run_dir(state) / 'independent_audit.json')['physical_metrics']
    return dict(wirelength=r['planar_wirelength_excluding_sb_half_nodes'], SB_pairs=r['sb_pairs_used'], CB_sources=r['cb_crossing_output_sources_used'])
def normalized(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        row = line.split()
        if row[0] == 'QUERY':
            row = row[:-1]
        if row[0] == 'COMPLETE':
            row = row[:4] + row[5:]
        rows.append(row)
    return rows

pool = NativeAnalysisPool(b / 'pool', command, static, guard)
evaluator = PoolStateEvaluator(pool, initial, D / 'full_route_graph_cache_bnn_01', b / 'evaluation_context')
workers = {}
candidates = {}
try:
    t = time.monotonic()
    pool._ensure_epoch()
    record('native_parent_startup_before_paired_requests', t)
    original_vector = read(initial / 'endpoint_vector.json')
    for echo in order:
        name = 'full' if echo else 'compact'
        write(b / 'status.json', dict(phase='paired_native_request', variant=name, pid=os.getpid()))
        t = time.monotonic()
        worker = pool.analyze(source / 'routed.route', echo=echo, reuse=False, native_request=request,
                              objective=role['objective'], crossing_domain=domain,
                              domain_failure_release=bool(domain), candidate_full_sta=True)
        record(name + '_fused_native_request', t, native_child_seconds=worker['native_child_seconds'],
               complete_request_seconds=worker['complete_request_seconds'], max_rss_kib=worker['max_rss_kib'])
        write(tx / (name + '_worker.json'), worker)
        assert worker['passed'] and worker['candidate_full_STA_passed'] and worker['native_transaction_succeeded']
        assert worker['full_timing_echo_requested'] is echo
        native = Path(worker['native_directory'])
        assert same_vector(load(native / 'native_sta_frontier.jsonl'), original_vector)
        view = evaluator.candidate_observation(worker)
        write(tx / (name + '_view.json'), view)
        workers[echo] = worker
        if len(workers) == 1:
            t = time.monotonic()
            assert evaluator.evaluate(source / 'routed.route', tx / 'observed', physical_reference=initial, native_observation=worker)['passed']
            record('source_materialization_with_exact_prior_physical_audit_reuse', t)
            invoke('audit_native_feedback_objective_cached.py', ['--batch', tx, '--role', 'observed', '--cache', D / 'rr_audit_cache_bnn_01', '--output', tx / 'observed_audit'], 'independent_scope_capacity_reconstruction')
            if domain:
                invoke('audit_failure_release_domain.py', ['--batch', tx, '--role', 'observed'], 'independent_failure_release_domain_trace')
            audit = read(tx / 'observed_audit/analysis.json')
            assert audit['passed'] and audit.get('candidate_route')
            assert structure(view['native_directory'] + '/routed.route') == structure(audit['candidate_route']) == structure(run_dir(reference) / 'routed.route')
            assert structure(native / 'candidate_restored/routed.route') == structure(source / 'routed.route')
        candidate = b / (name + '_evaluation')
        t = time.monotonic()
        # The second variant may reuse the first exact-byte candidate physical audit.
        # Native gates/vector parsing/manifest/scope equality still checked separately.
        exact_reference = next(iter(candidates.values())) if candidates else None
        result = evaluator.evaluate(Path(view['native_directory']) / 'routed.route', candidate,
                                    native_observation=view, physical_reference=exact_reference)
        record(name + '_candidate_materialization', t, physical_audit_reused=result['physical_audit_reused'])
        assert result['passed'] and result['native_analysis_calls'] == 0
        after = read(candidate / 'endpoint_vector.json')
        assert same_vector(after, read(reference / 'endpoint_vector.json'))
        assert physical(candidate) == physical(reference)
        assert read(run_dir(candidate) / 'manifest.json')['can_select_timing_cone'] is echo
        candidates[echo] = candidate
        write(b / 'progress.json', dict(workers=workers, candidates={str(k): str(v) for k, v in candidates.items()}))
    f, c = (Path(workers[v]['native_directory']) for v in [True, False])
    assert normalized(f / 'joint_native.log') == normalized(c / 'joint_native.log')
    for part in ['.', 'candidate', 'candidate_restored']:
        for name in ['native_sta_frontier.jsonl', 'native_sta_frontier.jsonl.constraints.echo']:
            assert sha(f / part / name) == sha(c / part / name)
        assert (f / part / 'timing_graph.full_precision.echo').is_file()
        assert not (c / part / 'timing_graph.full_precision.echo').exists()
        if part != '.':
            for name in ['routed.route', 'native_state_gate.txt']:
                assert sha(f / part / name) == sha(c / part / name)
    if domain:
        assert (f / 'vertical_domain.log').read_bytes() == (c / 'vertical_domain.log').read_bytes()
    after = read(candidates[False] / 'endpoint_vector.json')
    comparison = compare(original_vector, after)
    strict = timing_decide('strict', original_vector, after, True)
    assert strict['accepted'] is (a.case == 'timing')
    write(b / 'decisions.json', dict(strict=strict, comparison=comparison,
          qualification='Diagnostic acceptance of this fixed existing transaction, not an auto-selector trajectory. Resource case intentionally CPD-flat; timing case strictly improving.'))
    # Independent candidate LOAD with full graph; following original source compact.
    # These are extra validation jobs, never included as algorithm native calls.
    t = time.monotonic()
    independent = pool.analyze(c / 'candidate/routed.route', echo=True, reuse=False)
    assert independent['passed']
    for name in ['native_sta_frontier.jsonl', 'native_sta_frontier.jsonl.constraints.echo', 'timing_graph.full_precision.echo']:
        assert sha(f / 'candidate' / name) == sha(Path(independent['native_directory']) / name)
    record('validation_only_independent_candidate_LOAD_FULLSTA', t)
    t = time.monotonic()
    following = pool.analyze(source / 'routed.route', echo=False, reuse=False)
    assert following['passed']
    for name in ['native_sta_frontier.jsonl', 'native_sta_frontier.jsonl.constraints.echo']:
        assert sha(f / name) == sha(Path(following['native_directory']) / name)
    record('validation_only_following_original_source_LOAD_FULLSTA', t)
finally:
    t = time.monotonic()
    evaluator.close()
    record('final_native_context_cache_input_seal', t)
assert all(sha(path) == h for path, h in bound.items())
sizes = {}
for echo, worker in workers.items():
    native = Path(worker['native_directory'])
    sizes['full' if echo else 'compact'] = dict(
        graph_echo_bytes=sum(p.stat().st_size for p in native.rglob('timing_graph.full_precision.echo')),
        frontier_bytes=sum(p.stat().st_size for p in native.rglob('native_sta_frontier.jsonl')),
        native_child_seconds=worker['native_child_seconds'], request_seconds=worker['complete_request_seconds'],
        max_rss_kib=worker['max_rss_kib'])
write(b / 'completion.json', dict(passed=True, case=a.case, CPD_before_ns=original_vector['cpd_s'] * 1e9,
      CPD_after_ns=after['cpd_s'] * 1e9, resources=physical(candidates[False]), component_measurements=sizes,
      full_compact_actual_routes_searches_frontiers_constraints_exact=True, actual_native_FULL_fresh_STA=True,
      independent_candidate_LOAD_frontier_graph_exact=True, restored_and_following_source_exact=True,
      physical_scope_and_capacity_checks=True, paired_fused_native_workers=2, additional_validation_only_LOAD_calls=2,
      complete_engineering_validation_seconds=time.monotonic() - started, complete_single_configuration_algorithm_seconds=None,
      source_sha256={str(path): sha(path) for path in [b / 'registration.json', b / 'process_costs.json', b / 'decisions.json',
          b / 'pool/completion.json', b / 'evaluation_context/input_seal.json', tx / 'observed_audit/analysis.json']},
      qualification='One same-binary paired measurement per existing known transaction. Opposite full/compact order across resource/timing cases is a diagnostic, not repeated formal timing. Paired requests exclude recorded shared startup; final sealing and extra independent LOAD controls included only in whole validation cost. Second exact-byte physical audit reuse is explicit. No new quality point, no cold single-configuration runtime or algorithm speedup claim. Forced target path operator not covered.'))
print(dict(passed=True, case=a.case, CPD_ns=after['cpd_s'] * 1e9, sizes=sizes), flush=True)
