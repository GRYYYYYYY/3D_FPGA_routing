#!/usr/bin/env python3
"""Actual tiny native tests of opt-in release, default compatibility and isolation."""
import os
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from native_feedback_analysis_pool import NativeAnalysisPool

b = D / 'domain_failure_release_tiny_01'
b.mkdir(exist_ok=False)
started = time.monotonic()
prior = D / 'resource_domain_tiny_regression_02'
initial = prior / 'initial'
old = D / 'native_repair_queue_tiny_regression_01'
assert read(prior / 'completion.json')['passed'] and read(old / 'completion.json')['passed']
root = D.parents[1]
arch = root / 'results/architecture_flow_20261027/model_fixtures/n25_w100/hybrid_o/import_only.xml'
graph = arch.with_name('rr_graph.xml')
circuit = D / 'reservation_workspace_02/vtr_flow/tasks/regression_tests/vtr_reg_strong/strong_pending_multisink/fixture.blif'
guard = root / 'results/architecture_flow_20261027/serial_strict_reexecution_20261103/execution_scripts/seccomp_thread_guard'
binary = D / 'domain_failure_release_stage_01/bin/vpr'
command = [str(binary), str(arch), str(circuit), '--analysis', '--device', 'fixture',
           '--route_chan_width', '100', '--seed', '11', '--num_workers', '1',
           '--clock_modeling', 'ideal', '--check_route', 'full', '--verify_file_digests', 'off',
           '--verify_route_file_switch_id', 'on', '--read_rr_graph', str(graph),
           '--net_file', str(initial / 'packed.net'), '--place_file', str(initial / 'placed.place'),
           '--route_file', str(initial / 'routed.route')]
files = [Path(__file__).resolve(), binary, D / 'native_feedback_analysis_pool.py',
         D / 'domain_failure_release_stage_01/binding.json', old / 'completion.json',
         prior / 'completion.json', prior / 'partial.txt', prior / 'whole.txt', prior / 'domain.txt']
bound = {str(p): sha(p) for p in files}
write(b / 'registration.json', dict(pid=os.getpid(),
      start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
      question='Does opt-in whole-prune domain failure release reproduce unrestricted native trees, preserve default OFF/ON and failed-domain results, and leave the same parent/input FULLSTA unchanged?',
      source_sha256=bound, native_route_flows=0,
      limits=dict(child_seconds=60, memory_bytes=2 * 1024**3),
      qualification='Tiny integration tests in an independent new binary. Existing completed golden evidence reused; no new large QoR or speedup claim.'))

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

def nodes(path):
    return [l for l in Path(path).read_text().splitlines() if l.startswith(('KEEP ', 'NODE '))]

pool = NativeAnalysisPool(b / 'pool', command, [arch, graph, circuit, initial / 'packed.net', initial / 'placed.place'],
                          guard, child_seconds=60, memory_bytes=2 * 1024**3)
records = {}
try:
    for name, request, domain, feedback in [
        ('analysis', None, None, False),
        ('off', prior / 'partial.txt', None, False),
        ('on', prior / 'partial.txt', prior / 'domain.txt', False),
        ('infeasible', prior / 'whole.txt', prior / 'domain.txt', False),
        ('whole_free', prior / 'whole.txt', None, False),
        ('whole_feedback', prior / 'whole.txt', prior / 'domain.txt', True),
        ('following_on', prior / 'partial.txt', prior / 'domain.txt', False),
        ('following_source', None, None, False),
    ]:
        r = pool.analyze(initial / 'routed.route', native_request=request, crossing_domain=domain,
                         domain_failure_release=feedback, reuse=False)
        assert r['passed'], (name, r)
        native = Path(r['native_directory'])
        for output in ['native_sta_frontier.jsonl', 'native_sta_frontier.jsonl.constraints.echo', 'timing_graph.full_precision.echo']:
            assert sha(native / output) == sha(old / 'standalone_analysis' / output)
        if name in ['off', 'on', 'infeasible']:
            assert normalized(native / 'joint_native.log') == normalized(old / ('standalone_' + name) / 'joint_native.log')
        if name == 'infeasible':
            assert r['native_transaction_succeeded'] is False
        elif request is not None:
            assert r['native_transaction_succeeded'] is True
        records[name] = r
        write(b / 'progress.json', records)
    free = Path(records['whole_free']['native_directory'])
    feedback = Path(records['whole_feedback']['native_directory'])
    assert nodes(free / 'joint_native.log') == nodes(feedback / 'joint_native.log')
    releases = [l.split() for l in (feedback / 'joint_native.log').read_text().splitlines() if l.startswith('DOMAIN_RELEASE ')]
    assert releases and len(releases) == len({r[1] for r in releases})
    assert records['whole_feedback']['fingerprint'] != records['infeasible']['fingerprint']
    following = Path(records['following_on']['native_directory'])
    assert normalized(following / 'joint_native.log') == normalized(old / 'standalone_on/joint_native.log')
    assert 'RELEASE ' not in (following / 'vertical_domain.log').read_text()
    assert len({r['epoch_pid'] for r in records.values()}) == 1
finally:
    pool.close()
assert all(sha(p) == h for p, h in bound.items())
write(b / 'completion.json', dict(passed=True, source_FULL_STA_unchanged=True,
      default_off_on_failure_logs_exact=True, guided_failure_recovered_with_exact_free_native_trees=True,
      same_parent_following_default_mode_unchanged=True, feedback_identity_separated=True,
      native_children=len(pool.jobs), releases=releases, complete_regression_seconds=time.monotonic() - started,
      source_sha256={str(p): sha(p) for p in [Path(__file__).resolve(), b / 'registration.json', b / 'progress.json', b / 'pool/completion.json']},
      qualification='Native tiny local trees and source STA verified. Candidate serialization/physical/FULLSTA validation on the representative large matched case still required. No complete-algorithm timing claim.'))
print(dict(passed=True, jobs=len(pool.jobs), releases=releases), flush=True)
