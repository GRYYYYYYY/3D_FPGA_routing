"""Compare every routed sink in the actual R1 state to exported native floats."""
import json,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from resource_opportunity_census import stream_trace
from coordinated_repair_tree import from_trace,prefixes
from native_zero_rc_tree_delay_v1 import sink_delays
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof
from full_route_graph_cache import FullRouteGraphCache

started=time.monotonic();output=D/'R1_native_float32_route_delay_validation_01';output.mkdir(exist_ok=False)
state=Path(read(D/'R1_escape_owner_BFS_candidate_01/completion.json')['state']);run=run_dir(state)
require_publication_proof(state);manifest=read(run/'manifest.json');command=manifest['command']
cache=FullRouteGraphCache(command[command.index('--read_rr_graph')+1],D/'full_route_graph_cache_bnn_01')
g=cache.g
cpp=D/'native_resource_census_workspace_01/vpr/src/route/route_tree.cpp'
source_binding=read(D/'native_resource_census_stage_01/binding.json')
assert sha(cpp)==source_binding['source_sha256']['vpr/src/route/route_tree.cpp']
expected={};physical_float64={};nets=0
for row in stream_trace(run/'routed.route'):
 if not row['trace']:continue
 tree=from_trace(row['trace'],g.switches);native=sink_delays(tree,audited_zero_rc=True);exact_sum=prefixes(tree)
 for pin,sink in tree['sinks'].items():
  key=(row['net'],pin);assert key not in expected
  expected[key]=native[pin];physical_float64[key]=exact_sum[sink]
 nets+=1
write(output/'progress.json',dict(status='comparing_complete_native_frontier',routed_nets=nets,predicted_sink_connections=len(expected)))
observed=set();mismatches=[];extra=[];float64_differences=0;max_float64_delta=0.
for line in (run/'native_sta_frontier.jsonl').open():
 if not line.startswith('{"type":"pin","net":'):continue
 row=json.loads(line)
 if row['driver'] or not row['route_tree_present'] or row['global']:continue
 key=(row['net'],row['pin'])
 if key not in expected:
  extra.append(list(key));continue
 assert key not in observed;observed.add(key)
 actual=row['native_net_delay_s'];prediction=expected[key]
 if prediction!=actual:mismatches.append(dict(net=key[0],pin=key[1],actual_native_s=actual,predicted_native_s=prediction))
 delta=abs(physical_float64[key]-actual)
 if delta!=0:float64_differences+=1;max_float64_delta=max(max_float64_delta,delta)
missing=sorted(set(expected)-observed)
write(output/'mismatches.json',dict(native_float32_mismatches=mismatches,missing_native_rows=missing,unexpected_native_routed_pins=extra))
passed=not mismatches and not missing and not extra
files=[Path(__file__).resolve(),D/'native_zero_rc_tree_delay_v1.py',D/'coordinated_repair_tree.py',
 state/'completion.json',run/'manifest.json',run/'routed.route',run/'native_sta_frontier.jsonl',
 D/'native_resource_census_stage_01/binding.json',cpp,cache.directory/'completion.json']
write(output/'cache_identity.json',cache.receipt)
receipt=dict(passed=passed,native_calls_new=0,state=str(state),routed_nets=nets,predicted_sink_connections=len(expected),
 actual_native_sink_connections_compared=len(observed),native_float32_exact_matches=len(observed)-len(mismatches),
 mismatches=len(mismatches),missing_native_rows=len(missing),unexpected_native_routed_pins=len(extra),
 float64_switch_sum_differs_from_native_connections=float64_differences,max_float64_sum_minus_native_absolute_s=max_float64_delta,
 actual_source_native_binary_sha256=sha(command[0]),model_cpp_source_binary_binding=source_binding['binary_sha256'],
 complete_readonly_validation_seconds=time.monotonic()-started,
 source_sha256={str(p):sha(p) for p in files},artifact_sha256={n:sha(output/n) for n in ['mismatches.json','cache_identity.json']},
 qualification='All routed sink connections of one actual independently sealed known-circuit state, not independent benchmark samples. Binary32 path accumulation is compared exactly with actual native exported connection delays; float64 physical switch sums remain a separate quantity. The upcoming Census LOAD model routine is source-bound explicitly; current source binary identity is recorded separately, with compatibility established empirically for this state. Zero node/switch RC and fixed complete graph required; not generalized to RC-loaded graphs, endpoint STA, route legality or candidate acceptance. No native call, new candidate quality, complete algorithm runtime or statistical speedup claimed.')
write(output/'completion.json',receipt);print({k:receipt[k] for k in ['passed','routed_nets','predicted_sink_connections','native_float32_exact_matches','mismatches','float64_switch_sum_differs_from_native_connections','max_float64_sum_minus_native_absolute_s','complete_readonly_validation_seconds']},flush=True)
assert passed,'Preserve mismatch evidence; do not rerun native to repair a model'
