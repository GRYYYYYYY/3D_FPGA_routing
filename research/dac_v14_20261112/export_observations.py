#!/usr/bin/env python3
"""Export role rows with explicit execution keys; repeated references are not new runs."""
import json,csv,re,hashlib
from routing_log_metrics import last_iteration
from pathlib import Path
D=Path(__file__).resolve().parent
failed_index=json.loads((D/'failed_occupancy_index.json').read_text())['entries'] if (D/'failed_occupancy_index.json').exists() else {}
if (D/'failed_transfer_occupancy_index.json').exists():
 failed_index.update(json.loads((D/'failed_transfer_occupancy_index.json').read_text())['entries'])
rows=[]
for name in ['h1_dev_01','h1_dev_02','h2_dp_dev_01','h2_expansion_01','feedback_dev_01','target_query_dev_01','feedback_expansion_01','target_query_quota_dev_01','feedback_bnn_dev_01','profile_generation_dev_01','generation_confirmation_dev_01','shared_closure_dev_01','shared_confirmation_dev_01','compact_closure_dev_01','compact_confirmation_dev_01','feedback_gemm_dev_01','closure_view_dev_01','view_confirmation_dev_01','feedback_action_dev_01','feedback_prior_dev_01','incomplete_confirmation_dev_01','reassign_confirmation_dev_01','dynamic_components_dev_01','prior_trace_dev_01','eligibility_trigger_dev_01','eligibility_expansion_dev_01','target_reuse_dev_01','target_reuse_expansion_dev_01','view_gemm_dev_01','persistent_query_dev_01','persistent_view_dev_01','persistent_expansion_dev_01','retention_ablation_dev_01','delay_bound_dev_01','bound_clamp_dev_01','bound_clamp_expansion_dev_01','layer_bbox_dev_01','layer_bbox_expansion_dev_01','selective_layer_dev_01','query_priority_dev_01','query_priority_expansion_dev_01','selective_attention_dev_01','delayed_layer_dev_01','delayed_attention_dev_01','delayed_scope_expansion_dev_01','source_share_dev_01', 'source_share_expansion_dev_01','reverse_rerank_dev_01','reverse_rerank_expansion_dev_01','scope_gemm_dev_01','estimate_trace_dev_01','source_floor_dev_01','complete_distance_dev_01','complete_distance_dev_02','distance_dp_dev_01','timing_regret_dev_01','timing_regret_expansion_dev_01','equivalent_guides_dev_01','planar_trace_dev_01','planar_feedback_dev_01','exit_price_dev_01','update_pin_trace_dev_01','update_pin_trace_dev_03','target_feedback_dev_01','target_feedback_expansion_dev_01','target_gate_trace_dev_01','target_drift_dev_01','target_membership_dev_01','target_membership_dev_02','target_feedback_scale_dev_01','refresh_assignment_dev_01','refresh_assignment_expansion_dev_01','scope_target_feedback_dev_01','guide_pressure_dev_01','guide_margin_dev_01','dp_sensitivity_dev_01','tie_pressure_dev_01','relative_pressure_dev_01','tie_half_dev_01','target_feedback_transfer_dev_01','target_feedback_transfer_dev_02','target_feedback_transfer_expansion_dev_01']:
 b=D/name
 if not (b/'registration.json').exists():continue
 registration=json.loads((b/'registration.json').read_text())
 review=json.loads((b/'attempt_review.json').read_text()) if (b/'attempt_review.json').exists() else {}
 data=json.loads((b/'analysis.json').read_text()) if (b/'analysis.json').exists() else None
 observations=data['observations'] if data else json.loads((b/'observations.json').read_text()) if (b/'observations.json').exists() else []
 for x in observations:
  rd=Path(x['path']);mp=rd/'manifest.json';m=json.loads(mp.read_text()) if mp.exists() else {}
  log=rd/'stdout.log';lines=log.read_text(errors='replace').splitlines() if log.exists() and m.get('status') not in ['running','starting'] else []
  plan=[re.search(r'planning_seconds=([\d.]+)',s) for s in lines if s.startswith('H3D_PLAN ')];planning=float(plan[-1][1]) if plan else 0. if m.get('environment',{}).get('VPR_H3D_MODE','off')=='off' else None
  status=x['status']
  execution_seal=rd.parent.parent/'input_seal.json'
  if status=='legal' and rd.resolve().is_relative_to(D) and (not execution_seal.exists() or not json.loads(execution_seal.read_text())['passed']):status='legal_pending_batch_seal'
  raw_failed=failed_index.get(str(rd.resolve()),{}) if m.get('status')=='failed' else {}
  if raw_failed:
   assert hashlib.sha256(mp.read_bytes()).hexdigest()==raw_failed['manifest_sha256']
   assert hashlib.sha256(Path(raw_failed['source']).read_bytes()).hexdigest()==raw_failed['source_sha256']
   assert m['outputs']['routed.route']['sha256']==raw_failed['route_sha256']
  ph=x.get('physical_metrics') or {};me=x.get('metrics',{});legal=status=='legal';binary=m.get('command',[''])[0]
  counters={}
  for prefix in ['H3D_DELAY ','H3D_TARGET_DELAY ','H3D_SELECTED_DELAY ','H3D_SHARED_STORAGE ','H3D_CLOSURE_VIEW ','H3D_TARGET_REUSE ','H3D_PERSISTENT_DELAY ','H3D_BOUND_SELECTED_SUMMARY ','H3D_LAYER_BB ','H3D_QUERY_PRIORITY ']:
   matches=[line for line in lines if line.startswith(prefix)]
   counters[prefix]={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',matches[-1])} if matches else {}
  original=counters['H3D_DELAY '];target=counters['H3D_TARGET_DELAY '];selected=counters['H3D_SELECTED_DELAY ']
  if m.get('environment',{}).get('VPR_H3D_MIXED_DELAY')!='1':selected={}
  storage=counters['H3D_SHARED_STORAGE '];view=counters['H3D_CLOSURE_VIEW ']
  reuse=counters['H3D_TARGET_REUSE ']
  frontier=counters['H3D_PERSISTENT_DELAY ']
  bounds=counters['H3D_BOUND_SELECTED_SUMMARY '];bbox=counters['H3D_LAYER_BB '];priority=counters['H3D_QUERY_PRIORITY ']
  timefile=rd/'time.txt';rss=re.search(r'Maximum resident set size \(kbytes\): (\d+)',timefile.read_text()) if timefile.exists() else None
  rerank_lines=[line for line in lines if line.startswith('H3D_REVERSE_RERANK ')]
  rerank={k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',rerank_lines[-1])} if rerank_lines else {}
  source_shares=[{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)} for line in lines if line.startswith('H3D_SOURCE_SHARE ')]
  sharing=m.get('environment',{}).get('VPR_H3D_SOURCE_QUERY_SHARE')=='1'
  iteration=last_iteration(lines) or {}
  if me.get('iterations') is not None and iteration:assert me['iterations']==iteration['iteration'],(rd,me['iterations'],iteration)
  rows.append(dict(attempt=name,circuit=x['circuit'],architecture=registration.get('family','hybrid_o'),placement=registration.get('flow','p0'),seed=int(m['command'][m['command'].index('--seed')+1]) if '--seed' in m.get('command',[]) else registration.get('seed',11),width=registration.get('width',100),failure_classification=review.get('failure_kind'),arm=x['arm'],role_type='reused_optimization_reference' if x.get('reused_reference') else 'transaction_diagnostic_not_method_benefit' if x['arm'] in ['X','X2'] else 'historical_reference' if x['arm'] in ['A0','R1'] else 'mechanism_diagnostic_not_method_benefit' if m.get('tags',{}).get('diagnostic_only') else 'estimate_diagnostic_not_method_benefit' if m.get('environment',{}).get('VPR_H3D_TRACE_ESTIMATES')=='1' else 'algorithm_or_reproduction',status=status,
   cpd_ns=me.get('critical_path_ns') if legal else None,native_cpd_ns=me.get('critical_path_ns'),iterations=me.get('iterations') if me.get('iterations') is not None else iteration.get('iteration'),iteration_evidence='native_completion' if me.get('iterations') is not None else 'last_completed_iteration_table_row' if iteration else 'missing',last_overused_rr_nodes=iteration.get('overused_rr_nodes'),planning_seconds=planning,router_seconds=me.get('router_seconds'),process_seconds=m.get('wall_seconds'),
   peak_rss_kib=int(rss[1]) if rss else None,view_endpoint_count=view.get('endpoints'),view_local_entries=view.get('local_entries'),view_shared_references=view.get('shared_references'),
   closure_stored_words=storage.get('stored_words'),closure_logical_entries=storage.get('logical_entries'),closure_admitted=storage.get('admitted'),closure_refused=storage.get('refused'),closure_compact=storage.get('compact'),
   target_reuse_enabled=reuse.get('enabled'),target_reuse_settled_labels=reuse.get('settled_labels'),target_reuse_inserted=reuse.get('inserted'),target_reuse_uncertified_edges=reuse.get('uncertified_edges'),target_reuse_capacity_stops=reuse.get('capacity_stops'),
   frontier_enabled=frontier.get('enabled'),frontier_slots=frontier.get('slots'),frontier_evictions=frontier.get('evictions'),frontier_restarts=frontier.get('restarts'),frontier_forward_settled=frontier.get('forward_settled'),frontier_reverse_settled=frontier.get('reverse_settled'),frontier_terminal_events=frontier.get('terminal_certificates'),
   frontier_retain=frontier.get('retain'),frontier_discards=frontier.get('discards'),frontier_live_states=frontier.get('live_states'),bound_missing_sides=bounds.get('missing_sides'),bound_positive_sides=bounds.get('positive_bound_sides'),bound_raw_below_sides=bounds.get('below_bound_sides'),bound_clamp_enabled=m.get('environment',{}).get('VPR_H3D_BOUND_CLAMP'),source_geometry_floor=m.get('environment',{}).get('VPR_H3D_SOURCE_GEOMETRY_FLOOR'),refresh_assignment=m.get('environment',{}).get('VPR_H3D_REFRESH_ASSIGNMENT','inherit'),target_drift=m.get('environment',{}).get('VPR_H3D_TARGET_DRIFT','0'),target_feedback=m.get('environment',{}).get('VPR_H3D_TARGET_FEEDBACK','0'),planar_feedback=m.get('environment',{}).get('VPR_H3D_PLANAR_FEEDBACK','0'),exit_price_weight=m.get('environment',{}).get('VPR_H3D_EXIT_PRICE','0'),trace_update_pins=m.get('environment',{}).get('VPR_H3D_TRACE_UPDATE_PINS','0'),equivalent_guide_cap=m.get('environment',{}).get('VPR_H3D_EQUIVALENT_GUIDES','0'),timing_guide_mode=m.get('environment',{}).get('VPR_H3D_TIMING_GUIDE_MODE','coverage'),timing_guide_weight=m.get('environment',{}).get('VPR_H3D_TIMING_GUIDE'),estimate_trace_enabled=m.get('environment',{}).get('VPR_H3D_TRACE_ESTIMATES'),reverse_rerank_enabled=rerank.get('enabled'),reverse_rerank_pins=rerank.get('pins'),reverse_rerank_changed=rerank.get('changed'),source_share_enabled=sharing,source_share_calls=len(source_shares) if sharing else None,source_share_logged_charged=sum(e['charged'] for e in source_shares) if sharing else None,query_priority_enabled=priority.get('enabled'),query_priority_plans=priority.get('plans'),query_priority_reordered=priority.get('reordered'),delayed_layer_bb=m.get('environment',{}).get('VPR_H3D_LAYER_BB_DELAYED'),all_layer_bb=bbox.get('enabled'),selective_layer_bb=m.get('environment',{}).get('VPR_H3D_LAYER_BB_FEEDBACK'),selective_layer_expansions=sum(line.startswith('H3D_LAYER_BB_REFRESH ') for line in lines),layer_restricted_nets=bbox.get('restricted_nets'),layer_expanded_nets=bbox.get('expanded_nets'),
   saved_failed_artifact_sb_net_occupancy=raw_failed.get('physical_metrics',{}).get('sb_pair_net_occupancy'),saved_failed_artifact_cb_net_occupancy=raw_failed.get('physical_metrics',{}).get('cb_crossing_output_source_net_occupancy'),saved_failed_artifact_overused_rr_nodes=raw_failed.get('overused_rr_nodes'),saved_failed_artifact_source=raw_failed.get('source'),
   sb_net_occupancy=ph.get('sb_pair_net_occupancy'),cb_net_occupancy=ph.get('cb_crossing_output_source_net_occupancy'),
   delay_endpoint_queries=original.get('queries'),delay_settled=original.get('settled'),delay_cache_hits=original.get('cache_hits'),target_queries=target.get('queries'),target_exact=target.get('exact'),target_unknown=target.get('unknown'),target_settled=target.get('settled'),target_cache_hits=target.get('cache_hits'),target_candidate_quota=target.get('candidate_quota'),target_quota_stops=target.get('quota_stops'),selected_delay_pins=selected.get('pins'),selected_delay_informed=selected.get('informed_pins'),selected_delay_both=selected.get('both'),selected_delay_estimated=selected.get('estimated'),
   observation_environment='historical_ptrace' if x['arm'] in ['A0','R1'] else 'new_seccomp_development',source=str(rd),execution_key=str(rd),binary_sha256=m.get('shared_inputs',{}).get(binary,{}).get('sha256')))
with (D/'observations_all.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(D/'observations_all.json').write_text(json.dumps(rows,indent=2)+'\n')
print('role_rows',len(rows),'unique_existing_execution_paths',len({r['execution_key'] for r in rows if (Path(r['execution_key'])/'manifest.json').exists()}))
