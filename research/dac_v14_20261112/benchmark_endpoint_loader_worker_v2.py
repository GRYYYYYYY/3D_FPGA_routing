"""Isolated, non-native benchmark of one exact endpoint-vector read."""
import argparse
import hashlib
import json
import resource
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--mode', choices=['reference', 'stream'], required=True)
p.add_argument('--trace', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()
resource.setrlimit(resource.RLIMIT_AS, (16 * 1024**3, 16 * 1024**3))
def proc_memory():
    fields = {}
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith(('VmRSS:', 'VmHWM:')):
            key, value = line.split(':', 1)
            fields[key] = int(value.split()[0])
    return fields

before = proc_memory()
started = time.monotonic()
if a.mode == 'reference':
    from endpoint_timing_policy import load
else:
    from endpoint_timing_policy_streaming_v2 import load
vector = load(a.trace)
load_seconds = time.monotonic() - started
usage = resource.getrusage(resource.RUSAGE_SELF)
after = proc_memory()
payload = json.dumps(vector, sort_keys=True, separators=(',', ':'))
result = dict(mode=a.mode, trace=str(a.trace.resolve()),
              exact_canonical_vector_sha256=hashlib.sha256(payload.encode()).hexdigest(),
              endpoints=len(vector['endpoint_ids']), setup_components=len(vector['setup']),
              hold_components=len(vector['hold']), CPD_s=vector['cpd_s'],
              trace_sha256=vector['trace_sha256'],
              constraints_sha256=vector['constraints_sha256'],
              loader_seconds=load_seconds,
              process_RSS_high_water_kib=usage.ru_maxrss,
              process_user_CPU_seconds=usage.ru_utime,
              process_system_CPU_seconds=usage.ru_stime,
              native_calls=0, proc_memory_before=before, proc_memory_after=after,
              loader_module=load.__module__)
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result), flush=True)
