"""Verify one real fresh-route/resource/timing output and its whole-command cost."""
import argparse
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from run_native_scope_policy_v4 import run_dir
from seed_census_analysis_pool_v2 import process_identity
from multiobjective_acceptance_v2 import decide
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.root.resolve();flow=root/'flow';output=a.output.resolve()
from orphaned_flow_time_evidence_v1 import recover_original_time
recovered=recover_original_time(root);output.mkdir(parents=True,exist_ok=False)
registration=read(root/'queue/registration.json');live=process_identity(registration['pid']);assert not live or live['state']=='Z' or live['start_ticks']!=registration['start_ticks']
assert all(sha(f)==h for f,h in registration['source_sha256'].items())
done=read(flow/'completion.json');config=read(root/'config.json')
assert recovered['exit_status']==0 and done['passed']
assert done['complete_driver_seconds']<=recovered['elapsed_seconds']+.1
assert done['external_history_allowed'] is False and config['external_history_allowed'] is False
assert all(sha(f)==h for f,h in config['input_sha256'].items()) and all(sha(f)==h for f,h in done['source_sha256'].items())
assert sha(root/'config.json')==sha(done['config'])
assert [x['phase'] for x in read(flow/'stages.json')]==['fresh_route_and_complete_resource','bind_same_run_joint_query_graph','resource_final_handoff_FULL_STA','complete_current_STA_timing']
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

files=[Path(__file__).resolve(),joint/'completion.json',joint/'registration.json',root/'config.json',root/'measurement/gnu_time.txt',flow/'completion.json',flow/'registration.json',flow/'stages.json',resource_flow/'completion.json',resource_flow/'stages.json',repair/'registration.json',repair/'completion.json',flow/'physical_query_graph/completion.json']
def vector(state):return read(Path(state)/'endpoint_vector.json')
def physical(state):
 s=Path(state);c=read(s/'completion.json');assert c['passed'];rd=run_dir(s);m=read(rd/'manifest.json');assert m['metrics']['native_full_check_passed'];audit=read(rd/'independent_audit.json');assert audit['audit']['passed']
 for f in ['packed.net','placed.place','routed.route']:assert sha(rd/f)==m['outputs'][f]['sha256']
 if (s/'input_seal.json').exists():assert read(s/'input_seal.json')['passed']
 files.extend([s/'completion.json',s/'endpoint_vector.json',rd/'manifest.json',rd/'independent_audit.json'])
 z=audit['physical_metrics'];return dict(wirelength=z['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=z['sb_pairs_used'],CB_sources=z['cb_crossing_output_sources_used'])
initial=Path(done['initial_state']);resource_final=Path(done['resource_final_state']);handoff=Path(done['timing_initial_state']);final=Path(done['final_state'])
assert rdone['initial_state']==str(initial) and rdone['final_state']==rc['final_state']==str(resource_final)
rootv=vector(initial);rootaxes=physical(initial)
manifest=read(run_dir(initial)/'manifest.json');cmd=manifest['command'];assert cmd[cmd.index('--router_max_convergence_count')+1]=='8' and cmd[cmd.index('--router_reconvergence_cpd_threshold')+1]=='1.01'
assert cmd[cmd.index('--seed')+1]=='11' and manifest['environment']['VPR_H3D_MODE']=='off'
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
  worker=tx/name;wc=read(worker/'completion.json');assert wc['passed'];wm=read(run_dir(worker)/'manifest.json');assert sha(wm['command'][0])==config['phase_binary_sha256']['route_and_resource'];resource_counts['native_transactions']+=1
  source=Path(role['state']);assert all(vector(source)[k]==vector(worker)[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
  if row['status']=='transaction_failed_rolled_back':resource_counts['rolled_back_candidates']+=1;continue
  assert row['status']=='legal_evaluated' and not row['native_reused'];state=Path(row['evaluation']);r=physical(state)
  decision=decide('resources_under_timing',vector(source),vector(state),physical(source),r,cpd_limit_s=rootv['cpd_s'],resource_limits=rreg['resource_limits'],native_valid=True,transaction_complete=True,resource_objectives=('SB_pairs','CB_sources'))
  assert decision==read(tx/(name+'_decisions.json'))['resources_under_timing'];assert sha(read(run_dir(state)/'manifest.json')['command'][0])==config['phase_binary_sha256']['route_and_resource'];resource_counts['legal_candidates']+=1
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
  assert sta_binary==config['phase_binary_sha256']['route_and_resource'] and (state==handoff or state.resolve().is_relative_to(resource_flow)),'Only an actual own-run source/candidate may reuse its already executed FULL/STA'
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
write(output/'metadata_consumers.json',dict(passed=True,all_within_measured_flow=True,receipts=metadata_consumers))
files.append(output/'metadata_consumers.json')

files += [D/'verify_complete_resource_timing_joint_stream_v1.py',D/'orphaned_flow_time_evidence_v1.py',D/'orphaned_BNN_quality_preflight_01/completion.json',*map(Path,recovered['source_sha256'])]
write(output/'original_time_evidence.json',recovered);files.append(output/'original_time_evidence.json')
payload=dict(passed=True,complete_configuration_quality_verified=True,complete_observer_measurement_available=False,
    initial_state=str(initial),resource_final_state=str(resource_final),final_state=str(final),
    CPD_ns=vector(final)['cpd_s']*1e9,resources=physical(final),resource_actual_work=resource_counts,
    resource_accepted_steps=rc['accepted_steps'],timing_accepted_steps=tc['accepted_steps'],timing_attempted_proposals=tc['attempted_proposals'],
    phase_binary_sha256=config['phase_binary_sha256'],GNU_time_elapsed_seconds=recovered['elapsed_seconds'],
    waited_process_RSS_high_water_kib=recovered['waited_process_RSS_high_water_kib'],sampled_tree_PSS_peak_kib=None,
    complete_observer_wall_seconds=None,observer_CPU_seconds=None,undisturbed_timing=False,VPR_calls_new=0,
    source_sha256={str(f):sha(f) for f in files},
    qualification='Original full-flow quality gates preserved, including actual transactions, native FULL/STA, physical audits, decisions and own-flow metadata paths. Actual original GNU-time elapsed separately recovered; missing observer measurement is not reconstructed. Brief overlap and full PSS gap retained. Downstream equivalence against prior controls remains a separate requirement before a same-behavior engineering comparison. No original case or queue completion is overwritten.')
write(output/'completion.json',payload)
print({k:payload[k] for k in ['passed','CPD_ns','resources','GNU_time_elapsed_seconds','complete_observer_measurement_available']},flush=True)
