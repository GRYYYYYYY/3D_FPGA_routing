"""Bind live-actor attempt snapshot to individually sealed candidate evidence."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

out=D/'feedback_successor_candidates_validation_01';out.mkdir(exist_ok=False)
actor=D/'rejection_feedback_controller_dev_01/endpoint'
snapshot=out/'observed_attempts.json';snapshot.write_bytes((actor/'attempts.json').read_bytes())
attempts=read(snapshot);archive=D/'multiobjective_feedback_successor_candidates_01'
c=read(archive/'completion.json');assert c['passed'] and c['records']==390
assert all(sha(archive/f)==h for f,h in c['artifact_sha256'].items())
assert all(sha(f)==h for f,h in c['source_sha256'].items())
summaries=read(archive/'transaction_summaries.json')['transactions']
for s in summaries:
    row=next(r for r in attempts if r.get('evaluation')==s['state'])
    assert not row['accepted'] and not row['policy_accepted']
    assert row['reason']=='Setup endpoint/domain vector has regressions'
    assert row['after_CPD_s']*1e9==s['CPD_ns'] and row['after_resources']==s['resources']
    assert s['native_strict_accepts'] and not s['endpoint_vector_accepts']
    assert s['hold_violation_regressions']==0 and not s['aggregate_feedback_surviving_actions']
new=summaries[1];assert new['quality_status']=='nondominated_in_collected_population'
old=read(D/'multiobjective_completed_seed_transfer_01/points.json')
matches=[p for p in old if p['CPD_ns']==new['CPD_ns'] and p['SB_pairs']==45 and p['CB_sources']==5060]
assert len(matches)==1
previous=matches[0];assert previous['wirelength']-new['resources']['wirelength']==4
write(out/'completion.json',dict(passed=True,observed_candidate_records=2,actor_terminal_claim=False,
    new_nondominated_candidate=new,previous_same_CPD_SB_CB_state=previous['id'],wire_saved=4,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),snapshot,archive/'completion.json',archive/'transaction_summaries.json',D/'multiobjective_completed_seed_transfer_01/points.json']},
    qualification='Original endpoint actor continues its registered policy. Candidate is rejected there, legal and nondominated in the four-axis archive. Strict acceptance is an alternate-policy observation, not a completed strict continuation. Full cold cost unknown.'))
print(dict(passed=True,wire_saved=4,setup_improved=11,setup_regressed=17,native_calls=0),flush=True)
