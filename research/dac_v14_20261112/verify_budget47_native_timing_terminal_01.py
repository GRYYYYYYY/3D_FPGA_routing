"""Seal the completed local timing arm while its paired continuation runs."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from seed_census_analysis_pool_v2 import process_identity
from endpoint_timing_policy_streaming_v2 import compare
root=D/'budget47_current_timing_composition_01';actor=root/'native_full462/timing';closed=read(actor/'completion.json');reg=read(actor/'registration.json')
assert closed['passed'] and closed['operator_stop']=='no_admissible_candidate_in_current_portfolio'
p=process_identity(reg['pid']);assert not p or p['state']=='Z' or p['start_ticks']!=reg['start_ticks']
assert all(sha(f)==h for f,h in closed['source_sha256'].items()) and all(sha(f)==h for f,h in reg['source_sha256'].items())
observed=read(root/'queue/results.json')['native_full462'];assert observed['passed'] and observed['returncode']==0
out=D/'budget47_native_timing_terminal_validation_01';out.mkdir(exist_ok=False);snapshot=out/'observed_completed_arm.json';write(snapshot,observed)
steps=read(actor/'steps.json');attempts=read(actor/'attempts.json');assert len(steps)==len(attempts)==closed['accepted_steps']==closed['attempted_proposals']==3
assert all(s['accepted'] and not s['reused_native'] for s in steps)
initial=Path(closed['initial_state']);final=Path(closed['final_state']);source=Path(observed['original_source'])
assert str(final)==steps[-1]['evaluation'] and closed['native_transaction_coordinators_started']==3
iv,sv,fv=[read(s/'endpoint_vector.json') for s in [initial,source,final]]
assert all(iv[k]==sv[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
assert route_body(run_dir(initial)/'routed.route')==route_body(run_dir(source)/'routed.route')
assert read(initial/'completion.json')['passed'] and read(final/'completion.json')['passed'] and read(final/'input_seal.json')['passed']
audit=read(run_dir(final)/'independent_audit.json');assert audit['audit']['passed'];m=audit['physical_metrics'];r=dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=m['sb_pairs_used'],CB_sources=m['cb_crossing_output_sources_used'])
assert r==closed['final_resources']==dict(wirelength=2061249,SB_pairs=47,CB_sources=5060)
assert fv['cpd_s']==closed['final_CPD_s']==1.3228145689936355e-08
archive=D/'multiobjective_budget47_intermediates_02';assert read(archive/'completion.json')['passed']
point=next(p for p in read(archive/'points.json') if p.get('state')==str(final));assert point['quality_status']=='nondominated_in_collected_population'
delta=compare(iv,fv);assert delta['compatible'] and delta['hold_violation_regressions']==0
files=[Path(__file__).resolve(),snapshot,actor/'completion.json',actor/'registration.json',actor/'steps.json',actor/'attempts.json',actor/'process_costs.json',initial/'completion.json',initial/'endpoint_vector.json',source/'endpoint_vector.json',final/'completion.json',final/'input_seal.json',final/'endpoint_vector.json',run_dir(final)/'independent_audit.json',archive/'completion.json']
write(out/'completion.json',dict(passed=True,local_native_timing_arm_terminal=True,paired_comparison_terminal=False,accepted_steps=3,attempted_proposals=3,actual_native_coordinators=3,final_state=str(final),final_CPD_ns=fv['cpd_s']*1e9,final_resources=r,source_reobservation_seconds=observed['source_reobservation_seconds'],complete_timing_segment_process_seconds=observed['complete_timing_segment_process_seconds'],actor_recorded_imported_seconds=closed['complete_imported_state_workflow_seconds'],complete_fresh_route_algorithm_seconds=None,full_endpoint_comparison=delta,source_sha256={str(f):sha(f) for f in files},qualification='Completed registered native_full462 local timing menu from an unrestricted candidate created at a guided48SB source. Not a pristine-native full resource trajectory. Source reobservation and actual complete timing segment are separate measured phases; original resource candidate creation, caches/initial routing excluded and never spliced. All three accepted actual candidates were individually input sealed/FULL/STA/physically audited and retained in immutable archive snapshots; no live attempt file bound. Paired guided_budget54 continuation still runs independently under the same original absolute caps. Earlier archive records retain their observed intermediate-snapshot labels; this later terminal receipt supplies the phase completion fact without rewriting them. No cold full-algorithm cost or statistical runtime claim.'))
print(dict(passed=True,local_native_arm_terminal=True,paired_comparison_terminal=False,CPD_ns=fv['cpd_s']*1e9,resources=r,timing_segment_seconds=observed['complete_timing_segment_process_seconds'],source_reobservation_seconds=observed['source_reobservation_seconds']),flush=True)
