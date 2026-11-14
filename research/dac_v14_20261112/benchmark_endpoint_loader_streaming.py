#!/usr/bin/env python3
"""Matched all-row JSON validation and exact endpoint identity; measure component memory/time."""
import argparse
import hashlib
import importlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

p = argparse.ArgumentParser()
p.add_argument('--worker-loader')
p.add_argument('--trace', type=Path)
p.add_argument('--result', type=Path)
a = p.parse_args()
if a.worker_loader:
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    module = importlib.import_module(a.worker_loader)
    started = time.monotonic()
    vector = module.load(a.trace)
    elapsed = time.monotonic() - started
    digest = hashlib.sha256(json.dumps(vector, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    write(a.result, dict(loader=a.worker_loader, trace=str(a.trace), load_seconds=elapsed,
          peak_process_RSS_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          complete_vector_digest=digest, endpoint_count=len(vector['endpoint_ids']), setup_components=len(vector['setup']), CPD_s=vector['cpd_s']))
    raise SystemExit(0)

b = D / 'endpoint_loader_streaming_validation_01'
b.mkdir(exist_ok=False)
w = read(D / 'candidate_full_sta_bnn_01/transaction/fused_worker_receipt.json')
n = Path(w['native_directory'])
traces = [n / 'native_sta_frontier.jsonl', n / 'candidate/native_sta_frontier.jsonl']
files = [Path(__file__).resolve(), D / 'endpoint_timing_policy.py', D / 'endpoint_timing_policy_streaming_v2.py',
         D / 'candidate_full_sta_native_binding_01.json', *traces]
bound = {str(f): sha(f) for f in files}
write(b / 'registration.json', dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
      question='Can streaming every JSON row retain the exact complete endpoint/clock-domain vector and strict acceptance semantics while reducing memory and load cost for357MiB native traces?',
      source_sha256=bound, native_calls=0, route_calls=0,
      order='Source old->streaming; actual candidate streaming->old. Independent process per load. Read/validate every JSON row; no pin-row skipping, missing-vector inference or precision tolerance.',
      qualification='Component engineering measurement under current shared server load, not formal complete-algorithm time. Existing active timing experiment and materializer versions unchanged.'))
rows = []
for index, trace in enumerate(traces):
    modules = ['endpoint_timing_policy', 'endpoint_timing_policy_streaming_v2']
    if index:
        modules.reverse()
    for module in modules:
        out = b / (str(index) + '_' + module + '.json')
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker-loader', module,
                                 '--trace', str(trace), '--result', str(out)], capture_output=True, text=True, timeout=1800)
        assert result.returncode == 0, result.stderr
        rows.append(read(out))
        write(b / 'progress.json', rows)
for trace in traces:
    pair = [r for r in rows if r['trace'] == str(trace)]
    assert len(pair) == 2 and pair[0]['complete_vector_digest'] == pair[1]['complete_vector_digest']
assert all(sha(f) == h for f, h in bound.items())
write(b / 'completion.json', dict(passed=True, rows=rows, all_complete_vectors_exact=True,
      new_guard='Counts all parsed pin rows against the native COMPLETE marker; rejects trailing rows or missing completion. Every JSON row still parsed and validated.',
      native_calls=0, route_calls=0, source_sha256=bound,
      qualification='Read-only exact comparisons on fully sealed actual source/candidate native exports. Timing and peak RSS refer only to independent loader processes. Algorithm integration, broad negative-schema validation and matched complete routing+repair timing remain separate work.'))
print(rows, flush=True)
