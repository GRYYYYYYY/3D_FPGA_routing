#!/usr/bin/env python3
"""Same-binary full/compact output policy with real source/candidate FULLSTA and failures."""
import copy
import os
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from export_policy_analysis_pool import NativeAnalysisPool
from pool_state_evaluator_v7 import PoolStateEvaluator

b = D / 'export_policy_tiny_01'
b.mkdir(exist_ok=False)
started = time.monotonic()
fixture = D / 'resource_domain_tiny_regression_02'
initial = fixture / 'initial'
root = D.parents[1]
arch = root / 'results/architecture_flow_20261027/model_fixtures/n25_w100/hybrid_o/import_only.xml'
graph = arch.with_name('rr_graph.xml')
circuit = D / 'reservation_workspace_02/vtr_flow/tasks/regression_tests/vtr_reg_strong/strong_pending_multisink/fixture.blif'
guard = root / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard'
binary = D / 'export_policy_stage_01/bin/vpr'
command = [str(binary), str(arch), str(circuit), '--analysis', '--device', 'fixture', '--route_chan_width', '100',
           '--seed', '11', '--num_workers', '1', '--clock_modeling', 'ideal', '--check_route', 'full',
           '--verify_file_digests', 'off', '--verify_route_file_switch_id', 'on', '--read_rr_graph', str(graph),
           '--net_file', str(initial / 'packed.net'), '--place_file', str(initial / 'placed.place'), '--route_file', str(initial / 'routed.route')]
files = [Path(__file__).resolve(), D / 'export_policy_analysis_pool.py', D / 'pool_state_evaluator_v7.py',
         D / 'endpoint_timing_policy_streaming_v2.py', D / 'export_policy_stage_01/binding.json',
         fixture / 'completion.json', fixture / 'partial.txt', fixture / 'whole.txt', fixture / 'domain.txt']
bound = {str(p): sha(p) for p in files}
write(b / 'registration.json', dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
      source_sha256=bound, question='Do full and compact graph-text export produce exact same actual source/candidate/restored routes, full native frontier and complete endpoint precision, while keeping default isolation, infeasible transactions and automatic release correct?',
      native_route_flows=0, limits=dict(child_seconds=60, memory_bytes=2 * 1024**3, combined_VPR_maximum=3),
      qualification='Engineering regression with an existing two-layer fixture, no new pack/place/route. Compact omits only full graph text; native FULL/freshSTA and all frontier/constraint rows remain.'))
pool = NativeAnalysisPool(b / 'pool', command, [arch, graph, circuit, initial / 'packed.net', initial / 'placed.place'],
                          guard, child_seconds=60, memory_bytes=2 * 1024**3)
records = {}

def compare_states(full, compact, parts):
    x, y = Path(full['native_directory']), Path(compact['native_directory'])
    assert full['full_timing_echo_requested'] and not compact['full_timing_echo_requested']
    for part in parts:
        for name in ['native_sta_frontier.jsonl', 'native_sta_frontier.jsonl.constraints.echo']:
            assert sha(x / part / name) == sha(y / part / name)
        assert (x / part / 'timing_graph.full_precision.echo').exists()
        assert not (y / part / 'timing_graph.full_precision.echo').exists()
        if part != '.':
            assert sha(x / part / 'routed.route') == sha(y / part / 'routed.route')
            assert (x / part / 'native_state_gate.txt').read_text() == (y / part / 'native_state_gate.txt').read_text()

def normalized(path):
    result = []
    for line in Path(path).read_text().splitlines():
        row = line.split()
        if row[0] == 'QUERY':
            row = row[:-1]
        if row[0] == 'COMPLETE':
            row = row[:4] + row[5:]
        result.append(row)
    return result

try:
    for echo in [True, False]:
        records['source_' + str(echo)] = pool.analyze(initial / 'routed.route', echo=echo, reuse=False)
        assert records['source_' + str(echo)]['passed']
    compare_states(records['source_True'], records['source_False'], ['.'])
    fake_evaluator = PoolStateEvaluator.__new__(PoolStateEvaluator)
    fake_evaluator.pool = pool
    for name, request, domain, feedback in [
        ('partial', fixture / 'partial.txt', fixture / 'domain.txt', False),
        ('infeasible', fixture / 'whole.txt', fixture / 'domain.txt', False),
        ('feedback', fixture / 'whole.txt', fixture / 'domain.txt', True),
    ]:
        pair = {}
        for echo in [True, False]:
            worker = pool.analyze(initial / 'routed.route', echo=echo, native_request=request,
                                  crossing_domain=domain, domain_failure_release=feedback, candidate_full_sta=True, reuse=False)
            assert worker['passed']
            assert worker['native_transaction_succeeded'] == (name != 'infeasible')
            pair[echo] = worker
            records[name + '_' + str(echo)] = worker
        assert pair[True]['fingerprint'] != pair[False]['fingerprint']
        parts = ['.', 'candidate_restored'] + (['candidate'] if name != 'infeasible' else [])
        compare_states(pair[True], pair[False], parts)
        assert normalized(Path(pair[True]['native_directory']) / 'joint_native.log') == normalized(Path(pair[False]['native_directory']) / 'joint_native.log')
        if name != 'infeasible':
            view = fake_evaluator.candidate_observation(pair[False])
            assert view['observed_state_kind'] == 'installed_candidate' and not view['full_timing_echo_requested']
            changed = copy.deepcopy(pair[False])
            changed['full_timing_echo_requested'] = True
            try:
                fake_evaluator.candidate_observation(changed)
            except AssertionError:
                pass
            else:
                raise AssertionError('Forged full/compact view accepted')
    candidate = Path(records['feedback_False']['native_directory']) / 'candidate/routed.route'
    independent = pool.analyze(candidate, echo=False, reuse=False)
    assert independent['passed']
    for name in ['native_sta_frontier.jsonl', 'native_sta_frontier.jsonl.constraints.echo']:
        assert sha(candidate.parent / name) == sha(Path(independent['native_directory']) / name)
    following = pool.analyze(initial / 'routed.route', echo=False, reuse=False)
    assert following['passed']
    for name in ['native_sta_frontier.jsonl', 'native_sta_frontier.jsonl.constraints.echo']:
        assert sha(Path(following['native_directory']) / name) == sha(Path(records['source_True']['native_directory']) / name)
    assert len({r['epoch_pid'] for r in records.values()}) == 1
    write(b / 'progress.json', records)
finally:
    pool.close()
assert all(sha(p) == h for p, h in bound.items())
write(b / 'completion.json', dict(passed=True, full_compact_source_candidate_restored_frontiers_exact=True,
      full_compact_routes_and_native_searches_exact=True, complete_native_FULLSTA_gates=True,
      infeasible_transaction_and_failure_release_correct=True, explicit_candidate_view_flag_cannot_be_forged=True,
      separate_compact_candidate_LOAD_exact=True, following_source_exact=True, native_children=len(pool.jobs),
      complete_regression_seconds=time.monotonic() - started,
      source_sha256={str(p): sha(p) for p in [Path(__file__).resolve(), b / 'registration.json', b / 'progress.json', b / 'pool/completion.json']},
      qualification='Actual tiny same-binary output-level validation. Large CPD-changing/resource cases and materialization/cost controls remain separate; no full algorithm speedup claim.'))
print(dict(passed=True, children=len(pool.jobs)), flush=True)
