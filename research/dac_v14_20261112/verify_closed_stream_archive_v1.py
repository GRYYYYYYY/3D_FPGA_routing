"""Independent archive accounting and scope checks against the original proofs."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import compare
from orphaned_flow_time_evidence_v2 import recover_original_time

root=D/'multiobjective_closed_stream_quality_01';c=read(root/'completion.json');assert c['passed']
assert not (root/'verification.json').exists()
assert all(sha(root/n)==h for n,h in c['artifact_sha256'].items())
points=read(root/'points.json');parent=Path(c['parent']);old=read(parent/'points.json')
assert len(points)==len(old)+len(c['added']) and len({p['id'] for p in points})==len(points)
add=[p for p in points if p['id'] in c['added']]
case=D/'complete_BNN_closed_stream_flow_01/bnn_native_closed_stream'
quality_path=D/'orphaned_BNN_quality_analysis_02/completion.json';quality=read(quality_path)
assert quality['passed'] and quality['complete_configuration_quality_verified']
assert not (case/'completion.json').exists() and not (case/'measurement/completion.json').exists()
gnu=recover_original_time(case)
initial=read(Path(quality['initial_state'])/'endpoint_vector.json')
for p in add:
    state=Path(p['state']);done=read(state/'completion.json');assert done['passed']
    run=Path(done['run']);assert sha(run/'routed.route')==p['route_sha256']
    assert read(run/'manifest.json')['metrics']['native_full_check_passed']
    audit=read(run/'independent_audit.json');assert audit['audit']['passed']
    vector=read(state/'endpoint_vector.json');assert p['CPD_ns']==vector['cpd_s']*1e9
    assert p['endpoint_vector_sha256']==sha(state/'endpoint_vector.json')
    assert p['endpoint_changes_against_own_initial']==compare(initial,vector)
    metrics=audit['physical_metrics']
    for field,key in [('wirelength','planar_wirelength_excluding_sb_half_nodes'),('SB_pairs','sb_pairs_used'),('CB_sources','cb_crossing_output_sources_used')]:assert p[field]==metrics[key]
    assert p['timing_cohort'] is None and not p['matched_time_dominated_by'] and p['five_dimensional_comparison_count']==0
    assert p['complete_configuration_measurement'] is None and p['complete_observer_wall_seconds'] is None
    if not p['actor_final_selected']:
        assert p['complete_single_configuration_seconds'] is None and p['memory_observation'] is None
finals=[p for p in add if p['actor_final_selected']];assert len(finals)==1
p=finals[0];assert p['state']==quality['final_state'] and p['record_kind']=='complete_quality_final_qualified_GNU_time'
assert p['complete_single_configuration_seconds']==gnu['elapsed_seconds'] and p['complete_time_display_resolution_seconds']==gnu['display_resolution_seconds']
assert p['memory_observation']['waited_process_RSS_high_water_kib']==gnu['waited_process_RSS_high_water_kib']
assert all(p['memory_observation'][k] is None for k in ['sampled_tree_RSS_peak_kib','sampled_tree_PSS_peak_kib','observer_CPU_seconds'])
inventory=read(root/'complete_configuration_inventory.json');rows=inventory['configurations']
previous=read(parent/'complete_configuration_inventory.json')['configurations']
assert rows[:len(previous)]==previous
assert len(rows)==len({r['case'] for r in rows})==inventory['complete_quality_configurations']==c['complete_quality_configurations_total']
observed=[r for r in rows if r['measurement'] is not None];qualified=[r for r in rows if r['measurement'] is None]
assert len(observed)==inventory['complete_observer_measured_configurations']==c['complete_measured_configurations_total']
assert len(qualified)==inventory['qualified_GNU_only_configurations']==c['qualified_GNU_only_configurations']==1
assert qualified[0]['proof']==str(quality_path) and qualified[0]['state']==p['state']
for r in observed:
    proof=read(r['proof']);measurement=read(r['measurement'])
    assert proof['passed'] and measurement['passed'] and proof['complete_configuration_verified']
    assert r['complete_seconds']==proof['complete_wall_seconds']==measurement['complete_command_wall_seconds']
    assert r['quality']==dict(CPD_ns=proof['CPD_ns'],**proof['resources'])
assert sum(p['phase']=='resource' and not p['transition_committed'] for p in add)>0,'Legal rejected observations missing'
write(root/'verification.json',dict(passed=True,records=len(points),added=len(add),
    complete_quality_configurations=len(rows),complete_observer_measured_configurations=len(observed),
    qualified_GNU_only_configurations=len(qualified),old_inventory_rows_exact=True,
    actual_route_audit_vector_primary_proofs_match=True,legal_rejected_states_preserved=True,
    original_missing_receipts_still_absent=True,only_final_carries_whole_elapsed=True,
    no_qualified_time_in_matched_dominance=True,native_calls_new=0,new_independent_inputs=0,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),root/'completion.json',root/'complete_configuration_inventory.json',quality_path,case/'measurement/gnu_time.txt']}))
print(dict(passed=True,records=len(points),quality_configs=len(rows),observer_configs=len(observed),qualified_GNU_configs=len(qualified)))
