#!/usr/bin/env python3
"""Distinguish exhausted retained-prefix timing proposals from whole-net timing potential."""
import copy
import os
import resource
import signal
import subprocess
import time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D, read, write, sha
from run_native_frontier_queries import fingerprint, groups, write_cases
from immutable_rr_audit_cache import GraphAuditCache

b = D / 'full_root_timing_potential_01'
b.mkdir(exist_ok=False)
started = time.monotonic()
resource.setrlimit(resource.RLIMIT_AS, (24 * 1024**3, 24 * 1024**3))
signal.alarm(1800)
base = D / 'strong_A0_timing_trajectories_01/strict/round_003/feedback'
old = base / 'relaxed'
driver = D / 'current_sta_relaxed_01/critical_capacity_driver'
binary = D / 'bnn_physical_query_graph_01/graph.bin'
binding = read(binary.with_name('graph_binding.json'))
assert binding['passed'] and 'all node/switch RC zero checked' in binding['format']
assert sha(binary) == binding['binary_graph_sha256']
ex = read(old / 'execution.json')
assert ex['source_sha256'][str(driver)] == sha(driver) and ex['source_sha256'][str(binary)] == sha(binary)
assert read(old / 'analysis.json')['passed']
assert all(sha(old / p) == h for p, h in ex['output_sha256'].items())
files = [Path(__file__).resolve(), old / 'execution.json', old / 'analysis.json', old / 'query_stdout.log', old / 'cases.json',
         base / 'proposal/plan.json', driver, binary, binary.with_name('graph_binding.json'),
         D / 'immutable_rr_audit_cache.py', D / 'rr_audit_cache_bnn_01/completion.json']
bound = {str(p): sha(p) for p in files}
original = read(old / 'cases.json')
answers = groups(old / 'query_stdout.log')
queries = []
hits = []
new = []
for case in original:
    relaxed = copy.deepcopy(case)
    relaxed.update(retained=[case['root']], anchors={str(case['root']): 0.}, blocked=[],
                   domain='Full-device directed graph, source root only at zero delay; no retained branches or occupancy. Optimistic static-switch relaxation, not a feasible whole-net route.')
    queries.append(relaxed)
    if fingerprint(relaxed, 0) == fingerprint(case, 0):
        hits.append(dict(net=case['net'], pin=case['pin'], fingerprint=fingerprint(case, 0), source=str(old / 'query_stdout.log')))
    else:
        new.append(relaxed)
write(b / 'cases.json', queries)
write_cases(b / 'cases.txt', queries)
write(b / 'reuse_receipts.json', hits)
write(b / 'registration.json', dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
      source_sha256=bound, question='The current strong-A0 fast winning-cone portfolio has no positive retained-prefix move even ignoring occupancy. Does releasing all shared prefixes for source-root optimistic distance reveal whole-net opportunities, or is this intervention location close to its switch-distance reference?',
      modification='Only change retained-set/anchor semantics to source-only with no other occupancy. Reuse all exactly matching source-only old queries; never repeat them just for reporting.',
      limits=dict(query_seconds=900, memory_bytes=24 * 1024**3, disk_reserve_bytes=80 * 1024**3),
      native_route_calls=0,
      qualification='Optimistic independent paths in the verified zero-RC switch-delay model; mandatory branch preservation, nonconfigurable closure, full-net sharing, occupancy and native STA arithmetic are relaxed. Not legal repair performance, a global FPGA optimum, or a strict native-STA CPD bound.'))
if new:
    write_cases(b / 'new_cases.txt', new)
    t = time.monotonic()
    with (b / 'new_stdout.log').open('w') as out, (b / 'query_stderr.log').open('w') as err:
        r = subprocess.run(['prlimit', '--as=' + str(24 * 1024**3), '--', str(driver), str(binary), str(b / 'new_cases.txt')],
                           stdout=out, stderr=err, timeout=900)
    write(b / 'process.json', dict(returncode=r.returncode, query_seconds=time.monotonic() - t))
    assert r.returncode == 0
    answers.update(groups(b / 'new_stdout.log'))
with (b / 'query_stdout.log').open('w') as out:
    for case in queries:
        out.writelines(answers[(case['net'], case['pin'], 0)])
graph = Path(read(base / 'capacity/execution_registration.json')['input_run'])
manifest = read(graph / 'manifest.json')
rrg = Path(manifest['command'][manifest['command'].index('--read_rr_graph') + 1])
assert manifest['shared_inputs'][str(rrg)]['sha256'] == binding['source_rrg_sha256']
cache = GraphAuditCache(rrg, D / 'rr_audit_cache_bnn_01')
rows = []
for case in queries:
    block = answers[(case['net'], case['pin'], 0)]
    result = block[0].split()
    assert result[0] == 'RESULT' and int(result[4]) == 0, 'No exact relaxed solution; retain unknown rather than a false potential conclusion'
    value = float(result[8])
    lower = float(result[9])
    assert value == lower
    path = [line.split() for line in block[1:]]
    assert len(path) == int(result[11])
    total = 0.
    cursor = case['root']
    for edge in path:
        u, v, w = int(edge[5]), int(edge[6]), float(edge[7])
        assert u == cursor
        cursor = v
        total += w
        possible = [sw for sw, delay in cache.switches.items() if delay == w]
        available = False
        for sw in possible:
            key = (u * cache.n + v) * cache.stride + sw
            pos = np.searchsorted(cache.edges, np.uint64(key))
            if pos < len(cache.edges) and int(cache.edges[pos]) == key:
                available = True
                break
        assert available, 'Witness switch delay does not correspond to a real directed RRG edge'
    assert cursor == case['sink'] and abs(total - value) <= max(1.e-24, abs(value) * 1.e-14)
    prior_row = next(r for r in read(old / 'analysis.json')['results'] if (r['net'], r['pin']) == (case['net'], case['pin']))
    rows.append(dict(net=case['net'], pin=case['pin'], current_switch_distance_s=case['current_physical_seconds'],
        retained_prefix_relaxed_distance_s=prior_row['physical_seconds'], root_only_relaxed_distance_s=value,
        source_only_potential_ns=(case['current_physical_seconds'] - value) * 1e9,
        source_only_more_optimistic_ns=(prior_row['physical_seconds'] - value) * 1e9,
        exact_solver_stop=0, directed_witness_edges=len(path)))
write(b / 'completion.json', dict(passed=True, rows=rows, new_queries=len(new), exact_reuse_queries=len(hits),
      native_route_calls=0, complete_diagnostic_seconds=time.monotonic() - started,
      source_sha256=bound, artifact_sha256={n: sha(b / n) for n in ['cases.json', 'cases.txt', 'reuse_receipts.json', 'query_stdout.log', 'registration.json']},
      qualification='Only the static-switch relaxed problem is solved exactly. Native arithmetic may differ at last bits; diagnostic comparisons never create an acceptance tolerance. Independently validated directed edges are optimistic paths, not legal full-net branches or final CPD improvements. No fixed date/count/matrix or proxy-potential result ends the overall research.'))
print(dict(new=len(new), reused=len(hits), potentials=[(r['net'], r['source_only_potential_ns']) for r in rows]), flush=True)
