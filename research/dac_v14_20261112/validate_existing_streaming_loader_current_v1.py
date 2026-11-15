"""Reuse production streaming v2; validate actual current traces and guard scope."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from retained_prefix_workflow import D, read, write, sha
from endpoint_timing_policy_streaming_v2 import load as production
from endpoint_timing_policy_stream_v1 import load as prototype

p = D/'existing_streaming_loader_current_validation_01'
p.mkdir(exist_ok=False)
started = time.monotonic()
prior = D/'streaming_endpoint_loader_validation_01'
assert read(prior/'completion.json')['passed']
cases = read(prior/'registration.json')['actual_cases']
files = [Path(__file__).resolve(), D/'endpoint_timing_policy_streaming_v2.py',
         D/'endpoint_timing_policy_stream_v1.py', D/'benchmark_endpoint_loader_worker_v2.py',
         prior/'completion.json', prior/'results.json',
         D/'endpoint_loader_streaming_validation_01/completion.json',
         D/'endpoint_loader_streaming_integration_01/completion.json']
bindings = {str(f):sha(f) for f in files}
for old in ['endpoint_loader_streaming_validation_01', 'endpoint_loader_streaming_integration_01']:
    proof = read(D/old/'completion.json')
    assert proof['passed'] and all(sha(f)==h for f,h in proof['source_sha256'].items())
write(p/'registration.json', dict(pid=os.getpid(),
      start_ticks=Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19],
      source_sha256=bindings, cases=cases, native_calls=0,
      adopted_loader='endpoint_timing_policy_streaming_v2',
      prototype_adopted=False,
      qualification='Existing production parser and its stronger COMPLETE/pin-count guards are reused. Four sealed actual states; old prototype result is only an independent reference digest, not a production implementation. Only isolated component cost; no full-flow result.'))
tiny = D/'endpoint_loader_streaming_integration_01/healthy_real_tiny.jsonl'
raw = tiny.read_text().splitlines()
complete = json.loads(raw[-1])
assert complete['type'] == 'complete' and complete['pin_rows'] > 0
fixtures = {
    'pin_count_mismatch': raw[:-1]+[json.dumps(dict(complete, pin_rows=complete['pin_rows']+1))],
    'trailing_second_complete': raw+[raw[-1]],
}
guards = []
for name, lines in fixtures.items():
    path = p/(name+'.jsonl')
    path.write_text('\n'.join(lines)+'\n')
    Path(str(path)+'.constraints.echo').write_bytes(Path(str(tiny)+'.constraints.echo').read_bytes())
    outcomes = {}
    for label, loader in [('prototype', prototype), ('production', production)]:
        try:
            loader(path)
        except Exception as error:
            outcomes[label] = dict(accepted=False, exception=type(error).__name__)
        else:
            outcomes[label] = dict(accepted=True)
    assert outcomes['prototype']['accepted'] and not outcomes['production']['accepted']
    guards.append(dict(case=name, outcomes=outcomes))
write(p/'guard_difference.json', guards)
rows = []
references = {r['case']:r['workers']['reference'] for r in read(prior/'results.json')}
for case in cases:
    result = p/(case['label']+'.json')
    command = [sys.executable, str(D/'benchmark_endpoint_loader_worker_v2.py'),
               '--mode', 'stream', '--trace', case['trace'], '--output', str(result)]
    with result.with_suffix('.log').open('w') as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        write(p/'active_child.json', dict(pid=child.pid,
              start_ticks=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19],
              case=case['label']))
        try:
            code = child.wait(timeout=180)
        except subprocess.TimeoutExpired:
            child.kill(); child.wait()
            raise
    assert code == 0, case['label']
    actual = read(result)
    assert actual['loader_module'] == 'endpoint_timing_policy_streaming_v2'
    original = references[case['label']]
    assert actual['exact_canonical_vector_sha256'] == original['exact_canonical_vector_sha256']
    assert actual['trace_sha256'] == case['trace_sha256']
    assert sha(Path(case['state'])/'completion.json') == case['source_completion_sha256']
    rows.append(dict(case=case['label'], all_fields_exact=True, component=actual))
    write(p/'results.json', rows)
    print(dict(case=case['label'], exact=True, seconds=actual['loader_seconds'],
               proc_VmHWM_kib=actual['proc_memory_after']['VmHWM']), flush=True)
assert all(sha(f)==h for f,h in bindings.items())
write(p/'completion.json', dict(passed=True, actual_states=4, all_vectors_exact=True,
      production_parser='endpoint_timing_policy_streaming_v2', prototype_adopted=False,
      prototype_guard_gaps_demonstrated=len(guards), native_calls=0,
      source_sha256=bindings,
      artifact_sha256={n:sha(p/n) for n in ['registration.json','results.json','guard_difference.json']},
      complete_validation_seconds=time.monotonic()-started,
      qualification='Existing stronger parser reused. Prototype duplicates prior work and omits existing guards; retained as diagnostic, never integrated. Current parser/canonical vectors checked against all four actual sealed states. VmHWM records the process after exec; getrusage high water is retained separately because inherited pre-exec peaks can impose a floor. Component RSS/time cannot substitute for complete algorithm memory/time.'))
