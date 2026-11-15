"""Verify terminal Tf transfer, preserving its dominated quality outcome."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

actor=D/'stable_seed_transfer_recovery_02/bnn_Tf_paired';q=actor.parent/'queue'
for p in [q,actor]:
    reg=read(p/'registration.json');live=process_identity(reg['pid'])
    assert not live or live['state']=='Z' or live['start_ticks']!=reg['start_ticks']
assert read(q/'completion.json')['passed']
closed=read(actor/'completion.json');assert closed['passed']
assert closed['operator_stop']=='no_admissible_move_in_registered_current_rank_windows'
assert closed['accepted_steps']==closed['attempted_scopes']==12
assert closed['native_analysis_children']==25
assert closed['initial_CPD_s']==closed['final_CPD_s']==1.3421610489672275e-08
assert all(sha(p)==h for p,h in closed['source_sha256'].items())
assert read(actor/'pool/completion.json')['passed'] and read(actor/'evaluation_context/input_seal.json')['passed']
archive=D/'multiobjective_Tf_seed_complete_01';receipt=read(archive/'completion.json')
assert receipt['passed'] and receipt['records']==428 and len(receipt['added'])==24
assert all(sha(archive/n)==h for n,h in receipt['artifact_sha256'].items())
points=read(archive/'points.json');point=next(p for p in points if p.get('state')==closed['final_state'])
assert point['quality_status']=='dominated' and point['actor_final_selected']
strong=next(p for p in points if p['arm']=='complete_resource_paired_then_current_STA_native')
assert strong['id'] in point['quality_dominated_by']
summary=read(archive/'actor_summaries.json')['actors'][0]
assert summary['root_to_final_resource_delta']==dict(wirelength=1721,SB_pairs=-62,CB_sources=-2)
files=[Path(__file__).resolve(),actor/'completion.json',q/'completion.json',archive/'completion.json',archive/'points.json',archive/'actor_summaries.json']
write(D/'Tf_fixed_seed_resource_closure_01.json',dict(passed=True,accepted_steps=12,legal_candidates=24,
    root_to_final_resource_delta=summary['root_to_final_resource_delta'],final_CPD_ns=point['CPD_ns'],final_resources=closed['final_resources'],
    imported_workflow_seconds=closed['complete_imported_algorithm_workflow_seconds'],complete_cold_seconds=None,
    quality_status='dominated',existing_dominating_state=strong['id'],
    source_sha256={str(p):sha(p) for p in files},
    qualification='Fixed policy transfers legal vertical-resource refinement to Tf but does not advance the existing joint quality frontier. All legal OFF/ON candidates retained. Tf-native own-current checkpoint remains unsealed; local paired controls are not a completed native trajectory. One BNN root, not an independent circuit sample.'))
cohort=read(D/'completed_seed_transfer_summary_01.json');cohort.update(completed_roles=6,Tf_paired=summary,
    pending=['R1-native checkpoint recovery','Tf-native checkpoint recovery'])
cohort['source_sha256'].update({str(p):sha(p) for p in [D/'completed_seed_transfer_summary_01.json',D/'Tf_fixed_seed_resource_closure_01.json',archive/'completion.json']})
cohort['qualification']='Six of eight registered roles on two circuits; both native checkpoint continuations remain pending. Tf resource savings are real, but its final quality is dominated by existing strong A0 resource/timing. R1/Tf local OFF/ON controls do not replace their own-current native trajectories. Costs remain version/output specific.'
write(D/'completed_seed_transfer_summary_02.json',cohort)
print(dict(passed=True,completed_roles=6,Tf_SB=43,frontier_advance=False,native_calls=0),flush=True)
