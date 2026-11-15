"""Preserve three real partial-owner observations, without assigning shared cost per role."""
import copy,csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof
from pareto_archive_dimensions import annotate

parent=D/'multiobjective_additional_circuits_01';case=D/'partial_escape_owner_intervention_01';out=D/'multiobjective_partial_owner_01';assert not out.exists()
pc=read(parent/'completion.json');v=read(case/'verification.json');assert pc['passed'] and v['passed'] and v['cohort']==dict(registered_roles=3,legal_native_observations=3,failed_or_rolled_back_roles=0)
assert all(sha(parent/f)==h for f,h in pc['artifact_sha256'].items());assert all(sha(f)==h for f,h in v['source_sha256'].items())
points=read(parent/'points.json');original=copy.deepcopy(points);origin=next(p for p in points if p['id']=='native_extra_opportunity_bnn_01/runs/R1');reg=read(case/'transaction/registration.json');source=next(iter(reg['roles'].values()))['state']
files=[Path(__file__).resolve(),D/'pareto_archive_dimensions.py',parent/'completion.json',parent/'points.json',case/'verification.json',case/'transaction/registration.json',D/'R1_BFS_native_timing_prediction_01/analysis/completion.json'];added=[]
for name,item in v['outcomes'].items():
 assert item['status']=='legal_evaluated' and item['policy_accepted']
 state=Path(item['evaluation']);done=read(state/'completion.json');assert done['passed'];assurance=require_publication_proof(state);rd=run_dir(state);m=read(rd/'manifest.json');cmd=m['command'];vector=read(state/'endpoint_vector.json')
 assert m['metrics']['native_full_check_passed'] and all(sha(rd/n)==m['outputs'][n]['sha256'] for n in ['packed.net','placed.place','routed.route'])
 assert all(vector[k]==read(Path(source)/'endpoint_vector.json')[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
 identity=dict(architecture=sha(cmd[1]),graph=sha(cmd[cmd.index('--read_rr_graph')+1]),netlist=sha(cmd[2]),packed=sha(rd/'packed.net'),placed=sha(rd/'placed.place'),clock_modeling=cmd[cmd.index('--clock_modeling')+1],sdc='native_generated_default_from_bound_netlist',seed=cmd[cmd.index('--seed')+1]);assert identity==origin['physical_identity']
 assert item['resources']==dict(wirelength=2070657,SB_pairs=32,CB_sources=5071)
 ident=str(rd.relative_to(D));assert not any(p['id']==ident for p in points)
 row={k:copy.deepcopy(origin[k]) for k in ['circuit','physical_identity','quality_cohort','initial_routing_convergence']}
 row.update(id=ident,arm='R1_partial_owner_'+name,batch='partial_escape_owner_intervention_01',batch_full_path=str(case),state=str(state),source_state=source,status='legal',record_kind='partial_owner_scope_or_constructive_candidate',actor_final_selected=False,actor_terminal_claim=False,transition_committed=False,policy_accepted=True,committed_to_historical_actor=False,phase='resources',run_manifest=str(rd/'manifest.json'),binary_sha256=sha(cmd[0]),final_STA_binary_sha256=sha(cmd[0]),route_sha256=sha(rd/'routed.route'),route_body_sha256=route_body(rd/'routed.route'),command=cmd,environment=m.get('environment'),CPD_ns=vector['cpd_s']*1e9,CPD_interval_ns=[vector['cpd_s']*1e9]*2,CPD_precision='Own successful native FULL/freshSTA endpoint vector',wirelength=2070657,SB_pairs=32,CB_sources=5071,SB_net_occupancy=assurance['physical_metrics']['sb_pair_net_occupancy'],CB_net_occupancy=assurance['physical_metrics']['cb_crossing_output_source_net_occupancy'],convergence='one_registered_partial_owner_scope',opportunity='Two selected connections preserve the other target branches. Matched native/retained-CB controls use one private binary; deterministic BFS construction uses a different explicit Census LOAD. No one-factor construction/domain or equal-work timing claim.',complete_single_configuration_seconds=None,timing_cohort=None,new_native_calls_for_archival=0,audit_provenance=assurance['evidence'],resource_assurance_kind=assurance['assurance_kind'],acceptance=item['original_envelope_decision'],source_constraints_sha256=vector['constraints_sha256'],verification=str(case/'verification.json'),unknowns=['Shared three-role imported execution is not per-arm or whole configuration time.','Already verified five-connection point has4fewerwire at the same CPD/SB/CB; preserve this dominated scope alternative.'])
 points.append(row);added.append(ident);files += [state/'completion.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'routed.route',rd/'independent_audit.json']
annotate(points);assert len(points)==592
assert all(p['quality_status']=='dominated' for p in points if p['id'] in added)
out.mkdir();write(out/'points.json',points);write(out/'partial_owner_summary.json',dict(passed=True,registered_roles=3,legal_observations=3,source=source,added=added,original_actor_unchanged=True,shared_imported_execution_seconds=v['complete_shared_imported_execution_seconds'],offline_construction_seconds=v['offline_candidate_construction_seconds'],quality=dict(CPD_ns=13.421610489672275,wirelength=2070657,SB_pairs=32,CB_sources=5071),five_connection_point_saves_wire=4,complete_single_configuration_seconds=None))
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','record_kind','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r.get(k) for k in fields} for r in points)
write(out/'completion.json',dict(passed=True,records=len(points),parent=str(parent),added=added,native_calls=0,complete_measured_configurations_total=pc['complete_measured_configurations_total'],complete_known_circuits=pc['complete_known_circuits'],complete_vertical_families=pc['complete_vertical_families'],source_sha256={str(f):sha(f) for f in dict.fromkeys(files)},artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','partial_owner_summary.json']}))
keys={'quality_dominated_by','nominal_quality_dominated_by','matched_time_dominated_by','quality_projection_retained','quality_status','candidate_retention','archive_retained','record_preserved','five_dimensional_comparison_count','retention_qualification'};byid={p['id']:p for p in points}
assert all({k:v for k,v in p.items() if k not in keys}=={k:v for k,v in byid[p['id']].items() if k not in keys} for p in original)
write(out/'verification.json',dict(passed=True,records=592,added=3,parent_non_derived_fields_exact=True,actual_full_vectors_exact_to_source=True,all_candidates_native_FULL_STA_and_independently_audited=True,dominated_legal_candidates_preserved=True,only_existing_actual_final_states_carry_whole_cost=True,complete_measured_configurations_total=26,source_sha256={str(f):sha(f) for f in [out/'completion.json',case/'verification.json',Path(__file__).resolve()]},native_calls_new=0))
print(dict(passed=True,records=592,added=3,dominated=True,native_calls_new=0),flush=True)
