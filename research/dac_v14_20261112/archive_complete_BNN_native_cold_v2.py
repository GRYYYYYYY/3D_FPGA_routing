"""Archive all actual sealed states of one complete measured native BNN case."""
import copy,csv,collections
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from state_resource_assurance import require_publication_proof,resource_assurance
from run_native_scope_policy_v4 import run_dir
from pareto_archive_dimensions import annotate

parent=D/'multiobjective_revalidated_native_checkpoints_01';out=D/'multiobjective_complete_BNN_native_cold_01';assert not out.exists()
pc=read(parent/'completion.json');assert pc['passed'] and all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
case=D/'complete_resource_timing_full_flow_01/bnn_native';proof=read(case/'completion.json');assert proof['passed'] and proof['complete_configuration_verified']
config=read(case/'config.json');flow=case/'flow';done=read(flow/'completion.json')
points=read(parent/'points.json');origin=next(p for p in points if p['id']=='native_extra_opportunity_bnn_01/runs/A0')
files=[Path(__file__).resolve(),parent/'completion.json',parent/'points.json',case/'completion.json',case/'config.json',case/'measurement/completion.json',
 flow/'completion.json',flow/'resource_flow/repair/attempts.json',flow/'timing/attempts.json',D/'complete_BNN_native_cost_analysis_01/completion.json',D/'pareto_archive_dimensions.py']
hashed={}
def checked(path):
 path=str(Path(path).resolve())
 if path not in hashed:hashed[path]=sha(path)
 return hashed[path]
assert all(checked(p)==h for p,h in proof['source_sha256'].items())
entries=[dict(state=proof['initial_state'],phase='fresh_initial',source_state=None,committed=False,acceptance=None)]
for attempt in read(flow/'resource_flow/repair/attempts.json'):
 tx=Path(attempt['transaction']);progress=read(tx/'progress.json')
 for name,row in progress.items():
  if row['status']!='legal_evaluated':continue
  assert (attempt.get('committed_evaluation')==row['evaluation'])==(attempt.get('accepted_role')==name)
  entries.append(dict(state=row['evaluation'],phase='resource',source_state=attempt['current_state'],
   committed=attempt.get('committed_evaluation')==row['evaluation'],acceptance=read(tx/(name+'_decisions.json'))))
entries.append(dict(state=done['timing_initial_state'],phase='handoff_LOAD',source_state=proof['resource_final_state'],committed=False,acceptance=None))
for attempt in read(flow/'timing/attempts.json'):
 if attempt.get('evaluation'):
  entries.append(dict(state=attempt['evaluation'],phase='timing',source_state=attempt['before_state'],committed=attempt['accepted'],acceptance=None))
assert len(entries)==13 and len({e['state'] for e in entries})==13
added=[];summary=[]
for entry in entries:
 state=Path(entry['state']);closed=read(state/'completion.json');assert closed['passed']
 assurance=require_publication_proof(state);rd=run_dir(state);m=read(rd/'manifest.json');cmd=m['command']
 assert m['metrics']['native_full_check_passed']
 for name in ['packed.net','placed.place','routed.route']:assert checked(rd/name)==m['outputs'][name]['sha256']
 identity=dict(architecture=checked(cmd[1]),graph=checked(cmd[cmd.index('--read_rr_graph')+1]),netlist=checked(cmd[2]),
 packed=checked(rd/'packed.net'),placed=checked(rd/'placed.place'),clock_modeling=cmd[cmd.index('--clock_modeling')+1],
 sdc='native_generated_default_from_bound_netlist',seed=cmd[cmd.index('--seed')+1])
 assert identity==origin['physical_identity'] and '--sdc_file' not in cmd
 if (state/'input_seal.json').exists():assert read(state/'input_seal.json')['passed'];files.append(state/'input_seal.json')
 metrics=resource_assurance(state)['physical_metrics'];vector=read(state/'endpoint_vector.json')
 final=str(state)==proof['final_state'];ident=str(rd.relative_to(D));assert not any(p['id']==ident for p in points)
 row={key:copy.deepcopy(origin[key]) for key in ['circuit','physical_identity','quality_cohort','initial_routing_convergence']}
 row.update(id=ident,arm='cold_full_native_resource_then_current_STA' if final else 'cold_native_'+entry['phase']+'_observation',
  batch='complete_resource_timing_full_flow_01',batch_full_path=str(case),state=str(state),source_state=entry['source_state'],
  status='legal',record_kind='measured_whole_configuration_final' if final else 'sealed_intermediate_of_measured_whole_configuration',
  actor_final_selected=final,actor_terminal_claim=final,phase=entry['phase'],transition_committed=entry['committed'],
  committed_to_historical_actor=False,run_manifest=str(rd/'manifest.json'),binary_sha256=checked(cmd[0]),final_STA_binary_sha256=checked(cmd[0]),
  phase_binary_sha256=config['phase_binary_sha256'],route_sha256=checked(rd/'routed.route'),route_body_sha256=route_body(rd/'routed.route'),
  command=cmd,environment=m.get('environment'),CPD_ns=vector['cpd_s']*1e9,CPD_interval_ns=[vector['cpd_s']*1e9]*2,
  CPD_precision='Actual native endpoint vector from this complete cold case',wirelength=metrics['planar_wirelength_excluding_sb_half_nodes'],
  SB_pairs=metrics['sb_pairs_used'],CB_sources=metrics['cb_crossing_output_sources_used'],SB_net_occupancy=metrics['sb_pair_net_occupancy'],
  CB_net_occupancy=metrics['cb_crossing_output_source_net_occupancy'],convergence='fresh_count8_complete_own_current_resource_then_current_STA_menu' if final else 'intermediate_actual_stage_of_fresh_count8_full_case',
  opportunity='Fresh actual count8/1.01/seed11 root, same explicit inputs; resource8scopes/5commits then current-STA3proposals/3commits. No external route/candidate/query history. Domain partner still pending.',
  complete_single_configuration_seconds=proof['complete_wall_seconds'] if final else None,
  timing_cohort='complete_fresh_BNN_resource_timing_pair_01' if final else None,
  complete_configuration_verification=str(case/'completion.json'),actual_whole_configuration_terminal=final,
  complete_configuration_measurement=str(case/'measurement/completion.json') if final else None,
  memory_observation={key:proof[key] for key in ['waited_process_RSS_high_water_kib','sampled_tree_RSS_peak_kib','sampled_tree_PSS_peak_kib','missing_memory_observations','observer_CPU_seconds']} if final else None,
  new_native_calls_for_archival=0,audit_provenance=str(rd/'independent_audit.json'),resource_assurance_kind=assurance['assurance_kind'],
  acceptance=entry['acceptance'],source_constraints_sha256=vector['constraints_sha256'],verification=str(case/'completion.json'),
  unknowns=['Matched cold domain case pending; shared-host/OS-cache effects uncontrolled. No historical quality/time splice.'] if final else ['Intermediate state has no standalone whole-configuration runtime.'])
 if final:assert {k:row[k] for k in ['wirelength','SB_pairs','CB_sources']}==proof['resources'] and row['CPD_ns']==proof['CPD_ns']
 points.append(row);added.append(ident)
 summary.append(dict(id=ident,state=str(state),phase=entry['phase'],actor_final_selected=final,transition_committed=entry['committed'],
 CPD_ns=row['CPD_ns'],resources={k:row[k] for k in ['wirelength','SB_pairs','CB_sources']},complete_single_configuration_seconds=row['complete_single_configuration_seconds']))
 files.extend([state/'completion.json',state/'endpoint_vector.json',rd/'manifest.json',rd/'routed.route',rd/'independent_audit.json'])
annotate(points)
for item in summary:item['quality_status']=next(p['quality_status'] for p in points if p['id']==item['id'])
final=next(p for p in points if p['id']==added[-1]);assert final['quality_status']=='dominated'
old=next(p for p in points if p['arm']=='complete_resource_native_then_current_STA_native')
assert old['id'] in final['quality_dominated_by'] and old['complete_single_configuration_seconds'] is None
assert final['wirelength']-old['wirelength']==4 and final['CPD_ns']==old['CPD_ns']
out.mkdir();write(out/'points.json',points)
write(out/'complete_native_case_summary.json',dict(passed=True,observations=summary,complete_case=proof,
 registered_pair_roles=2,completed_pair_roles=1,complete_native_workflow_actual_resources=proof['resources'],
 old_imported_native_minus_cold_wire=-4,old_imported_native_has_unknown_complete_cost=True,
 qualification='Thirteen actual observations from one complete sealed cold native case; only actual final carries7933.245508622378s whole command and its memory. Older imported native point has4less wire at same CPD/SB/CB and quality-dominates this actual final, but its complete cost remains unknown. All intermediate/handoff/root observations and legal rejects retained without borrowing whole cost. Same historical physical root is not a new independent benchmark. Domain full case remains pending; registered pair denominator2, no paired speedup or new domain effect.'))
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','record_kind','actor_final_selected','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:p.get(k) for k in fields} for p in points)
write(out/'completion.json',dict(passed=True,records=len(points),parent=str(parent),added=added,native_calls=0,
 complete_measured_configurations_total=23,complete_known_circuits=4,complete_vertical_families=3,
 source_sha256={str(p):checked(p) for p in files},artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','complete_native_case_summary.json']}))
print(dict(passed=True,records=len(points),added=len(added),final=summary[-1]),flush=True)
