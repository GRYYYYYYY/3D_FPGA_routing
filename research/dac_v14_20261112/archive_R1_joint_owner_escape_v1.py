"""Archive matched native/domain joint candidates without assigning shared time per arm."""
import copy,csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from state_resource_assurance import require_publication_proof
from run_native_scope_policy_v4 import run_dir
from pareto_archive_dimensions import annotate

parent=D/'multiobjective_closed_Tf_native_01';case=D/'R1_owner_release_joint_probe_01';out=D/'multiobjective_R1_joint_owner_escape_01';assert not out.exists()
pc=read(parent/'completion.json');v=read(case/'verification.json');assert pc['passed'] and v['passed']
assert all(sha(parent/f)==h for f,h in pc['artifact_sha256'].items())
assert all(sha(f)==h for f,h in v['source_sha256'].items())
points=read(parent/'points.json');origin=next(p for p in points if p['id']=='native_extra_opportunity_bnn_01/runs/R1')
files=[Path(__file__).resolve(),D/'pareto_archive_dimensions.py',parent/'completion.json',parent/'points.json',parent/'verification.json',case/'verification.json',case/'transaction/registration.json',case/'transaction/completion.json',D/'R1_single_net_vertical_local_minimum_01/completion.json']
reg=read(case/'transaction/registration.json');added=[]
for name,item in v['roles'].items():
 state=Path(item['evaluation']);done=read(state/'completion.json');assert done['passed'] and item['accepted']
 assert item['resources']==dict(wirelength=2070653,SB_pairs=32,CB_sources=5071)
 assert item['endpoint_comparison']['setup_improved']==item['endpoint_comparison']['setup_regressed']==item['endpoint_comparison']['hold_violation_regressions']==0
 assert item['CPD_ns']==13.421610489672275
 assurance=require_publication_proof(state);rd=run_dir(state);m=read(rd/'manifest.json');cmd=m['command'];vector=read(state/'endpoint_vector.json')
 assert m['metrics']['native_full_check_passed']
 assert all(sha(rd/n)==m['outputs'][n]['sha256'] for n in ['packed.net','placed.place','routed.route'])
 identity=dict(architecture=sha(cmd[1]),graph=sha(cmd[cmd.index('--read_rr_graph')+1]),netlist=sha(cmd[2]),packed=sha(rd/'packed.net'),placed=sha(rd/'placed.place'),clock_modeling=cmd[cmd.index('--clock_modeling')+1],sdc='native_generated_default_from_bound_netlist',seed=cmd[cmd.index('--seed')+1]);assert identity==origin['physical_identity']
 ident=str(rd.relative_to(D));assert not any(p['id']==ident for p in points)
 metrics=assurance['physical_metrics'];source=reg['roles'][name]['state']
 row={k:copy.deepcopy(origin[k]) for k in ['circuit','physical_identity','quality_cohort','initial_routing_convergence']}
 row.update(id=ident,arm='R1_owner_escape_'+name,batch='R1_owner_release_joint_probe_01',batch_full_path=str(case),state=str(state),source_state=source,status='legal',record_kind='matched_joint_owner_scope_candidate',actor_final_selected=False,actor_terminal_claim=False,transition_committed=False,policy_accepted=True,committed_to_historical_actor=False,phase='resources',run_manifest=str(rd/'manifest.json'),binary_sha256=sha(cmd[0]),final_STA_binary_sha256=sha(cmd[0]),route_sha256=sha(rd/'routed.route'),route_body_sha256=route_body(rd/'routed.route'),command=cmd,environment=m.get('environment'),CPD_ns=vector['cpd_s']*1e9,CPD_interval_ns=[vector['cpd_s']*1e9]*2,CPD_precision='Actual independently checked candidate FULL/freshSTA vector',wirelength=metrics['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=metrics['sb_pairs_used'],CB_sources=metrics['cb_crossing_output_sources_used'],SB_net_occupancy=metrics['sb_pair_net_occupancy'],CB_net_occupancy=metrics['cb_crossing_output_source_net_occupancy'],convergence='one_prospectively_selected_five_connection_joint_scope',opportunity='Same source, selected owner+four-sink target, order/current weights/private binary/native objective/full box; only target CB-source whitelist differs. No original actor commit. Both controls reach the same actual tree, so no incremental domain benefit is inferred.',complete_single_configuration_seconds=None,timing_cohort=None,new_native_calls_for_archival=0,audit_provenance=assurance['evidence'],resource_assurance_kind=assurance['assurance_kind'],acceptance=read(case/'transaction'/(name+'_decisions.json')),source_constraints_sha256=vector['constraints_sha256'],verification=str(case/'verification.json'),native_core_seconds=item['native_core_seconds'],unknowns=['Shared imported two-arm scope time913.0741119608283s is not per-arm standalone or complete workflow time.','Both arms are one prospectively selected development scope on a known circuit, not independent samples or generic domain superiority.'])
 assert {k:row[k] for k in item['resources']}==item['resources'];points.append(row);added.append(ident)
 files += [state/'completion.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'routed.route',rd/'independent_audit.json',case/'transaction'/(name+'_decisions.json')]
assert len(added)==2
annotate(points);out.mkdir();write(out/'points.json',points)
write(out/'joint_owner_summary.json',dict(passed=True,roles=v['roles'],shared_imported_scope_seconds=v['complete_shared_imported_scope_seconds'],bound_resource_sum=5103,actual_resource_sum=5103,source_resource_sum=5104,source_wire=2070629,final_wire=2070653,wire_delta=24,committed_to_original_actor=False,qualification='Two actual matched candidates demonstrate escaping the certified single-net local minimum by changing another owner. Both native and target-CB-domain arms have the same actual route and unchanged endpoint vector; no extra domain benefit. Their aggregate vertical sum attains the same physical-input terminal lower bound. Wire/CPD optimality and full-flow cost are unproved.'))
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','record_kind','actor_final_selected','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r.get(k) for k in fields} for r in points)
write(out/'completion.json',dict(passed=True,records=len(points),parent=str(parent),added=added,native_calls=0,complete_measured_configurations_total=pc['complete_measured_configurations_total'],complete_known_circuits=pc['complete_known_circuits'],complete_vertical_families=pc['complete_vertical_families'],source_sha256={str(f):sha(f) for f in dict.fromkeys(files)},artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','joint_owner_summary.json']}))
print(dict(passed=True,records=len(points),new_quality={k:points[-1][k] for k in ['CPD_ns','wirelength','SB_pairs','CB_sources','quality_status']},native_calls_new=0),flush=True)
