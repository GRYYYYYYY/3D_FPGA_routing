"""Independently reconstruct new Tf workers, actual vectors and fixed-root decisions."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import load
from multiobjective_acceptance_v2 import decide
from state_resource_assurance import resource_assurance,require_publication_proof
from run_native_scope_policy_v4 import run_dir

archive=D/'multiobjective_closed_Tf_native_01';out=archive/'verification.json';assert not out.exists()
c=read(archive/'completion.json');assert c['passed']
assert all(sha(archive/n)==h for n,h in c['artifact_sha256'].items())
assert all(sha(f)==h for f,h in c['source_sha256'].items())
points=read(archive/'points.json');old=read(Path(c['parent'])/'points.json');byid={r['id']:r for r in points}
derived={'quality_dominated_by','nominal_quality_dominated_by','matched_time_dominated_by','quality_projection_retained','quality_status','candidate_retention','archive_retained','record_preserved','five_dimensional_comparison_count','retention_qualification'}
assert len(byid)==len(points)==574
for r in old:assert {k:v for k,v in r.items() if k not in derived}=={k:v for k,v in byid[r['id']].items() if k not in derived}
actor=D/'native_checkpoint_recovery_02/bnn_Tf_native';closed=read(actor/'completion.json');reg=read(actor/'registration.json')
jobs=read(actor/'pool/jobs.json');assert len(jobs)==closed['native_analysis_children']==6
worker_routes={}
for job in jobs:
 w=read(Path(job['job'])/'completion.json');assert w['passed'] and w['candidate_full_STA_passed'] and w['native_transaction_succeeded']
 assert all(sha(f)==h for f,h in w['artifact_sha256'].items())
 native=Path(w['native_directory']);route=native/'candidate/routed.route'
 assert (native/'candidate/native_state_gate.txt').read_text()=='candidate FULL fresh_STA actual_installed_trees\n'
 assert (native/'candidate_restored/native_state_gate.txt').read_text()=='restored_source FULL fresh_STA actual_installed_trees\n'
 for name in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:assert sha(native/name)==sha(native/'candidate_restored'/name)
 worker_routes[sha(route)]=native/'candidate/native_sta_frontier.jsonl'
added=[byid[i] for i in c['added']];assert len(added)==6 and len(worker_routes)==6
assert {r['route_sha256'] for r in added}==set(worker_routes)
expected={};rejected=0
for attempt in read(actor/'attempts.json'):
 for item in attempt['pair'].values():
  if item.get('evaluation') and Path(item['evaluation']).is_relative_to(actor):
   expected[item['evaluation']]=(attempt,item)
assert set(expected)=={r['state'] for r in added}
for r in added:
 state=Path(r['state']);a,item=expected[str(state)];v=read(state/'endpoint_vector.json');raw=load(worker_routes[r['route_sha256']]);raw['endpoint_ids']=[list(e) for e in raw['endpoint_ids']]
 assert all(v[k]==raw[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
 assert require_publication_proof(state)['passed']
 assert sha(run_dir(state)/'routed.route')==r['route_sha256']
 before=read(Path(a['current_state'])/'endpoint_vector.json');br=resource_assurance(a['current_state'])['resource_axes'];ar=resource_assurance(state)['resource_axes']
 decision=decide('resources_under_timing',before,v,br,ar,cpd_limit_s=reg['anchor']['CPD_s'],resource_limits=reg['anchor']['resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
 assert decision==item['decision']==r['acceptance'];assert decision['accepted']==r['transition_committed']
 assert {k:r[k] for k in ar}==ar
 assert r['complete_single_configuration_seconds'] is None and r['timing_cohort'] is None
 assert (r['complete_recovery_segment_seconds'] is not None)==r['actor_final_selected']
 rejected+=not decision['accepted']
assert rejected==3 and sum(r['actor_final_selected'] for r in added)==1
assert c['complete_measured_configurations_total']==24
write(out,dict(passed=True,records=574,new_actual_states=6,new_actual_native_workers=6,legal_rejected_candidates=3,parent_non_derived_fields_exact=True,actual_raw_candidate_FULL_STA_vectors_exact=True,fixed_root_decisions_reproduced=True,historical_whole_time_unknown=True,complete_measured_configurations_total=24,native_calls_new=0,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),archive/'completion.json',actor/'completion.json',actor/'pool/jobs.json',actor/'attempts.json']}))
print(dict(passed=True,records=574,added=6,rejected=3,whole_cost_not_invented=True,native_calls_new=0),flush=True)
