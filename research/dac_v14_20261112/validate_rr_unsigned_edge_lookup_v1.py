"""Validate actual graph row bounds and expose scalar-key conversion overhead."""
import bisect, resource, time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D, read, write, sha
from rr_unsigned_edge_lookup_v1 import edge_row_bounds

output = D/'rr_unsigned_edge_lookup_validation_01'
output.mkdir(exist_ok=False)
cache = D/'rr_audit_cache_bnn_01'
receipt = read(cache/'completion.json')
edges = np.load(cache/'edges.npy', mmap_mode='r')
assert edges.dtype == np.dtype('uint64')
# These positions are checked by Python's integer-only binary search, independent
# of NumPy's dtype promotion and the helper's two-key search call.
n, stride = receipt['node_count'], receipt['switch_stride']
sources = sorted({0, n-1, 265257, 265308, 3507189, *range(0, n, max(1, n//16))})
checks = []
for source in sources:
    expected = [bisect.bisect_left(edges, int(source)*n*stride), bisect.bisect_left(edges, (int(source)+1)*n*stride)]
    actual = edge_row_bounds(edges, n, stride, source).tolist()
    assert actual == expected
    checks.append(dict(source=source, positions=actual))
# Exactness must also hold beyond floating-point's contiguous integer range.
synthetic_n, synthetic_stride, synthetic_source = 4, 2**51+1, 2
width = synthetic_n*synthetic_stride
lo, hi = synthetic_source*width, (synthetic_source+1)*width
synthetic = np.array([lo-1, lo, lo+1, hi-1, hi, hi+1], dtype=np.uint64)
assert edge_row_bounds(synthetic, synthetic_n, synthetic_stride, synthetic_source).tolist() == [1, 4]
values = [3507189*n*stride, 3507190*n*stride]
measurements = {}
for name, query in [('python_int_list', values), ('matching_unsigned_keys', np.array(values, dtype=edges.dtype))]:
    before = resource.getrusage(resource.RUSAGE_SELF)
    started = time.monotonic()
    positions = edges.searchsorted(query).tolist()
    elapsed = time.monotonic()-started
    after = resource.getrusage(resource.RUSAGE_SELF)
    measurements[name] = dict(seconds=elapsed, minor_faults=after.ru_minflt-before.ru_minflt,
                              major_faults=after.ru_majflt-before.ru_majflt, positions=positions)
assert measurements['python_int_list']['positions'] == measurements['matching_unsigned_keys']['positions']
write(output/'actual_row_checks.json', checks)
files = [Path(__file__).resolve(), D/'rr_unsigned_edge_lookup_v1.py', cache/'completion.json']
write(output/'completion.json', dict(passed=True, actual_graph_rows=len(checks), above_2_to_53_synthetic_exact=True,
    native_calls_new=0, edge_array_dtype=str(edges.dtype), inferred_python_list_dtype=str(np.asarray(values).dtype),
    edge_array_bytes=edges.nbytes, micro_observations=measurements,
    source_sha256={str(p): sha(p) for p in files}, artifact_sha256={'actual_row_checks.json': sha(output/'actual_row_checks.json')},
    qualification='Integer-only independent binary search agrees on actual complete-graph RR rows, including boundaries; synthetic keys beyond2^53 remain exact. One shared-process lookup per representation exposes conversion/page-fault overhead only. This is not a complete algorithm speedup or statistical timing claim; peak RSS not attributed across the shared process. Original native experiments and bound historical scripts unchanged. Full graph identity/digests remain the surrounding cache adapter responsibility.'))
print(dict(passed=True, actual_rows=len(checks), measurements=measurements), flush=True)
