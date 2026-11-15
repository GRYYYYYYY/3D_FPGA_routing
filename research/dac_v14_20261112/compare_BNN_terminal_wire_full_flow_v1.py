"""Compare actual final tradeoff/cost only after verifying the common resource prefix."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from complete_resource_prefix_equivalence_v1 import compare
from endpoint_timing_policy_streaming_v2 import compare as compare_vectors
root=D/'complete_BNN_terminal_wire_flow_01';actual=root/'bnn_native_terminal_wire';baseline=D/'complete_BNN_closed_stream_flow_01/bnn_native_closed_stream'
results=read(root/'queue/results.json');key='bnn_native_terminal_wire'
if not results[key]['passed']:
 write(root/'comparison.json',dict(passed=True,execution_legal=False,quality_comparison_available=False,status=results[key]['failure_stage'],actual=results[key],native_calls_new=0,qualification='Failed registered full configuration retained without quality or inferred speedup.'))
 raise SystemExit(0)
a,b=[read(p/'completion.json') for p in [actual,baseline]];assert a['passed'] and b['passed']
shared=compare(actual,baseline)
va,vb=[read(Path(p['final_state'])/'endpoint_vector.json') for p in [b,a]]
fields={k:a['resources'][k]-b['resources'][k] for k in a['resources']}
files=[Path(__file__).resolve(),D/'complete_resource_prefix_equivalence_v1.py',actual/'completion.json',baseline/'completion.json',root/'queue/results.json',*map(Path,shared['compared_files'])]
write(root/'comparison.json',dict(passed=True,execution_legal=True,quality_comparison_available=shared['resource_prefix_actual_states_requests_and_native_work_exact'],prefix=shared,actual={k:a[k] for k in ['final_state','CPD_ns','resources','complete_wall_seconds','terminal_wire_commits']},baseline={k:b[k] for k in ['final_state','CPD_ns','resources','complete_wall_seconds']},terminal_minus_baseline=fields,terminal_minus_baseline_CPD_ns=a['CPD_ns']-b['CPD_ns'],descriptive_terminal_minus_baseline_seconds=a['complete_wall_seconds']-b['complete_wall_seconds'],final_endpoint_comparison=compare_vectors(va,vb),source_sha256={str(f):sha(f) for f in dict.fromkeys(files)},native_calls_new=0,qualification='One actual full fresh configuration with optional endpoint-safe wire selection before timing, compared with the previously registered explicit-cache/streaming native full control on the same physical inputs/phase binaries/root rules. Common original resource prefix verified independently; differing prefix disqualifies single-change attribution without deleting actual outcomes. Timing targets are reselected from each real resource state; no old final tree or candidate is injected. Quality/time/memory belong to each actual full command; shared-host single observations are not statistical speedup.'))
print(dict(passed=True,prefix_exact=shared['resource_prefix_actual_states_requests_and_native_work_exact'],quality_delta=fields,whole_seconds=a['complete_wall_seconds']),flush=True)
