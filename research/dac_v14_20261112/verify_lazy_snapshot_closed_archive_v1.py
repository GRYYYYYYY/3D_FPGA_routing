"""Reconstruct actual combined snapshot/lazy observations and bind their own measured costs."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from state_resource_assurance import require_publication_proof
from run_native_scope_policy_v4 import run_dir
from complete_flow_equivalence_v1 import equal_state

archive=D/'multiobjective_lazy_snapshot_closed_01';out=archive/'verification.json';assert not out.exists()
c=read(archive/'completion.json');assert c['passed'];assert all(sha(archive/f)==h for f,h in c['artifact_sha256'].items());assert all(sha(f)==h for f,h in c['source_sha256'].items())
points=read(archive/'points.json');parent=read(Path(c['parent'])/'points.json');byid={p['id']:p for p in points};assert len(byid)==len(points)==645
keys={'quality_dominated_by','nominal_quality_dominated_by','matched_time_dominated_by','quality_projection_retained','quality_status','candidate_retention','archive_retained','record_preserved','five_dimensional_comparison_count','retention_qualification'}
for p in parent:assert {k:v for k,v in p.items() if k not in keys}=={k:v for k,v in byid[p['id']].items() if k not in keys}
added=[byid[i] for i in c['added']];assert len(added)==5 and {p['circuit'] for p in added}=={'eltwise_layer','softmax'}
cohort=D/'complete_serial_lazy_source_snapshot_01';report=read(cohort/'comparison.json');assert report['passed'] and report['registered_roles']==2 and report['successful_legal_roles']==2
expected={};finals=[]
for label in ['eltwise_domain','softmax_domain']:
 case=cohort/label;proof=read(case/'explicit_policy_verification.json');assert proof['passed'] and proof['complete_configuration_verified']
 expected[proof['initial_state']]=case
 for attempt in read(case/'flow/repair/attempts.json'):
  for result in read(Path(attempt['transaction'])/'progress.json').values():
   if result['status']=='legal_evaluated':expected[result['evaluation']]=case
 final=next(p for p in added if p['state']==proof['final_state']);finals.append(final)
 assert final['actor_final_selected'] and final['complete_single_configuration_seconds']==proof['complete_wall_seconds']
 assert final['complete_single_configuration_seconds']==read(case/'measurement/completion.json')['complete_command_wall_seconds']
 assert final['measured_memory']['sampled_tree_PSS_peak_kib']==proof['sampled_tree_PSS_peak_kib']
assert set(expected)=={p['state'] for p in added}
for p in added:
 state=Path(p['state']);run=run_dir(state);assert require_publication_proof(state)['passed']
 assert sha(run/'routed.route')==p['route_sha256']
 v=read(state/'endpoint_vector.json');assert v['cpd_s']*1e9==p['CPD_ns']
 axes=require_publication_proof(state)['resource_axes'];assert all(p[k]==v for k,v in axes.items())
 if p not in finals:assert p['complete_single_configuration_seconds'] is None and p['measured_memory'] is None
assert len(finals)==2
assert read(archive/'failed_role_observations.json')==[]
assert all(r['equivalence']['same_complete_execution_states_and_workload'] for r in report['results'].values())
assert c['complete_measured_configurations_total']==28 and c['complete_known_circuits']==5 and c['complete_vertical_families']==3
write(out,dict(passed=True,records=645,new_observations=5,successful_legal_new_configurations=2,registered_new_roles=2,failed_new_roles=0,complete_measured_configurations_total=28,complete_known_circuits=5,complete_vertical_families=3,parent_non_derived_fields_exact=True,actual_event_set_complete=True,only_two_actual_finals_carry_complete_cost=True,failed_quality_not_archived=True,actual_execution_states_and_workload_exact_to_each_reference=True,failed_costs_preserved=True,native_calls_new=0,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),archive/'completion.json',cohort/'comparison.json',archive/'failed_role_observations.json']}))
print(dict(passed=True,records=645,legal=2,failed=0,registered=2,complete_configurations=28,native_calls_new=0),flush=True)
