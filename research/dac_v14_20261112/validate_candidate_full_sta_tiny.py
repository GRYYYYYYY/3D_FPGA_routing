#!/usr/bin/env python3
"""Real native candidate/source trees and STA, independent LOAD, default and failure gates."""
import collections
import os
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from candidate_full_sta_analysis_pool import NativeAnalysisPool
from coordinated_repair_tree import from_trace, prune_sinks
sys.path.insert(0, str(D.parents[1] / 'scripts'))
from check_route import read_trace

b = D / 'candidate_full_sta_tiny_01'
b.mkdir(exist_ok=False)
started = time.monotonic()
prior = D / 'resource_domain_tiny_regression_02'
old = D / 'native_repair_queue_tiny_regression_01'
initial = prior / 'initial'
root = D.parents[1]
arch = root / 'results/architecture_flow_20261027/model_fixtures/n25_w100/hybrid_o/import_only.xml'
graph = arch.with_name('rr_graph.xml')
circuit = D / 'reservation_workspace_02/vtr_flow/tasks/regression_tests/vtr_reg_strong/strong_pending_multisink/fixture.blif'
guard = root / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard'
binary = D / 'candidate_full_sta_stage_01/bin/vpr'
command = [str(binary), str(arch), str(circuit), '--analysis', '--device', 'fixture', '--route_chan_width', '100',
           '--seed', '11', '--num_workers', '1', '--clock_modeling', 'ideal', '--check_route', 'full',
           '--verify_file_digests', 'off', '--verify_route_file_switch_id', 'on', '--read_rr_graph', str(graph),
           '--net_file', str(initial / 'packed.net'), '--place_file', str(initial / 'placed.place'), '--route_file', str(initial / 'routed.route')]
files = [Path(__file__).resolve(), D / 'candidate_full_sta_analysis_pool.py', D / 'candidate_full_sta_stage_01/binding.json',
         old / 'completion.json', prior / 'completion.json', initial / 'routed.route', prior / 'partial.txt', prior / 'whole.txt', prior / 'domain.txt']
bound = {str(p): sha(p) for p in files}
write(b / 'registration.json', dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
      source_sha256=bound,
      question='Does fused native candidate FULL/freshSTA actually observe the correct installed candidate and restore the exact source trees/occupancy/sink mappings/digest/output hooks, including failed transactions and later requests?',
      qualification='Independent implementation regression; same-binary separate route LOAD for every successful tiny fused candidate. No new pack/place/initial route, no QoR or cold timing claim.',
      limits=dict(child_seconds=60, memory_bytes=2 * 1024**3,temporary_small_fixture_total_native_process_limit=4)))
outputs = ['native_sta_frontier.jsonl', 'native_sta_frontier.jsonl.constraints.echo', 'timing_graph.full_precision.echo']

def normalized(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        v = line.split()
        if v[0] == 'QUERY':
            v = v[:-1]
        if v[0] == 'COMPLETE':
            v = v[:4] + v[5:]
        rows.append(v)
    return rows

def exact_exports(a, c):
    assert all(sha(a / n) == sha(c / n) for n in outputs)

def structure(path):
    return {net: from_trace(row['trace'], collections.defaultdict(float)) for net, row in read_trace(path).items()}

original = structure(initial / 'routed.route')
pool = NativeAnalysisPool(b / 'pool', command, [arch, graph, circuit, initial / 'packed.net', initial / 'placed.place'],
                          guard, child_seconds=60, memory_bytes=2 * 1024**3)
records = {}
try:
    source = pool.analyze(initial / 'routed.route', reuse=False)
    assert source['passed']
    exact_exports(Path(source['native_directory']), old / 'standalone_analysis')
    for name, request, domain, feedback in [
        ('partial_off', prior / 'partial.txt', None, False),
        ('partial_on', prior / 'partial.txt', prior / 'domain.txt', False),
        ('whole_failure', prior / 'whole.txt', prior / 'domain.txt', False),
        ('whole_feedback', prior / 'whole.txt', prior / 'domain.txt', True),
    ]:
        r = pool.analyze(initial / 'routed.route', native_request=request, crossing_domain=domain,
                         domain_failure_release=feedback, candidate_full_sta=True, reuse=False)
        records[name] = r
        write(b / 'progress.json', records)
        assert r['passed'], r
        native = Path(r['native_directory'])
        exact_exports(native, Path(source['native_directory']))
        restored = native / 'candidate_restored'
        exact_exports(restored, Path(source['native_directory']))
        assert structure(restored / 'routed.route') == original
        if name == 'whole_failure':
            assert r['native_transaction_succeeded'] is False and r['candidate_full_STA_passed'] is None
            assert not (native / 'candidate/native_state_gate.txt').exists()
            continue
        assert r['native_transaction_succeeded'] and r['candidate_full_STA_passed']
        candidate = native / 'candidate'
        trees = structure(candidate / 'routed.route')
        assert trees.keys() == original.keys()
        assert all(trees[n] == original[n] for n in original if n != 4)
        pins = [1] if name.startswith('partial') else [1, 2]
        # Request file, rather than the test label, is authoritative for pruning.
        tokens = request.read_text().split()
        assert int(tokens[0]) == 1 and int(tokens[1]) == 4
        pins = list(map(int, tokens[3:3 + int(tokens[2])]))
        pruned = prune_sinks(original[4], pins)
        assert all(trees[4]['edges'].get(node) == edge for node, edge in pruned['edges'].items())
        assert trees[4]['sinks'] == original[4]['sinks']
        raw = {}
        for line in (native / 'joint_native.log').read_text().splitlines():
            row = line.split()
            if row[0] == 'NODE':
                net, node, parent, switch, pin = map(int, row[1:6])
                assert net == 4
                raw[node] = (parent, switch, pin)
        assert set(raw) == {trees[4]['root']} | set(trees[4]['edges'])
        assert all((parent, switch) == trees[4]['edges'][node][:2] for node, (parent, switch, pin) in raw.items() if parent >= 0)
        independent = pool.analyze(candidate / 'routed.route', reuse=False)
        assert independent['passed']
        exact_exports(candidate, Path(independent['native_directory']))
        records[name + '_independent_LOAD'] = independent
    failed_file = b / 'invalid_domain.txt'
    failed_file.write_text('1\n999999999\n')
    invalid = pool.analyze(initial / 'routed.route', native_request=prior / 'partial.txt', crossing_domain=failed_file,
                           candidate_full_sta=True, reuse=False)
    assert not invalid['passed']
    following = pool.analyze(initial / 'routed.route', native_request=prior / 'partial.txt', crossing_domain=prior / 'domain.txt', reuse=False)
    assert following['passed'] and following['native_transaction_succeeded']
    exact_exports(Path(following['native_directory']), Path(source['native_directory']))
    assert normalized(Path(following['native_directory']) / 'joint_native.log') == normalized(old / 'standalone_on/joint_native.log')
    assert not (Path(following['native_directory']) / 'candidate').exists()
    assert all(r['epoch_pid'] == source['epoch_pid'] for r in records.values())
    write(b / 'progress.json', records)
finally:
    pool.close()
assert all(sha(p) == h for p, h in bound.items())
write(b / 'completion.json', dict(passed=True, actual_candidate_separate_LOAD_FULLSTA_exact=True,
      complete_source_and_restored_exports_exact=True, unchanged_nets_retained_edges_terminals_and_node_sidecar_match=True,
      failed_transaction_has_no_candidate_gate=True, invalid_child_isolated_next_default_exact=True,
      same_native_parent=True, native_children=len(pool.jobs), complete_regression_seconds=time.monotonic() - started,
      source_sha256={str(p): sha(p) for p in [Path(__file__).resolve(), b / 'registration.json', b / 'progress.json', b / 'pool/completion.json']},
      qualification='Actual candidate install/native FULL/new STA/native serialization and original-tree restoration validated on existing tiny two-layer fixture. Large case and algorithm materialization remain separate gates; no complete-algorithm runtime or QoR claim.'))
print(dict(passed=True, native_children=len(pool.jobs)), flush=True)
