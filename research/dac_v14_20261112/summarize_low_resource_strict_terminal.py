#!/usr/bin/env python3
"""Final strict composition, vector/near-tail changes and exact reference reuse."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir
from endpoint_timing_policy_streaming_v2 import compare
from coordinated_repair_tree import from_trace,prefixes
from resource_opportunity_census import stream_trace
from immutable_rr_audit_cache import GraphAuditCache
from run_native_frontier_queries import fingerprint

out=D/'low_resource_strict_terminal_summary_01.json';assert not out.exists()
actor=D/'low_resource_dual_timing_02/strict';terminal=read(actor/'completion.json');assert terminal['passed'] and terminal['accepted_steps']==3
initial,final=Path(terminal['initial_state']),Path(terminal['final_state'])
assert read(final/'completion.json')['passed'] and read(final/'input_seal.json')['passed']
before,after=read(initial/'endpoint_vector.json'),read(final/'endpoint_vector.json')
whole=compare(before,after);assert whole['compatible'] and whole['cpd_strictly_better'] and not whole['hold_violation_regressions']
known=read(D/'strong_A0_paired_K8_summary_01.json');other=Path(known['final_state'])
old=read(other/'endpoint_vector.json');cross=compare(old,after);assert cross['compatible'] and old['cpd_s']==after['cpd_s']
oldmetrics=read(run_dir(other)/'independent_audit.json')['physical_metrics'];newmetrics=read(run_dir(final)/'independent_audit.json')['physical_metrics']
cone_path=final.parent/'current_group_successor_cone.json';cone=read(cone_path);assert cone['passed'] and Path(cone['source_state'])==final
m=read(run_dir(final)/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
cache=GraphAuditCache(graph,D/'rr_audit_cache_bnn_01')
reference=D/'full_root_timing_potential_02';ref=read(reference/'completion.json');assert ref['passed']
assert all(sha(reference/n)==h for n,h in ref['artifact_sha256'].items())
lookup={fingerprint(c,0):c for c in read(reference/'cases.json')};distances={(r['net'],r['pin']):r['root_only_relaxed_distance_s'] for r in ref['rows']}
needed={r['net'] for r in cone['routed_connections']}
trees={r['net']:from_trace(r['trace'],cache.switches) for r in stream_trace(run_dir(final)/'routed.route') if r['net'] in needed}
rows=[]
for connection in cone['routed_connections']:
    net,pin=connection['net'],connection['pin'];tree=trees[net];root=tree['root'];sink=tree['sinks'][pin]
    case=dict(net=net,pin=pin,sink=sink,retained=[root],anchors={str(root):0.},blocked=[])
    fp=fingerprint(case,0)
    if fp not in lookup:
        rows.append(dict(net=net,pin=pin,status='unknown_no_matching_reference'));continue
    previous=lookup[fp];assert previous['root']==root and previous['sink']==sink
    value=prefixes(tree)[sink];distance=distances[net,pin]
    rows.append(dict(net=net,pin=pin,status='exact_static_reference_reused',
        current_switch_seconds=value,source_only_static_seconds=distance,potential_ns=(value-distance)*1e9))
files=[Path(__file__).resolve(),actor/'registration.json',actor/'completion.json',actor/'steps.json',
    initial/'endpoint_vector.json',final/'endpoint_vector.json',final/'input_seal.json',cone_path,
    D/'strong_A0_paired_K8_summary_01.json',other/'endpoint_vector.json',reference/'completion.json',reference/'cases.json',
    reference/'query_stdout.log',run_dir(final)/'independent_audit.json']
write(out,dict(passed=True,operator_stop=terminal['operator_stop'],accepted_steps=3,
    final_state=str(final),CPD_initial_ns=before['cpd_s']*1e9,CPD_final_ns=after['cpd_s']*1e9,
    final_resources=terminal['final_resources'],whole_endpoint_comparison=whole,
    same_CPD_old79SB_reference=str(other),old79_vs_new45_complete_endpoint_comparison=cross,
    equal_CPD_resource_tradeoff=dict(extra_wire=newmetrics['planar_wirelength_excluding_sb_half_nodes']-oldmetrics['planar_wirelength_excluding_sb_half_nodes'],
        fewer_SB=oldmetrics['sb_pairs_used']-newmetrics['sb_pairs_used'],fewer_CB=oldmetrics['cb_crossing_output_sources_used']-newmetrics['cb_crossing_output_sources_used']),
    selected_endpoints=cone['selected_endpoints'],current_winning_connection_references=rows,
    reused_reference_count=sum(r['status']=='exact_static_reference_reused' for r in rows),new_queries=0,native_calls=0,
    all_known_source_only_gaps_exactly_zero=all(r['potential_ns']==0 for r in rows if 'potential_ns' in r),
    complete_imported_strict_workflow_seconds=terminal['complete_imported_state_workflow_seconds'],
    complete_single_configuration_algorithm_seconds=None,secondary_branch_still_separate=True,
    source_sha256={str(path):sha(path) for path in files},
    qualification='Terminal strict repair phase from registered seven-accept45SB prefix, not final43SB resource input or complete cold algorithm. Same-CPD old79SB point has different opportunities/versions; resource tradeoff is descriptive, not matched whole-algorithm superiority. Reused optimistic zero-RC distances are not feasible whole-net routes or native global-STA bounds. Local menu/reference exhaustion does not terminate research.'))
print(dict(passed=True,CPD_ns=after['cpd_s']*1e9,resources=terminal['final_resources'],
    source_comparison=(whole['setup_improved'],whole['setup_regressed']),
    old79_comparison=(cross['setup_improved'],cross['setup_regressed']),reference_count=len(rows),
    reused=sum('potential_ns' in r for r in rows)),flush=True)
