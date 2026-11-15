"""Verify quality advance and exact policy rejection of the new owner exchange."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

archive=D/'multiobjective_feedback_exchange_candidates_01'
c=read(archive/'completion.json');assert c['passed'] and c['records']==393
assert all(sha(archive/f)==h for f,h in c['artifact_sha256'].items())
points=read(archive/'points.json');summaries=read(archive/'transaction_summaries.json')['transactions']
new=next(s for s in summaries if s['actual_proposal']=='critical_owner_exchange_000_target_first')
assert new['resources']==dict(wirelength=2061257,SB_pairs=45,CB_sources=5060)
assert new['CPD_ns']==13.413972155262854
assert new['setup_improved']==new['setup_regressed']==1 and new['hold_violation_regressions']==0
assert new['native_strict_accepts'] and not new['endpoint_vector_accepts']
assert new['quality_status']=='nondominated_in_collected_population'
assert 2.486609<new['minimum_regressed_setup_distance_above_new_worst_ns']<2.486610
point=next(p for p in points if p.get('state')==new['state'])
prior=next(p for p in points if p['id']=='low_resource_dual_timing_02/strict/round_001/proposal_01/transaction/current_group_evaluation/runs/state')
group=next(p for p in points if p['arm']=='sealed_timing_proposal_02')
for other in [prior,group]:
    assert all(point[k]==other[k] for k in ['CPD_ns','SB_pairs','CB_sources','physical_identity','quality_cohort'])
    assert other['quality_status']=='dominated'
assert prior['wirelength']-point['wirelength']==40 and group['wirelength']-point['wirelength']==36
assert not point['transition_committed'] and not point['actor_terminal_claim']
unchanged=[s for s in summaries if s['actual_proposal'] in ['all_positive_target_only','all_positive_owner_only']]
assert len(unchanged)==2 and all(s['setup_improved']==s['setup_regressed']==0 for s in unchanged)
out=D/'feedback_exchange_candidates_validation_01';out.mkdir(exist_ok=False)
write(out/'completion.json',dict(passed=True,records=393,new_candidate=new,
    wire_saved_vs_previous_equal_quality=40,wire_saved_vs_preceding_combined=36,
    native_calls=0,actor_terminal_claim=False,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),archive/'completion.json',archive/'points.json',archive/'transaction_summaries.json',D/'feedback_exchange_attempts_snapshot_01.json']},
    qualification='Three sealed actual candidates retained, including two unchanged outcomes. Only the exchange adds a quality coordinate; no independent circuit/sample, completed strict trajectory or complete-cost claim. Both earlier equal-timing/vertical candidates are now dominated in the updated quality archive.'))
print(dict(passed=True,wire_saved=40,preceding_combined_wire_saved=36,setup_improved=1,setup_regressed=1,native_calls=0),flush=True)
