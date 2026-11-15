"""Validate exact parser semantics and measure actual isolated read components."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from retained_prefix_workflow import D, read, write, sha
from endpoint_timing_policy import load as reference_load
from endpoint_timing_policy_stream_v1 import load as stream_load

p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
out = a.output.resolve()
out.mkdir(exist_ok=False)
started = time.monotonic()
cases = []
peak = D/'complete_resource_timing_full_flow_01/bnn_native/flow/resource_flow/repair/round_005/candidate_01/reuse_off_evaluation'
roots = [('BNN_actual_peak_candidate', peak),
         ('BNN_native_final', Path(read(D/'complete_resource_timing_full_flow_01/bnn_native/completion.json')['final_state'])),
         ('eltwise_native_final', Path(read(D/'complete_serial_resource_measurement_dev_01/completion.json')['final_state'])),
         ('SB102_domain_final', Path(read(D/'complete_serial_timing_budget_01/sb_domain/completion.json')['final_state']))]
files = [Path(__file__).resolve(), D/'endpoint_timing_policy.py',
         D/'endpoint_timing_policy_stream_v1.py', D/'benchmark_endpoint_loader_worker_v1.py']
hashes = {str(f): sha(f) for f in files}
for label, state in roots:
    complete = read(state/'completion.json')
    assert complete['passed']
    trace = Path(complete['run'])/'native_sta_frontier.jsonl'
    vector = read(state/'endpoint_vector.json')
    assert sha(trace) == vector['trace_sha256']
    cases.append(dict(label=label, state=str(state), trace=str(trace),
                      source_vector_sha256=sha(state/'endpoint_vector.json'),
                      source_completion_sha256=sha(state/'completion.json'),
                      trace_sha256=vector['trace_sha256']))
write(out/'registration.json', dict(pid=os.getpid(),
      start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
      actual_cases=cases, source_sha256=hashes, native_calls=0,
      fixed_run_order=['reference', 'stream'],
      limits=dict(worker_seconds=180, worker_memory_bytes=16*1024**3),
      qualification='Four known actual states/three circuit-architecture contexts, not new independent route samples. Sequential isolated-process component measurements on a shared host, uncontrolled OS cache and order effects. Original loader and full registered algorithms unchanged. No full algorithm memory/time saving inferred from a parser component.'))

base = [dict(type='metadata'),
        dict(type='pin', net=1, pin=2, arbitrary={'still_fully_decoded': [1, 'test']}),
        dict(type='endpoint', node=3, atom_pin=5, name='endpoint_name',
             setup_tags=[dict(launch=0, capture=0, slack_s=1.0000000000000002),
                         dict(launch=0, capture=0, slack_s=-0.0)],
             hold_tags=[dict(launch=0, capture=0, slack_s=2e-12)]),
        dict(type='endpoint', node=1, atom_pin=4, name='unconstrained',
             setup_tags=[dict(launch=0, capture=1, slack_s='+inf')], hold_tags=[]),
        dict(type='timing_metrics', least_slack_CPD_s=13.421610489672275e-9),
        dict(type='complete', endpoint_rows=2)]
variants = {'valid_numeric_duplicate_tag_and_unconstrained': base,
            'empty': [], 'missing_complete': base[:-1],
            'wrong_endpoint_count': base[:-1]+[dict(type='complete', endpoint_rows=1)],
            'duplicate_metrics': base[:-1]+[base[-2], base[-1]],
            'missing_metrics': base[:-2]+[base[-1]],
            'duplicate_endpoint_identity': base[:-1]+[base[2], dict(type='complete', endpoint_rows=3)]}
for value in ['nan', float('inf'), float('nan')]:
    rows = copy.deepcopy(base)
    rows[-2]['least_slack_CPD_s'] = value
    variants['invalid_CPD_'+str(value)] = rows
rows = copy.deepcopy(base)
rows[2]['setup_tags'][1]['slack_s'] = '+inf'
variants['duplicate_tag_numeric_status_mismatch'] = rows
guards = []
fixtures = out/'synthetic'
fixtures.mkdir()
for i, (label, records) in enumerate(variants.items()):
    path = fixtures/f'{i:02d}.jsonl'
    path.write_text(''.join(json.dumps(r)+'\n' for r in records))
    Path(str(path)+'.constraints.echo').write_text('fixed constraints\n')
    outputs = []
    for loader in [reference_load, stream_load]:
        try:
            outputs.append(dict(passed=True, vector=loader(path)))
        except Exception as error:
            outputs.append(dict(passed=False, exception=type(error).__name__))
    assert outputs[0]['passed'] == outputs[1]['passed'], (label, outputs)
    if outputs[0]['passed']:
        assert outputs[0]['vector'] == outputs[1]['vector']
    guards.append(dict(case=label, both_passed=outputs[0]['passed'],
                       reference_exception=outputs[0].get('exception'),
                       stream_exception=outputs[1].get('exception')))
# Invalid JSON in an irrelevant pin must still be decoded and rejected.
path = fixtures/'invalid_unrelated_line.jsonl'
path.write_text(json.dumps(base[0])+'\n{"type":"pin",BROKEN}\n'+
                ''.join(json.dumps(r)+'\n' for r in base[2:]))
Path(str(path)+'.constraints.echo').write_text('fixed constraints\n')
for loader in [reference_load, stream_load]:
    try:
        loader(path)
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError('Malformed unrelated pin was skipped')
guards.append(dict(case='malformed_unrelated_pin', both_passed=False,
                   both_raised='JSONDecodeError'))
write(out/'guard_results.json', guards)

results = []
for case in cases:
    row = dict(case=case['label'], workers={})
    for mode in ['reference', 'stream']:
        target = out/(case['label']+'_'+mode+'.json')
        command = [sys.executable, str(D/'benchmark_endpoint_loader_worker_v1.py'),
                   '--mode', mode, '--trace', case['trace'], '--output', str(target)]
        t = time.monotonic()
        with target.with_suffix('.log').open('w') as log:
            child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            write(out/'active_child.json', dict(pid=child.pid,
                  start_ticks=Path('/proc', str(child.pid), 'stat').read_text().split(') ', 1)[1].split()[19],
                  case=case['label'], mode=mode))
            code = child.wait(timeout=180)
        assert code == 0, (case['label'], mode, code)
        receipt = read(target)
        receipt['outer_worker_seconds'] = time.monotonic()-t
        row['workers'][mode] = receipt
    left, right = (row['workers'][m] for m in ['reference', 'stream'])
    assert left['exact_canonical_vector_sha256'] == right['exact_canonical_vector_sha256']
    # Compare all actual vector fields with the original sealed state too.
    original = read(Path(case['state'])/'endpoint_vector.json')
    import hashlib
    digest = hashlib.sha256(json.dumps(original, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert left['exact_canonical_vector_sha256'] == digest
    assert left['trace_sha256'] == right['trace_sha256'] == case['trace_sha256']
    row['whole_vector_exact_to_sealed_actual_state'] = True
    results.append(row)
    write(out/'results.json', results)
    print(dict(case=case['label'], exact=True,
               reference_RSS_kib=left['process_RSS_high_water_kib'],
               stream_RSS_kib=right['process_RSS_high_water_kib'],
               reference_seconds=left['loader_seconds'], stream_seconds=right['loader_seconds']), flush=True)
assert all(sha(f)==h for f,h in hashes.items())
for case in cases:
    state = Path(case['state'])
    assert sha(state/'endpoint_vector.json') == case['source_vector_sha256']
    assert sha(state/'completion.json') == case['source_completion_sha256']
    assert sha(case['trace']) == case['trace_sha256']
write(out/'completion.json', dict(passed=True, native_calls=0,
      actual_states=len(cases), complete_vector_equality=True,
      synthetic_guards=len(guards), source_sha256=hashes,
      artifact_sha256={n:sha(out/n) for n in ['registration.json','guard_results.json','results.json']},
      complete_validation_seconds=time.monotonic()-started,
      qualification='Every line is decoded by the same stdlib JSON parser. Every endpoint-vector field and canonical numeric serialization equals the original loader and sealed actual source. Only isolated parser time/RSS measured; no full algorithm cost or quality improvement claimed. Full flows remain frozen pending an independent integrated version.'))
