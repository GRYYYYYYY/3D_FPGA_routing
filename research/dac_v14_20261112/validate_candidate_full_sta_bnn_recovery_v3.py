#!/usr/bin/env python3
"""One actual fused BNN candidate, independent physical audit/LOAD and exact source recovery."""
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
from candidate_full_sta_analysis_pool import NativeAnalysisPool
from pool_state_evaluator_v5 import PoolStateEvaluator
from sealed_native_pool_replay import SealedNativePoolReplay
from run_native_scope_policy_v4 import run_dir
from endpoint_timing_policy import load, decide as timing_decide
from multiobjective_acceptance_v2 import decide
from coordinated_repair_tree import from_trace
sys.path.insert(0, str(D.parents[1] / 'scripts'))
from check_route import read_trace

b = D / 'candidate_full_sta_bnn_03'
b.mkdir(exist_ok=False)
lock = (b / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
started = time.monotonic()
resource.setrlimit(resource.RLIMIT_AS, (64 * 1024**3, 64 * 1024**3))
assert read(D / 'candidate_full_sta_tiny_01/completion.json')['passed']
assert read(D / 'candidate_observation_view_validation_01/completion.json')['passed']
assert (D / 'uniform_feedback_resource_dev_01/queue/completion.json').exists(), 'Prior owner terminal receipt required; unrelated actor failure does not invalidate this independent known-scope check'
old = D / 'automatic_domain_release_dev_01'
original_tx = old / 'round_000/candidate_00'
oldrole = read(original_tx / 'registration.json')['roles']['automatic_release']
initial = Path(oldrole['state'])
source = run_dir(initial)
reference = Path(read(old / 'completion.json')['final_state'])
command = list(read(source / 'manifest.json')['command'])
command[0] = str(D / 'candidate_full_sta_stage_01/bin/vpr')
if '--route' in command:
    command.remove('--route')
for option, name in [('--net_file', 'packed.net'), ('--place_file', 'placed.place'), ('--route_file', 'routed.route')]:
    command[command.index(option) + 1] = str(source / name)
if '--verify_route_file_switch_id' not in command:
    command += ['--verify_route_file_switch_id', 'on']
static = [Path(command[1]), Path(command[2]), Path(command[command.index('--read_rr_graph') + 1]), source / 'packed.net', source / 'placed.place']
guard = D.parents[1] / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard'
files = [Path(__file__).resolve(), D / 'candidate_full_sta_analysis_pool.py', D / 'pool_state_evaluator_v5.py',D/'candidate_full_sta_bnn_02/evaluation_context/input_seal.json',D/'candidate_full_sta_bnn_02/transaction/fused_audit/analysis.json',D/'candidate_full_sta_bnn_02/transaction/fused_domain_audit.json',D/'sealed_native_pool_replay.py',D/'candidate_full_sta_bnn_01/pool/completion.json',
         D / 'audit_native_feedback_objective_cached.py', D / 'audit_failure_release_domain.py',
         D / 'candidate_full_sta_stage_01/binding.json', D / 'candidate_full_sta_tiny_01/completion.json',
         D / 'candidate_observation_view_validation_01/completion.json', D / 'uniform_feedback_resource_dev_01/queue/completion.json',
         original_tx / 'registration.json', reference / 'completion.json', reference / 'endpoint_vector.json',
         initial / 'completion.json', initial / 'endpoint_vector.json', source / 'routed.route']
bound = {str(p): sha(p) for p in files}
write(b / 'registration.json', dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
      initial_state=str(initial), reference=str(reference), source_sha256=bound,
      question='Does the fused actual-candidate native FULL/freshSTA exactly match an independent same-binary route LOAD and the prior sealed selective-domain point, with unchanged restored source and all physical/scope/capacity checks?',
      qualification='Engineering integration on a known eight-cut scope, not a new quality configuration or a complete-algorithm speedup. Current quality cohort must be terminal before this second large loaded context starts. One fused worker plus separate validation-only candidate/source LOAD controls; those extra controls are not counted as algorithm calls.',
      limits=dict(child_seconds=1800, memory_bytes=64 * 1024**3, disk_reserve_bytes=80 * 1024**3)))
tx = b / 'transaction'
tx.mkdir()
request = tx / 'request.txt'
domain = tx / 'domain.txt'
shutil.copy2(oldrole['request'], request)
shutil.copy2(oldrole['crossing_domain'], domain)
role = dict(oldrole, request=str(request), crossing_domain=str(domain), domain_failure_release=True,
            source_sha256={str(p): sha(p) for p in [initial / 'completion.json', initial / 'endpoint_vector.json', source / 'routed.route', request, domain]})
write(tx / 'registration.json', dict(roles={'fused': role}, source_sha256={str(b / 'registration.json'): sha(b / 'registration.json')}))
costs = []
def persist():
    write(b / 'process_costs.json', costs)
def invoke(script, args, tag):
    assert shutil.disk_usage(D).free >= 80 * 1024**3
    t = time.monotonic()
    with (b / (tag + '.log')).open('w') as log:
        proc = subprocess.Popen([sys.executable, str(D / script), *map(str, args)], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(b / 'active_child.json', dict(pid=proc.pid, start_ticks=Path('/proc', str(proc.pid), 'stat').read_text().split(') ', 1)[1].split()[19], tag=tag))
        try:
            code = proc.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            raise
    costs.append(dict(tag=tag, returncode=code, complete_process_seconds=time.monotonic() - t))
    persist()
    assert code == 0, tag
def vector_equal(a, c):
    return all(a[k] == c[k] for k in ['cpd_s','setup','hold','constraints_sha256']) and list(map(tuple,a['endpoint_ids']))==list(map(tuple,c['endpoint_ids']))
def structure(path):
    return {n: from_trace(x['trace'], collections.defaultdict(float)) if x['trace'] else None for n, x in read_trace(path).items()}
def physical(state):
    p = read(run_dir(state) / 'independent_audit.json')['physical_metrics']
    return dict(wirelength=p['planar_wirelength_excluding_sb_half_nodes'], SB_pairs=p['sb_pairs_used'], CB_sources=p['cb_crossing_output_sources_used'])
persist()
sealed=SealedNativePoolReplay(D/'candidate_full_sta_bnn_01/pool')
pool = NativeAnalysisPool(b / 'validation_only_pool', command, static, guard)
evaluator = PoolStateEvaluator(sealed, initial, D / 'full_route_graph_cache_bnn_01', b / 'evaluation_context')
try:
    t = time.monotonic()
    worker=read(D/'candidate_full_sta_bnn_01/transaction/fused_worker_receipt.json');assert worker['passed'] and worker['static_identity']==sealed.identity
    assert sha(request)==worker['native_options']['inputs']['native_request.txt'] and sha(domain)==worker['native_options']['inputs']['crossing_domain.txt']
    assert sha(source/'routed.route')==worker['route_sha256']
    costs.append(dict(tag='exact_sealed_fused_worker_reuse_zero_native_no_creation_time_borrowed', complete_process_seconds=time.monotonic() - t))
    persist()
    assert worker['passed'] and worker['candidate_full_STA_passed']
    write(tx / 'fused_worker_receipt.json', worker)
    native = Path(worker['native_directory'])
    original_vector = read(initial / 'endpoint_vector.json')
    assert vector_equal(load(native / 'native_sta_frontier.jsonl'), original_vector)
    view = evaluator.candidate_observation(worker)
    write(tx / 'fused_candidate_view.json', view)
    # Version02 already sealed the exact source observation and real transaction/domain audits.
    # Reuse those passed artifacts rather than rerunning physical transaction reconstruction.
    prior=D/'candidate_full_sta_bnn_02'
    assert read(prior/'evaluation_context/input_seal.json')['passed']
    prior_source=prior/'transaction/fused'
    assert read(prior_source/'completion.json')['passed']
    assert read(prior_source/'registration.json')['native_receipt_sha256']==sha(Path(worker['job'])/'completion.json')
    for suffix in ['fused_audit/analysis.json','fused_domain_audit.json']:
        report=read(prior/'transaction'/suffix);assert report['passed']
        assert all(sha(p)==h for p,h in report['source_sha256'].items())
    shutil.copytree(prior_source,tx/'fused')
    shutil.copytree(prior/'transaction/fused_audit',tx/'fused_audit')
    shutil.copy2(prior/'transaction/fused_domain_audit.json',tx/'fused_domain_audit.json')
    write(tx/'exact_audit_reuse.json',dict(passed=True,source=str(prior/'transaction'),source_context_seal=str(prior/'evaluation_context/input_seal.json'),same_source_request_and_native_artifacts=True,native_calls=0,new_transaction_audit_calls=0,creation_time_borrowed=False,source_sha256={str(p):sha(p)for p in[prior/'evaluation_context/input_seal.json',prior_source/'registration.json',prior_source/'completion.json',prior/'transaction/fused_audit/analysis.json',prior/'transaction/fused_domain_audit.json']}))
    audit = read(tx / 'fused_audit/analysis.json')
    assert audit['passed'] and audit.get('candidate_route')
    actual_route = Path(view['installed_candidate_identity']['actual_route'])
    # Serialization order/header may differ. Compare every actual tree edge and terminal.
    assert structure(actual_route) == structure(audit['candidate_route']) == structure(run_dir(reference) / 'routed.route')
    assert structure(native / 'candidate_restored/routed.route') == structure(source / 'routed.route')
    candidate = b / 'candidate_evaluation'
    t = time.monotonic()
    result = evaluator.evaluate(actual_route, candidate, native_observation=view)
    costs.append(dict(tag='actual_candidate_materialization_and_full_independent_physical_audit_no_extra_native', complete_process_seconds=time.monotonic() - t))
    persist()
    assert result['passed'] and result['native_analysis_calls'] == 0
    after = read(candidate / 'endpoint_vector.json')
    assert vector_equal(after, read(reference / 'endpoint_vector.json'))
    assert physical(candidate) == physical(reference)
    algorithm_prefix = time.monotonic() - started
    write(b / 'actual_candidate_prefix.json', dict(passed=True, candidate=str(candidate), actual_candidate_native_calls=0,
          actual_fused_search_native_calls=0,reused_fused_native_workers=1, elapsed_prefix_seconds=algorithm_prefix,
          qualification='Measured recovery prefix consuming an already sealed fused worker, before new independent validation controls and final context sealing. Old native creation time explicitly excluded. Not complete routing+repair or a cold-algorithm timing result.'))
    t = time.monotonic()
    independent = pool.analyze(actual_route, reuse=False)
    assert independent['passed']
    comparison_dir = Path(independent['native_directory'])
    for name in ['native_sta_frontier.jsonl', 'native_sta_frontier.jsonl.constraints.echo', 'timing_graph.full_precision.echo']:
        assert sha(native / 'candidate' / name) == sha(comparison_dir / name)
    costs.append(dict(tag='validation_only_same_binary_independent_candidate_LOAD_FULLSTA', complete_process_seconds=time.monotonic() - t))
    t = time.monotonic()
    following = pool.analyze(source / 'routed.route', reuse=False)
    assert following['passed']
    for name in ['native_sta_frontier.jsonl', 'native_sta_frontier.jsonl.constraints.echo', 'timing_graph.full_precision.echo']:
        assert sha(native / name) == sha(Path(following['native_directory']) / name)
    costs.append(dict(tag='validation_only_following_original_source_LOAD_FULLSTA', complete_process_seconds=time.monotonic() - t))
    decisions = dict(resources_under_timing=decide('resources_under_timing', original_vector, after, physical(initial), physical(candidate),
        cpd_limit_s=read(original_tx / 'registration.json')['anchor']['CPD_s'], resource_limits=read(original_tx / 'registration.json')['anchor']['resource_limits'],
        native_valid=True, transaction_complete=True, resource_objectives=('SB_pairs', 'CB_sources')),
        strict=timing_decide('strict', original_vector, after, True), endpoint_vector=timing_decide('endpoint_vector', original_vector, after, True))
    write(b / 'decisions.json', decisions)
    assert decisions['resources_under_timing']['accepted']
finally:
    persist()
    t = time.monotonic()
    evaluator.close()
    pool.close()
    costs.append(dict(tag='final_native_context_and_cache_seal', complete_process_seconds=time.monotonic() - t))
    persist()
assert all(sha(p) == h for p, h in bound.items())
write(b / 'completion.json', dict(passed=True, candidate_state=str(candidate), CPD_s=after['cpd_s'], resources=physical(candidate),
      actual_candidate_and_prior_reference_tree_structure_exact=True, actual_candidate_native_FULL_and_fresh_STA=True,
      actual_candidate_exports_independent_same_binary_LOAD_exact=True, restored_and_following_original_source_exports_exact=True,
      full_scope_resource_physical_checks=True, new_fused_algorithm_worker_calls=0,reused_fused_algorithm_workers=1, additional_validation_only_native_calls=2,
      new_native_pool_new_validation_children=len(pool.jobs), native_kernel_including_candidate_observation_seconds=audit['native_transaction_seconds'],native_connection_queries_seconds=sum(row['seconds'] for row in audit['queries']),
      measured_algorithm_prefix_seconds=algorithm_prefix, complete_recovery_segment_engineering_validation_seconds=time.monotonic() - started,
      complete_single_configuration_algorithm_seconds=None,
      source_sha256={str(p): sha(p) for p in [b / 'registration.json', b / 'process_costs.json', b / 'decisions.json',
          b / 'actual_candidate_prefix.json', b / 'validation_only_pool/completion.json', b / 'evaluation_context/input_seal.json', b / 'evaluation_context/completion.json']},
      qualification='Recovered immutable actual fused native candidate evidence plus new independent candidate/source LOAD validation. Version01 failed list/tuple comparison and zero-state cleanup. Version02 retained an inapplicable six-digit printed-CPD check for an explicit full-precision candidate view; all native gate/vector/source and scope checks passed. Version03 separates printed-source consistency from dedicated candidate-vector identity and exactly reuses passed transaction/domain audits. Old failed attempts preserved, no native search repeated. This segment is not a fresh fused run or end-to-end speed measurement. Reference is the already-known selective-domain quality point, not a new frontier configuration. Whole validation includes extra control jobs; measured prefix excludes final sealing and is not a complete algorithm timing point. Full cold routing+repair remains unknown.'))
print(dict(passed=True, resources=physical(candidate), new_validation_children=len(pool.jobs)), flush=True)
