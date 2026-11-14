#!/usr/bin/env python3
"""Reject corrupt real export copies and consume an exact sealed candidate with the new loader."""
import copy
import importlib
import json
import os
import shutil
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from endpoint_timing_policy import load as oldload, compare, decide
from endpoint_timing_policy_streaming_v2 import load as newload
from sealed_native_pool_replay import SealedNativePoolReplay
from pool_state_evaluator_v6 import PoolStateEvaluator

b = D / 'endpoint_loader_streaming_integration_01'
b.mkdir(exist_ok=False)
started = time.monotonic()
assert read(D / 'endpoint_loader_streaming_validation_01/completion.json')['passed']
prior = D / 'candidate_full_sta_tiny_01'
tiny = Path(read(prior / 'progress.json')['partial_on']['native_directory']) / 'candidate/native_sta_frontier.jsonl'
rows = [json.loads(line) for line in tiny.open()]
endpoint = next(i for i, r in enumerate(rows) if r['type'] == 'endpoint')
pin = next(i for i, r in enumerate(rows) if r['type'] == 'pin')
metric = next(i for i, r in enumerate(rows) if r['type'] == 'timing_metrics')
files = [Path(__file__).resolve(), D / 'endpoint_timing_policy_streaming_v2.py', D / 'pool_state_evaluator_v6.py',
         D / 'endpoint_loader_streaming_validation_01/completion.json', D / 'candidate_full_sta_native_binding_01.json',
         D / 'candidate_full_sta_bnn_03/completion.json', tiny, Path(str(tiny) + '.constraints.echo')]
bound = {str(p): sha(p) for p in files}
write(b / 'registration.json', dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
      source_sha256=bound, native_calls=0, route_calls=0,
      question='Does all-row streaming preserve exact acceptance vectors, reject corrupted exports and materialize the actual already-sealed fused candidate without another native job?',
      qualification='Independent decoder/materializer version; running resource-first timing uses its unchanged registered version. Corruption touches only test-owned copies. Exact physical audit is reused only for the same candidate bytes/graph/packing/placement.'))

def fixture(name, records):
    path = b / (name + '.jsonl')
    path.write_text(''.join(json.dumps(r, separators=(',', ':')) + '\n' for r in records))
    shutil.copy2(str(tiny) + '.constraints.echo', str(path) + '.constraints.echo')
    return path

healthy = fixture('healthy_real_tiny', rows)
assert oldload(healthy) == newload(healthy)
cases = {}
cases['missing_complete'] = copy.deepcopy(rows[:-1])
cases['missing_endpoint'] = copy.deepcopy(rows[:endpoint] + rows[endpoint + 1:])
cases['duplicate_endpoint'] = copy.deepcopy(rows[:-1] + [rows[endpoint]] + [dict(rows[-1], endpoint_rows=rows[-1]['endpoint_rows'] + 1)])
cases['nonfinite_CPD'] = copy.deepcopy(rows)
cases['nonfinite_CPD'][metric]['least_slack_CPD_s'] = 'nan'
cases['trailing_row'] = copy.deepcopy(rows + [rows[0]])
rejected = []
for name, records in cases.items():
    path = fixture(name, records)
    for parser in [oldload, newload]:
        try:
            parser(path)
        except (AssertionError, IndexError, ValueError, TypeError):
            pass
        else:
            raise AssertionError((name, parser.__module__))
    rejected.append(name)
malformed = fixture('malformed_pin', rows)
lines = malformed.read_text().splitlines(True)
lines[pin] = '{"type":"pin","broken":}\n'
malformed.write_text(''.join(lines))
for parser in [oldload, newload]:
    try:
        parser(malformed)
    except ValueError:
        pass
    else:
        raise AssertionError('Pin row JSON was silently skipped')
rejected.append('malformed_pin')
missing_pin = fixture('missing_pin', rows[:pin] + rows[pin + 1:])
assert oldload(missing_pin)
try:
    newload(missing_pin)
except AssertionError:
    rejected.append('missing_pin_count_guard_new')
else:
    raise AssertionError('Incomplete native pin census accepted')

reference = Path(read(D / 'candidate_full_sta_bnn_03/completion.json')['candidate_state'])
initial = Path(read(D / 'candidate_full_sta_bnn_03/registration.json')['initial_state'])
worker = read(D / 'candidate_full_sta_bnn_01/transaction/fused_worker_receipt.json')
pool = SealedNativePoolReplay(D / 'candidate_full_sta_bnn_01/pool')
evaluator = PoolStateEvaluator(pool, initial, D / 'full_route_graph_cache_bnn_01', b / 'evaluation_context')
try:
    view = evaluator.candidate_observation(worker)
    actual = Path(view['installed_candidate_identity']['actual_route'])
    result = evaluator.evaluate(actual, b / 'candidate', physical_reference=reference, native_observation=view)
    assert result['passed'] and result['native_analysis_calls'] == 0 and result['physical_audit_reused']
    old = read(reference / 'endpoint_vector.json')
    new = read(b / 'candidate/endpoint_vector.json')
    assert old == new
    before = read(initial / 'endpoint_vector.json')
    assert compare(before, old) == compare(before, new)
    assert all(decide(mode, before, old, True) == decide(mode, before, new, True) for mode in ['strict', 'endpoint_vector'])
finally:
    evaluator.close()
assert all(sha(p) == h for p, h in bound.items())
write(b / 'completion.json', dict(passed=True, corrupted_real_export_cases_rejected=rejected,
      full_real_candidate_vector_exact=True, strict_and_endpoint_acceptance_exact=True,
      actual_candidate_materialization_passed=True, exact_physical_audit_reference_used=True,
      new_native_calls=0, new_route_calls=0, complete_integration_component_seconds=time.monotonic() - started,
      source_sha256={str(p): sha(p) for p in [b / 'registration.json', b / 'candidate/completion.json',
          b / 'evaluation_context/input_seal.json', b / 'evaluation_context/completion.json', Path(__file__).resolve()]},
      qualification='Decoder and explicit real-candidate materialization integration, not complete algorithm speedup. Every JSON row parsed; no number truncation/tolerance. Historical native creation not borrowed. Full-policy same-environment routing+repair timing remains required.'))
print(dict(passed=True, negative_cases=len(rejected), new_native_calls=0), flush=True)
