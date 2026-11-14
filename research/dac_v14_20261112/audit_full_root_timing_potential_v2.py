#!/usr/bin/env python3
"""Audit completed reverse-query answers with virtual-anchor handling; zero repeated queries."""
import shutil
import time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D, read, write, sha
from run_native_frontier_queries import groups
from immutable_rr_audit_cache import GraphAuditCache

started = time.monotonic()
prior = D / 'full_root_timing_potential_01'
b = D / 'full_root_timing_potential_02'
b.mkdir(exist_ok=False)
reg = read(prior / 'registration.json')
assert all(sha(p) == h for p, h in reg['source_sha256'].items())
assert read(prior / 'process.json')['returncode'] == 0
for n in ['registration.json', 'cases.json', 'cases.txt', 'new_cases.txt', 'new_stdout.log', 'query_stdout.log', 'query_stderr.log', 'reuse_receipts.json', 'process.json']:
    shutil.copy2(prior / n, b / n)
queries = read(b / 'cases.json')
answers = groups(b / 'query_stdout.log')
base = D / 'strong_A0_timing_trajectories_01/strict/round_003/feedback'
source = Path(read(base / 'capacity/execution_registration.json')['input_run'])
manifest = read(source / 'manifest.json')
rrg = Path(manifest['command'][manifest['command'].index('--read_rr_graph') + 1])
binding = read(D / 'bnn_physical_query_graph_01/graph_binding.json')
assert manifest['shared_inputs'][str(rrg)]['sha256'] == binding['source_rrg_sha256']
cache = GraphAuditCache(rrg, D / 'rr_audit_cache_bnn_01')
oldrows = {(r['net'], r['pin']): r for r in read(base / 'relaxed/analysis.json')['results']}
rows = []
for case in queries:
    block = answers[(case['net'], case['pin'], 0)]
    result = block[0].split()
    assert int(result[4]) == 0
    value, lower = map(float, result[8:10])
    assert value == lower
    reverse_path = [line.split() for line in block[1:]]
    assert len(reverse_path) == int(result[11])
    # Driver searches sink->root in the reversed RRG, then root->virtual terminal.
    assert tuple(map(int, reverse_path[-1][5:7])) == (case['root'], cache.n)
    assert float(reverse_path[-1][7]) == 0.
    total = 0.
    cursor = case['root']
    witness = []
    for edge in reversed(reverse_path[:-1]):
        u, v, w = int(edge[6]), int(edge[5]), float(edge[7])
        assert u == cursor
        cursor = v
        total += w
        switches = []
        for sw, delay in cache.switches.items():
            if delay != w:
                continue
            key = (u * cache.n + v) * cache.stride + sw
            pos = np.searchsorted(cache.edges, np.uint64(key))
            if pos < len(cache.edges) and int(cache.edges[pos]) == key:
                switches.append(sw)
        assert switches, 'Reverse witness does not correspond to an actual forward RRG edge at this switch delay'
        witness.append([u, v, switches[0], w])
    assert cursor == case['sink'] and abs(total - value) <= max(1.e-24, abs(value) * 1.e-14)
    previous = oldrows[(case['net'], case['pin'])]
    rows.append(dict(net=case['net'], pin=case['pin'], current_switch_distance_s=case['current_physical_seconds'],
        retained_prefix_relaxed_distance_s=previous['physical_seconds'], root_only_relaxed_distance_s=value,
        source_only_potential_ns=(case['current_physical_seconds'] - value) * 1e9,
        source_only_more_optimistic_ns=(previous['physical_seconds'] - value) * 1e9,
        exact_solver_stop=0, actual_directed_witness=witness))
files = [Path(__file__).resolve(), prior / 'registration.json', prior / 'process.json', prior / 'query_stdout.log',
         prior / 'cases.json', base / 'relaxed/analysis.json', D / 'bnn_physical_query_graph_01/graph_binding.json',
         D / 'rr_audit_cache_bnn_01/completion.json']
write(b / 'completion.json', dict(passed=True, rows=rows, new_queries_from_preserved_parent=len(read(prior / 'new_cases.json')) if (prior / 'new_cases.json').exists() else len(queries) - len(read(prior / 'reuse_receipts.json')),
      exact_reuse_queries_from_old_relaxed=len(read(prior / 'reuse_receipts.json')), repeated_query_calls=0, native_route_calls=0,
      prior_audit_issue='Version01 treated reverse/virtual edges as physical forward edges. Its solver succeeded; this version reuses every answer and checks the actual reversed forward RRG edges, excluding the virtual anchor.',
      all_source_root_distances_equal_current=all(r['source_only_potential_ns'] == 0 for r in rows),
      audit_seconds=time.monotonic() - started, original_solver_process_seconds=read(prior / 'process.json')['query_seconds'],
      source_sha256={str(p): sha(p) for p in files},
      artifact_sha256={n: sha(b / n) for n in ['cases.json', 'cases.txt', 'reuse_receipts.json', 'query_stdout.log', 'registration.json']},
      qualification='Exact optimistic static-switch source-root reference with independently checked forward physical edges; no retained prefixes or background occupancy. Mandatory nonconfigurable closure, whole-net sharing and native STA arithmetic remain relaxed. This is not a native FPGA/STA global optimality proof or a stop rule. Acceptance still uses full-precision native FULL/STA with no tolerance.'))
print(dict(passed=True, potentials=[(r['net'], r['source_only_potential_ns']) for r in rows], repeated_queries=0), flush=True)
