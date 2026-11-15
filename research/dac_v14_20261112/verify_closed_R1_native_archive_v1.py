"""Reconstruct actual R1 recovery states, their original workers and terminal reference."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import load
from multiobjective_acceptance_v2 import decide
from state_resource_assurance import resource_assurance,require_publication_proof
from run_native_scope_policy_v4 import run_dir

archive=D/'multiobjective_closed_R1_native_01';out=archive/'verification.json';assert not out.exists()
c=read(archive/'completion.json');assert c['passed']
assert all(sha(archive/n)==h for n,h in c['artifact_sha256'].items())
assert all(sha(f)==h for f,h in c['source_sha256'].items())
points=read(archive/'points.json');old=read(Path(c['parent'])/'points.json');byid={r['id']:r for r in points}
keys={'quality_dominated_by','nominal_quality_dominated_by','matched_time_dominated_by','quality_projection_retained','quality_status','candidate_retention','archive_retained','record_preserved','five_dimensional_comparison_count','retention_qualification'}
assert len(byid)==len(points)==len(old)+2
for r in old:assert {k:v for k,v in r.items() if k not in keys}=={k:v for k,v in byid[r['id']].items() if k not in keys}
actor=D/'native_checkpoint_recovery_03/bnn_R1_native';closed=read(actor/'completion.json');reg=read(actor/'registration.json');jobs=read(actor/'pool/jobs.json')
assert len(jobs)==closed['native_analysis_children']==1
expected={}
for a in read(actor/'attempts.json'):
 for item in a['pair'].values():
  if item.get('evaluation') and Path(item['evaluation']).is_relative_to(actor):expected[item['evaluation']]=(a,item)
added=[byid[i] for i in c['added']];assert set(expected)=={r['state'] for r in added}
worker_origins=[];audits=[]
for r in added:
 state=Path(r['state']);done=read(state/'completion.json');sr=read(state/'registration.json');a,item=expected[str(state)]
 assert done['passed'] and not done['physical_audit_reused']
 assert require_publication_proof(state)['passed']
 origin=Path(sr['installed_candidate_identity']['origin_worker_receipt']);worker=read(origin)
 assert worker['passed'] and worker['candidate_full_STA_passed'] and worker['native_transaction_succeeded']
 assert all(sha(f)==h for f,h in worker['artifact_sha256'].items())
 native=Path(worker['native_directory']);assert sha(native/'candidate/routed.route')==sha(run_dir(state)/'routed.route')==r['route_sha256']
 assert (native/'candidate/native_state_gate.txt').read_text()=='candidate FULL fresh_STA actual_installed_trees\n'
 assert (native/'candidate_restored/native_state_gate.txt').read_text()=='restored_source FULL fresh_STA actual_installed_trees\n'
 for name in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:assert sha(native/name)==sha(native/'candidate_restored'/name)
 raw=load(native/'candidate/native_sta_frontier.jsonl');raw['endpoint_ids']=[list(e) for e in raw['endpoint_ids']];vector=read(state/'endpoint_vector.json')
 assert all(raw[k]==vector[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
 before=read(Path(a['current_state'])/'endpoint_vector.json');br=resource_assurance(a['current_state'])['resource_axes'];ar=resource_assurance(state)['resource_axes']
 decision=decide('resources_under_timing',before,vector,br,ar,cpd_limit_s=reg['anchor']['CPD_s'],resource_limits=reg['anchor']['resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
 assert decision==item['decision']==r['acceptance'] and not decision['accepted']
 assert r['complete_single_configuration_seconds'] is None and r['complete_recovery_segment_seconds'] is None
 sealpath=Path(done['requires_final_input_seal']);seal=read(sealpath);pool=Path(seal['pool_completion']);assert seal['passed'] and sha(pool)==seal['pool_completion_sha256'] and read(pool)['passed']
 if a['candidate_rank']==1:
  assert not origin.is_relative_to(actor) and item['materialized_completed_fused_candidate'] and item['new_native_search_calls']==item['new_native_LOAD_calls']==0
  assert read(pool)['original_pool_seal_fabricated'] is False
 elif a['candidate_rank']==2:assert origin==Path(jobs[0]['job'])/'completion.json'
 else:raise AssertionError(a['candidate_rank'])
 worker_origins.append(str(origin));audits.append(str(run_dir(state)/'independent_audit.json'))
summary=read(archive/'R1_native_closure_summary.json');event=summary['terminal_event'];terminal=next(r for r in old if r.get('state')==closed['final_state'])
assert event['existing_record_id']==terminal['id'] and event['state']==terminal['state'] and not event['new_observation'] and terminal['id'] not in c['added']
assert {k:terminal[k] for k in ['wirelength','SB_pairs','CB_sources']}==closed['final_resources']
assert all(r['state']!=event['state'] for r in added)
assert c['complete_measured_configurations_total']==24
write(out,dict(passed=True,records=len(points),new_materialized_states=2,new_native_workers_in_recovery=1,reused_completed_historical_workers=1,new_independent_physical_audits=2,legal_rejected_candidates=2,terminal_reference_existing_record=terminal['id'],terminal_checkpoint_not_duplicated=True,parent_non_derived_fields_exact=True,raw_completed_candidate_FULL_STA_vectors_exact=True,fixed_root_decisions_reproduced=True,historical_whole_time_unknown=True,complete_measured_configurations_total=24,native_calls_new=0,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),archive/'completion.json',actor/'completion.json',actor/'pool/jobs.json',actor/'attempts.json',*map(Path,worker_origins),*map(Path,audits)]}))
print(dict(passed=True,records=len(points),new_states=2,only_one_new_native_worker=True,terminal_not_duplicated=True),flush=True)
