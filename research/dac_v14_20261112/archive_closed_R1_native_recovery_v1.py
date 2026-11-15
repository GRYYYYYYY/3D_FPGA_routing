"""Append R1 recovery observations and reference an already archived terminal checkpoint."""
import copy,csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from state_resource_assurance import require_publication_proof
from run_native_scope_policy_v4 import run_dir
from pareto_archive_dimensions import annotate

parent=D/'multiobjective_R1_joint_owner_escape_01';actor=D/'native_checkpoint_recovery_03/bnn_R1_native'
out=D/'multiobjective_closed_R1_native_01';assert not out.exists()
pc=read(parent/'completion.json');closed=read(actor/'completion.json');assert pc['passed'] and closed['passed']
assert closed['operator_stop']=='no_admissible_move_in_registered_current_rank_windows'
assert closed['complete_single_configuration_algorithm_seconds'] is None
files=[Path(__file__).resolve(),D/'pareto_archive_dimensions.py',parent/'completion.json',parent/'points.json',actor/'completion.json',actor/'registration.json',actor/'attempts.json',actor/'steps.json',actor/'pool/jobs.json']
for n in ['pool/completion.json','evaluation_context/input_seal.json','evaluation_context/completion.json']:
 p=actor/n;x=read(p);assert x['passed'] and all(sha(f)==h for f,h in x['source_sha256'].items());files.append(p)
assert all(sha(f)==h for f,h in closed['source_sha256'].items())
assert all(sha(parent/n)==h for n,h in pc['artifact_sha256'].items())
points=read(parent/'points.json');origin=next(p for p in points if p['id']=='native_extra_opportunity_bnn_01/runs/R1')
added=[];events=[]
for attempt in read(actor/'attempts.json'):
 for role,item in attempt['pair'].items():
  if item['status']!='legal_evaluated':continue
  state=Path(item['evaluation'])
  if not state.is_relative_to(actor):continue  # already archived historical sealed LOADs remain unchanged
  rd=run_dir(state);done=read(state/'completion.json');assert done['passed']
  sealpath=Path(done['requires_final_input_seal']);assert sealpath.is_relative_to(actor)
  context=sealpath.parent
  seal=read(sealpath);assert seal['passed'] and all(sha(f)==h for f,h in seal['source_sha256'].items())
  poolpath=Path(seal['pool_completion']);poolseal=read(poolpath);assert poolseal['passed']
  assert sha(poolpath)==seal['pool_completion_sha256']
  assert all(sha(f)==h for f,h in poolseal['source_sha256'].items())
  assert read(context/'completion.json')['passed']
  files += [sealpath,context/'completion.json',poolpath]
  assurance=require_publication_proof(state);m=read(rd/'manifest.json');cmd=m['command'];v=read(state/'endpoint_vector.json')
  assert m['metrics']['native_full_check_passed'] and done['consumed_already_executed_worker_receipt']
  assert all(sha(rd/n)==m['outputs'][n]['sha256'] for n in ['packed.net','placed.place','routed.route'])
  actual=dict(architecture=sha(cmd[1]),graph=sha(cmd[cmd.index('--read_rr_graph')+1]),netlist=sha(cmd[2]),packed=sha(rd/'packed.net'),placed=sha(rd/'placed.place'),clock_modeling=cmd[cmd.index('--clock_modeling')+1],sdc='native_generated_default_from_bound_netlist',seed=cmd[cmd.index('--seed')+1])
  assert actual==origin['physical_identity'] and '--sdc_file' not in cmd
  metrics=assurance['physical_metrics'];ident=str(rd.relative_to(D));assert all(p['id']!=ident for p in points)
  row={k:copy.deepcopy(origin[k]) for k in ['circuit','physical_identity','quality_cohort','initial_routing_convergence']}
  final=str(state)==closed['final_state'];committed=attempt.get('committed_evaluation')==str(state)
  row.update(id=ident,arm='R1_native_recovery_final' if final else 'R1_native_recovery_candidate',batch='native_checkpoint_recovery_03',batch_full_path=str(actor),state=str(state),source_state=attempt['current_state'],status='legal',record_kind='sealed_recovery_final' if final else 'sealed_recovery_candidate',actor_final_selected=final,actor_terminal_claim=final,transition_committed=committed,committed_to_historical_actor=False,phase='resources',run_manifest=str(rd/'manifest.json'),binary_sha256=sha(cmd[0]),final_STA_binary_sha256=sha(cmd[0]),route_sha256=sha(rd/'routed.route'),route_body_sha256=route_body(rd/'routed.route'),command=cmd,environment=m.get('environment'),CPD_ns=v['cpd_s']*1e9,CPD_interval_ns=[v['cpd_s']*1e9]*2,CPD_precision='Actual installed-candidate FULL and fresh native STA export',wirelength=metrics['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=metrics['sb_pairs_used'],CB_sources=metrics['cb_crossing_output_sources_used'],SB_net_occupancy=metrics['sb_pair_net_occupancy'],CB_net_occupancy=metrics['cb_crossing_output_source_net_occupancy'],convergence='registered_current_rank_windows_exhausted' if final else 'legal_candidate_of_closed_recovery_menu',opportunity='Own-current native K8 repair, original R1 root anchor/seed/rank3 and acceptance unchanged. Historical four-step prefix reused. Completed rank1 worker receives a separate read-only replay context/independent physical audit; rank2 is one new native worker. All state-specific declared seals must pass. Menu closure is not global optimality.',complete_single_configuration_seconds=None,timing_cohort=None,new_native_calls_for_archival=0,audit_provenance=assurance['evidence'],resource_assurance_kind=assurance['assurance_kind'],acceptance=item['decision'],source_constraints_sha256=v['constraints_sha256'],verification=str(actor/'completion.json'),complete_recovery_segment_seconds=closed['complete_recovery_segment_seconds'] if final else None,historical_whole_workflow_seconds=None,original_interrupted_pool_seal_fabricated=False,unknowns=['Original interrupted whole-workflow time remains unknown. Recovery segment is not complete configuration cost.','Historical prefixes and repeated observations are not independent benchmark samples.'])
  assert {k:row[k] for k in ['wirelength','SB_pairs','CB_sources']}==item['resources']
  points.append(row);added.append(ident);events.append(dict(id=ident,state=str(state),round=attempt['round'],rank=attempt['candidate_rank'],role=role,accepted=item['accepted'],actor_final_selected=final,transition_committed=committed))
  files += [state/'completion.json',state/'endpoint_vector.json',state/'registration.json',rd/'manifest.json',rd/'routed.route',rd/'independent_audit.json',rd/'native_sta_frontier.jsonl',rd/'native_sta_frontier.jsonl.constraints.echo']
assert len(added)==2 and sum(e['actor_final_selected'] for e in events)==0
terminal=[row for row in points if row.get('state')==closed['final_state']]
assert len(terminal)==1 and terminal[0]['id'] not in added
assert {k:terminal[0][k] for k in ['wirelength','SB_pairs','CB_sources']}==closed['final_resources']
terminal_event=dict(state=closed['final_state'],existing_record_id=terminal[0]['id'],new_observation=False,
    accepted_steps=closed['accepted_steps'],attempted_scopes=closed['attempted_scopes'],
    complete_recovery_segment_seconds=closed['complete_recovery_segment_seconds'],
    historical_whole_workflow_seconds=None,actual_actor_closed=True)
annotate(points);out.mkdir();write(out/'points.json',points);write(out/'events.json',events)
write(out/'R1_native_closure_summary.json',dict(passed=True,actor=str(actor),actual_final={k:closed[k] for k in ['final_state','accepted_steps','attempted_scopes','final_CPD_s','final_resources','native_analysis_children','complete_recovery_segment_seconds']},new_actual_states=events,terminal_event=terminal_event,qualification='Two actual newly materialized legal rejected candidate states, one completed historical fused worker and one new native worker, archived without re-executing native. Terminal closure references the already archived checkpoint, without cloning it into a fictitious new observation. Historical sealed initial/pending observations already archived remain as their original records. The actor menu closed; historical whole time is unknown. No increase in complete configuration count.'))
fields=['id','arm','circuit','CPD_ns','wirelength','SB_pairs','CB_sources','quality_status','record_kind','actor_final_selected','complete_single_configuration_seconds']
with (out/'points.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r.get(k) for k in fields} for r in points)
write(out/'completion.json',dict(passed=True,records=len(points),parent=str(parent),added=added,native_calls=0,complete_measured_configurations_total=pc['complete_measured_configurations_total'],complete_known_circuits=pc['complete_known_circuits'],complete_vertical_families=pc['complete_vertical_families'],source_sha256={str(f):sha(f) for f in dict.fromkeys(files)},artifact_sha256={n:sha(out/n) for n in ['points.json','points.csv','events.json','R1_native_closure_summary.json']}))
print(dict(passed=True,records=len(points),added=len(added),complete_configurations=pc['complete_measured_configurations_total']),flush=True)
