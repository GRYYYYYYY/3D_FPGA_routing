#!/usr/bin/env python3
"""Compare actual phase-order endpoints and reuse exact graph-only path references."""
import math
import time
from pathlib import Path
import numpy as np
from retained_prefix_workflow import D, read, write, sha, route_body
from endpoint_timing_policy_streaming_v2 import compare
from run_native_scope_policy_v4 import run_dir
from resource_opportunity_census import stream_trace
from coordinated_repair_tree import from_trace, prefixes

started = time.monotonic()
out = D / 'resource_first_composition_01.json'
assert not out.exists()
state = D / 'resource_first_timing_resume_01/timing/round_002/proposal_01/transaction/current_group_evaluation'
reference = D / 'strong_A0_fast_K8_resource_dev_01/paired_K8/round_001/candidate_00/reuse_on_evaluation'
steps = read(D / 'resource_first_timing_resume_01/timing/steps.json')[:3]
assert len(steps) == 3 and all(s['accepted'] for s in steps) and steps[-1]['evaluation'] == str(state)
rd, ref = run_dir(state), run_dir(reference)
for route_state in [state, reference]:
    assert read(route_state / 'completion.json')['passed']
    assert read(run_dir(route_state) / 'independent_audit.json')['audit']['passed']
sv, rv = read(state / 'endpoint_vector.json'), read(reference / 'endpoint_vector.json')
comparison = compare(rv, sv)
assert comparison['compatible']
def resources(run):
    physical = read(run / 'independent_audit.json')['physical_metrics']
    return dict(wirelength=physical['planar_wirelength_excluding_sb_half_nodes'],
        SB_pairs=physical['sb_pairs_used'], CB_sources=physical['cb_crossing_output_sources_used'])
same_quality = sv['cpd_s'] == rv['cpd_s'] and resources(rd) == resources(ref)
assert same_quality
for name in ['packed.net', 'placed.place']:
    assert sha(rd / name) == sha(ref / name)
cone_path = state.parent / 'current_group_successor_cone.json'
cone = read(cone_path)
assert Path(cone['source_state']) == state
needed = {(r['net'], r['pin']) for r in cone['routed_connections']}
potential = read(D / 'full_root_timing_potential_02/completion.json')
assert potential['passed']
old_rows = {(r['net'], r['pin']): r for r in potential['rows']}
cases = {(r['net'], r['pin']): r for r in read(D / 'full_root_timing_potential_02/cases.json')}
assert needed <= old_rows.keys()
manifest = read(rd / 'manifest.json')
graph = manifest['command'][manifest['command'].index('--read_rr_graph') + 1]
binding = read(D / 'bnn_physical_query_graph_01/graph_binding.json')
assert manifest['shared_inputs'][graph]['sha256'] == binding['source_rrg_sha256']
cache = D / 'rr_audit_cache_bnn_01'
cache_completion = read(cache / 'completion.json')
assert cache_completion['passed'] and cache_completion['graph_sha256'] == binding['source_rrg_sha256']
assert sha(cache / 'switches.npy') == cache_completion['payload_sha256']['switches.npy']
delays = np.load(cache / 'switches.npy', allow_pickle=False)
switches = {i: float(v) for i, v in enumerate(delays) if math.isfinite(v)}
rows = []
for record in stream_trace(rd / 'routed.route'):
    keys = [key for key in needed if key[0] == record['net']]
    if not keys:
        continue
    tree = from_trace(record['trace'], switches)
    distance = prefixes(tree)
    for key in keys:
        case = cases[key]
        assert tree['root'] == case['root'] and tree['sinks'][key[1]] == case['sink']
        current = distance[tree['sinks'][key[1]]]
        lower = old_rows[key]['root_only_relaxed_distance_s']
        rows.append(dict(net=key[0], pin=key[1], current_actual_switch_distance_s=current,
            reused_exact_root_only_relaxation_s=lower, difference_ns=(current - lower) * 1e9,
            independent_query_reference='full_root_timing_potential_02/completion.json',
            query_reexecuted=False))
assert {(row['net'], row['pin']) for row in rows} == needed
last_tx = state.parent
transaction = read(last_tx / 'current_group_audit/analysis.json')
decision = read(last_tx / 'current_group_decisions.json')
files = [Path(__file__).resolve(), D / 'endpoint_timing_policy_streaming_v2.py', D / 'actual_route_tree_identity.py',
    cone_path, last_tx / 'registration.json', last_tx / 'current_group_audit/analysis.json',
    last_tx / 'current_group_decisions.json', D / 'full_root_timing_potential_02/completion.json',
    D / 'full_root_timing_potential_02/cases.json', D / 'bnn_physical_query_graph_01/graph_binding.json',
    cache / 'completion.json', cache / 'switches.npy']
for route_state in [state, reference]:
    files += [route_state / 'completion.json', route_state / 'endpoint_vector.json',
        run_dir(route_state) / 'manifest.json', run_dir(route_state) / 'independent_audit.json',
        run_dir(route_state) / 'routed.route']
write(out, dict(passed=True, resource_first_state=str(state), timing_first_reference=str(reference),
    resource_first_accepted_prefix=steps, same_CPD_wire_SB_CB=same_quality,
    CPD_ns=sv['cpd_s'] * 1e9, resources=resources(rd),
    serialized_route_body_exact=route_body(rd / 'routed.route') == route_body(ref / 'routed.route'),
    endpoint_comparison_reference_to_resource_first=comparison,
    third_transaction=dict(queries=read(last_tx / 'registration.json')['roles']['current_group']['queries'],
        changed_connection_switch_distances=transaction['changed_delays'],
        strict_accepts=decision['strict']['accepted'], endpoint_vector_accepts=decision['endpoint_vector']['accepted'],
        native_connection_query_seconds=sum(q['seconds'] for q in transaction['queries']),
        native_transaction_seconds=transaction['native_transaction_seconds']),
    current_winning_connection_reference=rows,
    all10_current_winning_switch_distances_exactly_equal_reused_optimistic_reference=all(row['difference_ns'] == 0 for row in rows),
    native_calls=0, query_calls=0, complete_single_configuration_algorithm_seconds=None,
    source_sha256={str(path): sha(path) for path in files}, complete_analysis_seconds=time.monotonic() - started,
    qualification='A third accepted prefix reaches an existing four-axis quality coordinate, not a new frontier or proof of phase commutation. Whole endpoint vector and serialized route may differ. Known exact source-only static-switch distances are reused only after graph, root and sink identity match; no search repeated for reporting. Relaxation omits background occupancy, mandatory closure and whole-net sharing; equal static distances are not a native-STA global optimality proof. Current operator may continue to refresh STA; recovery-segment and historical creation times are not assembled into one cold configuration.'))
print(dict(same_quality=same_quality, setup_better=comparison['setup_improved'], setup_worse=comparison['setup_regressed'],
    reused_path_queries=len(rows), zero_potential=all(row['difference_ns'] == 0 for row in rows),
    third_query_seconds=sum(q['seconds'] for q in transaction['queries'])), flush=True)
