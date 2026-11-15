"""Verify one real fresh-route/resource/timing output and its whole-command cost."""
import argparse
import math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from seed_census_analysis_pool_v2 import process_identity
from multiobjective_acceptance_v2 import decide
from terminal_resource_handoff_v1 import choose
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root.resolve();flow=root/'flow'
registration=read(root/'queue/registration.json');live=process_identity(registration['pid']);assert not live or live['state']=='Z' or live['start_ticks']!=registration['start_ticks']
assert all(sha(f)==h for f,h in registration['source_sha256'].items())
measure=read(root/'measurement/completion.json');done=read(flow/'completion.json');config=read(root/'config.json')
assert measure['passed'] and measure['returncode']==0 and not measure['live_descendants_after_command_exit'] and done['passed']
assert done['external_history_allowed'] is False and config['external_history_allowed'] is False
assert all(sha(f)==h for f,h in config['input_sha256'].items()) and all(sha(f)==h for f,h in done['source_sha256'].items())
assert sha(root/'config.json')==sha(done['config'])
assert [x['phase'] for x in read(flow/'stages.json')]==['fresh_route_and_complete_resource','terminal_resource_wire_selection','bind_same_run_joint_query_graph','resource_final_handoff_FULL_STA','complete_current_STA_timing']
assert all(x['status']=='completed' for x in read(flow/'stages.json'))
resource_flow=flow/'resource_flow';rdone=read(resource_flow/'completion.json');repair=resource_flow/'repair';rreg=read(repair/'registration.json');rc=read(repair/'completion.json')
assert rdone['passed'] and rc['passed'] and rc['operator_stop']=='no_admissible_candidate_in_registered_current_scope_probe'
assert all(sha(f)==h for f,h in rc['source_sha256'].items())
assert [x['phase'] for x in read(resource_flow/'stages.json')]==['joint_graph_index_generation','fresh_route_and_materialization','resource_repair']
assert all(read(resource_flow/n/'completion.json')['passed'] for n in ['graph_audit_cache','full_graph_cache'])
assert read(flow/'physical_query_graph/completion.json')['passed']
assert config['cache_mode']=='joint_build_inside_flow'
joint=resource_flow/'joint_graph_indexes';generated=read(joint/'completion.json')
assert generated['passed'] and generated['XML_traversals']==1
assert all(sha(joint/name)==digest for name,digest in generated['artifact_sha256'].items())
assert all(sha(path)==digest for path,digest in generated['source_sha256'].items())
assert generated['graph_sha256']==sha(generated['graph'])
for alias,target in [(resource_flow/'graph_audit_cache',joint/'audit_cache'),(resource_flow/'full_graph_cache',joint/'full_cache'),(flow/'physical_query_graph',joint/'query_graph')]:
 assert alias.resolve()==target.resolve() and alias.resolve().is_relative_to(flow),'No supplied index outside measured command'
assert read(joint/'audit_cache/completion.json')['complete_build_seconds'] is None
assert read(joint/'full_cache/completion.json')['complete_build_seconds'] is None
assert read(joint/'query_graph/completion.json')['export_seconds'] is None

files=[Path(__file__).resolve(),joint/'completion.json',joint/'registration.json',root/'config.json',root/'measurement/completion.json',flow/'completion.json',flow/'registration.json',flow/'stages.json',resource_flow/'completion.json',resource_flow/'stages.json',repair/'registration.json',repair/'completion.json',flow/'physical_query_graph/completion.json']
def vector(state):return read(Path(state)/'endpoint_vector.json')
def physical(state):
 s=Path(state);c=read(s/'completion.json');assert c['passed'];rd=run_dir(s);m=read(rd/'manifest.json');assert m['metrics']['native_full_check_passed'];audit=read(rd/'independent_audit.json');assert audit['audit']['passed']
 for f in ['packed.net','placed.place','routed.route']:assert sha(rd/f)==m['outputs'][f]['sha256']
 if (s/'input_seal.json').exists():assert read(s/'input_seal.json')['passed']
 files.extend([s/'completion.json',s/'endpoint_vector.json',rd/'manifest.json',rd/'independent_audit.json'])
 z=audit['physical_metrics'];return dict(wirelength=z['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=z['sb_pairs_used'],CB_sources=z['cb_crossing_output_sources_used'])
initial=Path(done['initial_state']);resource_final=Path(done['resource_final_state']);handoff=Path(done['timing_initial_state']);final=Path(done['final_state'])
assert rdone['initial_state']==str(initial) and rdone['final_state']==rc['final_state']==done['resource_policy_final_state']
assert config['terminal_resource_policy']=='endpoint_wire_before_timing'
assert config['unified_controller_version']=='development_v1' and config['final_state_policy']=='strict_timing_terminal_after_endpoint_wire_handoff'
assert rreg['owner_escalation']==config['owner_escalation']
assert rreg['owner_domain_mode']==config['owner_domain_mode']=='unrestricted_in_both_arms'
assert rreg['owner_rank_windows']==config['owner_rank_windows']==3
choice=choose(resource_flow,flow/'terminal_wire_selection')
assert choice==read(flow/'terminal_resource_handoff.json')
assert choice['selected_resource_state']==str(resource_final) and done['terminal_wire_commits']==choice['terminal_wire_commits']
files += [flow/'terminal_resource_handoff.json',flow/'terminal_wire_selection/completion.json',flow/'terminal_wire_selection/observed_candidates.json']
rootv=vector(initial);rootaxes=physical(initial)
manifest=read(run_dir(initial)/'manifest.json');cmd=manifest['command'];assert cmd[cmd.index('--router_max_convergence_count')+1]=='8' and cmd[cmd.index('--router_reconvergence_cpd_threshold')+1]=='1.01'
assert cmd[cmd.index('--seed')+1]==config['route_command'][config['route_command'].index('--seed')+1] and manifest['environment']['VPR_H3D_MODE']=='off'
assert sha(cmd[0])==config['phase_binary_sha256']['route_and_resource']
assert rreg['anchor']['CPD_s']==rootv['cpd_s'] and rreg['resource_limits']['wirelength']==(rootaxes['wirelength']*1001+999)//1000
resource_counts=dict(scopes=0,native_transactions=0,skipped_OFF=0,legal_candidates=0,rolled_back_candidates=0)
for attempt in read(repair/'attempts.json'):
 assert attempt['native_transaction_complete'];tx=Path(attempt['transaction']);closed=read(tx/'completion.json');assert closed['passed'];assert all(sha(f)==h for f,h in closed['source_sha256'].items());resource_counts['scopes']+=1
 roles=read(tx/'registration.json')['roles'];progress=read(tx/'progress.json')
 for name,row in progress.items():
  role=roles[name];assert role['original_budget']['CPD_s']==rootv['cpd_s'] and role['fixed_resource_limits']==rreg['resource_limits']
  if row['status']=='not_executed_domain_candidate_accepted':
   assert name=='reuse_off' and progress['reuse_on']['policies']['resources_under_timing']['accepted'];assert not (tx/name).exists() and row['acceptance_evaluated'] is False;resource_counts['skipped_OFF']+=1;continue
  worker=tx/name;wc=read(worker/'completion.json');assert wc['passed'];wm=read(run_dir(worker)/'manifest.json');assert sha(wm['command'][0])==config['phase_binary_sha256']['owner_coordination' if attempt.get('mechanism')=='capacity_certified_owner_coordination' else 'route_and_resource'];resource_counts['native_transactions']+=1
  source=Path(role['state']);assert all(vector(source)[k]==vector(worker)[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
  if row['status']=='transaction_failed_rolled_back':resource_counts['rolled_back_candidates']+=1;continue
  assert row['status']=='legal_evaluated' and not row['native_reused'];state=Path(row['evaluation']);r=physical(state)
  decision=decide('resources_under_timing',vector(source),vector(state),physical(source),r,cpd_limit_s=rootv['cpd_s'],resource_limits=rreg['resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
  assert decision==read(tx/(name+'_decisions.json'))['resources_under_timing'];assert sha(read(run_dir(state)/'manifest.json')['command'][0])==config['phase_binary_sha256']['owner_coordination' if attempt.get('mechanism')=='capacity_certified_owner_coordination' else 'route_and_resource'];resource_counts['legal_candidates']+=1
 if attempt.get('mechanism')=='capacity_certified_owner_coordination':
  preg=read(tx/'registration.json');prep=read(tx/'preparation.json')
  assert prep['passed'] and prep['transaction_registered'] and prep['registration_sha256']==sha(tx/'registration.json')
  assert set(roles)=={'joint_native'} and not roles['joint_native']['crossing_reuse_enabled']
  assert Path(preg['root_state'])==initial and preg['resource_conditions']['anchor']==rreg['anchor']
  assert Path(preg['owner_selection']).resolve().is_relative_to(repair)
  sel=read(Path(preg['owner_selection'])/'completion.json');assert sel['passed'] and Path(sel['state'])==Path(attempt['current_state'])
  assert all(sha(f)==h for f,h in prep['source_sha256'].items())
  files += [tx/'preparation.json',Path(preg['owner_selection'])/'completion.json']
 files.extend([tx/'completion.json',tx/'registration.json',tx/'progress.json'])
assert physical(resource_final)==physical(handoff) and all(vector(resource_final)[k]==vector(handoff)[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
assert route_body(run_dir(resource_final)/'routed.route')==route_body(run_dir(handoff)/'routed.route')
assert sha(read(run_dir(handoff)/'manifest.json')['command'][0])==config['phase_binary_sha256']['route_and_resource']
limits=read(flow/'absolute_timing_limits.json');expected=dict(wirelength=rreg['resource_limits']['wirelength'],SB_pairs=physical(resource_final)['SB_pairs'],CB_sources=physical(resource_final)['CB_sources']);assert limits==expected==done['absolute_timing_limits']
timing=flow/'timing';tc=read(timing/'completion.json');tr=read(timing/'registration.json');assert tc['passed'] and tc['operator_stop']=='no_admissible_candidate_in_current_portfolio';assert all(sha(f)==h for f,h in tc['source_sha256'].items())
assert tr['fixed_absolute_limits']==limits and tr['policy']=='timing_under_resources' and tr['fraction']==.9 and tr['initial_state']==str(handoff)
assert tc['final_state']==str(final) and done['final_resources']==physical(final) and done['final_CPD_s']==vector(final)['cpd_s']
for attempt in read(timing/'attempts.json'):
 if not attempt.get('evaluation'):assert not attempt['accepted'];continue
 state=Path(attempt['evaluation']);before=Path(attempt['before_state']);r=physical(state)
 decision=decide('timing_under_resources',vector(before),vector(state),physical(before),r,cpd_limit_s=vector(handoff)['cpd_s'],resource_limits=limits,native_valid=True,transaction_complete=True,resource_objectives=('wirelength',))
 assert decision['accepted']==attempt['policy_accepted']
 assert attempt['accepted']==bool(decision['accepted'] and not attempt['already_visited'])
 assert state.resolve().is_relative_to(flow)
 sta_binary=sha(read(run_dir(state)/'manifest.json')['command'][0])
 if sta_binary!=config['phase_binary_sha256']['timing_candidate_STA']:
  assert sta_binary in [config['phase_binary_sha256']['route_and_resource'],config['phase_binary_sha256']['owner_coordination']] and (state==handoff or state.resolve().is_relative_to(resource_flow)),'Only an actual own-run source/candidate may reuse its already executed FULL/STA'
 if not attempt['reused_native']:
  matching=[]
  for proposal in (timing/f"round_{attempt['round']:03d}").glob('proposal_*'):
   decision=proposal/'policy_decisions.json'
   if not decision.exists():continue
   transaction=proposal/'transaction';progress=transaction/'progress.json'
   if progress.exists() and read(progress).get('current_group',{}).get('evaluation')==str(state):matching.append(transaction/'current_group')
  assert matching,'Actual native worker missing for timing attempt'
  worker=matching[-1]
  assert worker.is_dir() and read(worker/'completion.json')['passed']
  assert sha(read(run_dir(worker)/'manifest.json')['command'][0])==config['phase_binary_sha256']['timing_native_repair']
for path in timing.rglob('reuse_receipts.json'):
 for row in read(path):
  for key in ['source','path','batch','evaluation']:
   if row.get(key) and isinstance(row[key],str) and row[key].startswith('/'):
    assert Path(row[key]).resolve().is_relative_to(timing),'Historical result escaped complete-flow boundary'
 files.append(path)
assert vector(final)['cpd_s']<=vector(handoff)['cpd_s']<=rootv['cpd_s'] and all(physical(final)[k]<=limits[k] for k in limits)
assert done['owner_commits']==rc['owner_commits']==sum(x.get('mechanism')=='capacity_certified_owner_coordination' for x in read(repair/'steps.json'))
files += [timing/'completion.json',timing/'registration.json',timing/'attempts.json',timing/'steps.json',flow/'absolute_timing_limits.json']
# Require actual metadata consumers, not merely index generation, inside flow.
assert config['endpoint_loader_strategy']=='existing_streaming_v2_all_observations'
assert config['metadata_cache_strategy']=='explicit_same_measured_flow_only'
metadata_consumers=[]
for receipt_path in flow.rglob('full_graph_cache_receipt.json'):
 receipt=read(receipt_path)
 for entry in [receipt,receipt['parent']]:
  consumed=Path(entry['cache_completion']).resolve()
  assert consumed.is_relative_to(flow),'External metadata cache consumer'
  assert consumed in [(resource_flow/'graph_audit_cache/completion.json').resolve(),(resource_flow/'full_graph_cache/completion.json').resolve()]
 metadata_consumers.append(str(receipt_path));files.append(receipt_path)
for analysis_path in timing.glob('round_*/proposal_*/transaction/*_audit/analysis.json'):
 analysis=read(analysis_path)
 if 'graph_cache' in analysis:
  consumed=Path(analysis['graph_cache']['cache_completion']).resolve()
  assert consumed==(resource_flow/'graph_audit_cache/completion.json').resolve()
  assert consumed.is_relative_to(flow),'External transaction metadata cache'
  metadata_consumers.append(str(analysis_path));files.append(analysis_path)
for costs_path in timing.glob('round_*/proposal_*/transaction/process_costs.json'):
 for row in read(costs_path):
  command=row.get('command',[])
  if '--cache' in command:assert Path(command[command.index('--cache')+1]).resolve()==(resource_flow/'graph_audit_cache').resolve()
  if '--full-graph-cache' in command:assert Path(command[command.index('--full-graph-cache')+1]).resolve()==(resource_flow/'full_graph_cache').resolve()
 files.append(costs_path)
assert metadata_consumers,'No actual metadata consumer receipts'
write(root/'metadata_consumers.json',dict(passed=True,all_within_measured_flow=True,receipts=metadata_consumers))
files.append(root/'metadata_consumers.json')
sdc_result=None
if '--sdc_file' in config['route_command']:
 sdc=Path(config['route_command'][config['route_command'].index('--sdc_file')+1]).resolve()
 assert sha(sdc)==config['input_sha256'][str(sdc)]
 for state in [initial,resource_final,handoff,final]:
  command=read(run_dir(state)/'manifest.json')['command']
  assert '--sdc_file' in command and Path(command[command.index('--sdc_file')+1]).resolve()==sdc
  echo=run_dir(state)/'native_sta_frontier.jsonl.constraints.echo'
  assert sha(echo)==vector(state)['constraints_sha256']
  files.append(echo)
 vv=vector(final)
 counts={kind:dict(negative=sum(isinstance(x,(int,float)) and x<0 for x in vv[kind].values()),nonfinite_or_unconstrained=sum(not isinstance(x,(int,float)) or not math.isfinite(x) for x in vv[kind].values()),components=len(vv[kind])) for kind in ['setup','hold']}
 sdc_result=dict(path=str(sdc),sha256=sha(sdc),clock_and_IO_spec=config['explicit_sdc_spec'],observed_final_component_counts=counts,all_observed_components_finite_and_nonnegative=all(v['negative']==v['nonfinite_or_unconstrained']==0 for v in counts.values()),qualification='Declared benchmark timing instance, not an externally supplied application requirement. Report actual native constraint echo and all observed components; no timing-closure assumption.')
 files.append(sdc)
payload=dict(passed=True,explicit_SDC_result=sdc_result,owner_commits=rc['owner_commits'],unified_controller_version=config['unified_controller_version'],complete_configuration_verified=True,terminal_resource_selection_verified=True,initial_state=str(initial),resource_final_state=str(resource_final),resource_policy_final_state=done['resource_policy_final_state'],terminal_wire_commits=choice['terminal_wire_commits'],final_state=str(final),CPD_ns=vector(final)['cpd_s']*1e9,resources=physical(final),complete_wall_seconds=measure['complete_command_wall_seconds'],resource_actual_work=resource_counts,resource_accepted_steps=rc['accepted_steps'],timing_accepted_steps=tc['accepted_steps'],timing_attempted_proposals=tc['attempted_proposals'],phase_binary_sha256=config['phase_binary_sha256'],waited_process_RSS_high_water_kib=measure['waited_process_RSS_high_water_kib'],sampled_tree_RSS_peak_kib=measure['sampled_tree_RSS_peak_kib'],sampled_tree_PSS_peak_kib=measure['sampled_tree_PSS_peak_kib'],missing_memory_observations=measure['missing_memory_observations'],observer_CPU_seconds=measure['observer_CPU_seconds'],source_sha256={str(f):sha(f) for f in files},qualification='Actual whole measured development unified count8 fresh-route/current-resource/owner/endpoint-safe terminal wire/current-STA configuration with one same-command XML traversal jointly generating all3graph payloads; shared build cost is not counted three times. Graph indexes are generated and actual metadata consumers remain inside this measured flow; existing streaming v2 validates all JSON lines and native COMPLETE/pin counts; no external route/candidate/query history. Resource and timing phase binaries are distinct and explicitly bound as parts of this single configuration. All actual legal/rejected/failed/omitted work is retained and decisions checked against immutable original envelopes; zero-commit phases are allowed only with exact actual source state retained. Timing/quality/memory belong to this same execution, not historical splices. OS cache and shared-host concurrency uncontrolled; descriptive single observation, not statistical speedup or independent held-out confirmation.')
write(root/'completion.json',payload);write(root/'queue/completion.json',dict(passed=True,source_sha256={str(root/'completion.json'):sha(root/'completion.json')}));write(root/'queue/status.json',dict(status='terminal',passed=True));print({k:payload[k] for k in ['passed','CPD_ns','resources','complete_wall_seconds']},flush=True)
