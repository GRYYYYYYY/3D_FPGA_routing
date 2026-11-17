"""Small authoritative entry point; preserve historical receipts and old handoffs."""
from datetime import datetime,timezone
from pathlib import Path
import shutil
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

def evaluation_receipt_evidence(evaluation):
    """Read existing worker/materializer gates, without re-running native work.

    This is status evidence, not an adoption adapter or a new byte/STA audit.
    The materializer's installed-candidate manifest must remain distinguishable
    from the source LOAD that supplied its already executed callback.
    """
    evaluation=Path(evaluation);completion=evaluation/'completion.json';done=read(completion)
    receipts=[completion];checks=done.get('checks')
    if isinstance(checks,dict) and checks:
        evidence=dict(schema='original_worker_checks',passed=bool(done['passed'] and all(checks.values())),original_checks=checks)
    elif done.get('status')=='standalone_candidate_materialization_terminal':
        gate_path=evaluation/'runs/state/analysis_gate.json'
        audit_path=evaluation/'independent_native_analysis_audit.json'
        manifest_path=evaluation/'runs/state/manifest.json'
        registration_path=evaluation/'registration.json'
        receipts.extend([gate_path,audit_path,manifest_path,registration_path])
        gate=read(gate_path);audit=read(audit_path);manifest=read(manifest_path);registration=read(registration_path)
        worker=Path(registration['source_worker']);worker_completion=worker/'completion.json';exports_path=worker/'candidate_exports.json'
        receipts.extend([worker_completion,exports_path]);closed=read(worker_completion);exports=read(exports_path)
        passed=(done['passed'] and done.get('native_analysis_calls')==0
            and done.get('consumed_already_executed_worker_receipt') is True
            and all(gate.get(k) is True for k in ['passed','native_candidate_FULL_fresh_STA','physical_capacity_audit','source_restored'])
            and audit.get('passed') is True and audit.get('legal_count')==1 and audit.get('failed_count')==0
            and manifest.get('status')=='completed' and manifest.get('observed_state_kind')=='installed_candidate'
            and manifest.get('execution_scope')=='standalone_installed_candidate_callback'
            and manifest.get('native_analysis_calls_new')==0
            and manifest.get('source_worker_completion')==str(worker_completion)
            and manifest.get('metrics',{}).get('native_full_check_passed') is True
            and closed.get('passed') is True and exports.get('passed') is True and exports.get('candidate_gate_present') is True)
        evidence=dict(schema='original_installed_candidate_materialization',passed=bool(passed),
            original_analysis_gate=gate,original_independent_audit=dict(passed=audit.get('passed'),legal_count=audit.get('legal_count'),failed_count=audit.get('failed_count')),
            manifest_execution_scope=manifest.get('execution_scope'),source_worker=str(worker),
            consumed_already_executed_worker_receipt=done.get('consumed_already_executed_worker_receipt'),
            new_native_analysis_calls=done.get('native_analysis_calls'),
            complete_materialization_seconds=done.get('complete_materialization_seconds'))
    else:
        evidence=dict(schema=done.get('status'),passed=False,status_reason='Unsupported receipt schema; no validation inferred')
    assert all(p.stat().st_size<4*1024**2 for p in receipts),'Status reader consumes small gate receipts only'
    evidence['source_receipt_sha256']={str(p):sha(p) for p in receipts}
    return evidence

now=datetime.now(timezone.utc).isoformat()
owners=[]
for name in ['stable_seed_transfer_recovery_02','direct_scope_resource_equivalence_recovery_02',
             'native_census_resource_equivalence_recovery_02','native_checkpoint_recovery_01',
             'rejection_feedback_controller_dev_01','complete_route_resource_measurements_01',
             'vector_then_strict_comparison_01','connection_budget_resource_dev_01',
             'complete_serial_resource_measurement_dev_01','complete_serial_resource_measurement_paired_dev_01',
             'complete_serial_reusable_graph_dev_01','complete_serial_seed_policy_dev_01','serial_fused_candidate_validation_01','serial_fused_candidate_validation_02','complete_serial_fused_dev_01','complete_serial_transfer_dev_01','complete_serial_fused_dev_03','complete_serial_lazy_dev_01','connection_budget_scope_probe_01','complete_serial_lazy_transfer_dev_01','complete_serial_architecture_transfer_01','budget47_current_timing_composition_01','complete_serial_seed_transfer_01','complete_serial_source_snapshot_01','complete_serial_timing_budget_01','complete_resource_timing_full_flow_01','R1_whole_net_residual_probe_01','R1_crossing_source_probe_01','native_checkpoint_recovery_02','complete_route_resource_measurements_02','vector_then_strict_comparison_02','connection_budget_resource_dev_02','R1_owner_release_joint_probe_01','complete_serial_additional_circuits_01','complete_serial_lazy_source_snapshot_01','partial_escape_owner_intervention_01','complete_BNN_joint_index_flow_01','complete_BNN_closed_stream_flow_01','BNN_wire_timing_native_validation_01','native_checkpoint_recovery_03','complete_route_resource_measurements_03','vector_then_strict_comparison_04','robot_domain_release_ablation_01','complete_BNN_terminal_wire_flow_01','query_reduction_resource_dev_01','unexecuted_recovery_20261115_01','unified_input_integration_01','standalone_native_observation_equivalence_01','standalone_transaction_native_check_01','standalone_whole_method_check_01','portable_clstm_pair_01','robot_owner_scope_pair_01','portable_robot_p1_pair_01','complete_BNN_domain_engineering_01','portable_reduction_pair_01','clstm_input_contract_pair_02','robot_p1_input_contract_pair_02','cp1_cross_circuit_cohort_01','robot_union_mechanism_01','BNN_interleaved_timing_01','cp1r1_cross_circuit_cohort_01','cp1r2_cross_circuit_cohort_01','robot_union_mechanism_02','robot_union_verification_recovery_01','BNN_interleaved_timing_02','BNN_interleaved_timing_03','robot_owner_reentry_audit_01','robot_owner_reentry_audit_02','empty_query_patch_validation_01','confirmation_release_cp1r3_01','robot_p1_prefix_recovery_01','cp1r3_distinct_input_cohort_01','interrupted_stage_reconciliation_01','interrupted_flow_recovery_01','CP1r3_supplemental_verifier_01','CP1r3_raw_admission_01','vertical_cost_baseline_dev_01','cp1r4_gemm_pair_01','CLSTM_domain_recovery_02','LSTM_necessary_readonly_02','CLSTM_domain_recovery_03','LSTM_domain_whole_admission_03','cp1r5_tpu_os_pair_01']:
    q=D/name/('' if name.startswith('serial_fused_candidate_validation_') else 'queue')
    if (D/name/'queue_priority_02/registration.json').exists():q=D/name/'queue_priority_02'
    if (D/name/'queue_priority_03/registration.json').exists():q=D/name/'queue_priority_03'
    if (D/name/'queue_priority_04/registration.json').exists():q=D/name/'queue_priority_04'
    if (D/name/'queue_priority_05/registration.json').exists():q=D/name/'queue_priority_05'
    reg=read(q/'registration.json')
    phase=read(q/'status.json') if (q/'status.json').exists() else dict(status='running')
    live=process_identity(reg['pid'])
    live=live if live and live['state']!='Z' and live['start_ticks']==reg['start_ticks'] else None
    terminal=read(q/'completion.json') if (q/'completion.json').exists() else None
    child=None
    if 'pid' in phase:
        observed=process_identity(phase['pid'])
        if observed and observed['state']!='Z' and observed['start_ticks']==phase['start_ticks']:child=observed
    wait_channel=None
    if live:
        try:wait_channel=Path(f'/proc/{reg["pid"]}/wchan').read_text().strip()
        except FileNotFoundError:pass
    flow_stage=None
    completed_flow_stages=[]
    if phase.get('case'):
        flow=D/name/phase['case']/'flow' if name!='interrupted_flow_recovery_01' else D/name/'arms'/phase['case']/'flow'
        if (flow/'active_child.json').exists():
            stage=read(flow/'active_child.json');actual=process_identity(stage['pid'])
            if actual and actual['state']!='Z' and actual['start_ticks']==stage['start_ticks']:
                flow_stage=dict(phase=stage.get('tag') or stage['phase'],supervision_phase=stage['phase'],pid=stage['pid'],start_ticks=stage['start_ticks'],verified_live=True,actual_process=actual)
        if (flow/'stages.json').exists():
            completed_flow_stages=[{k:v for k,v in row.items() if k in ['phase','status','returncode','complete_process_seconds']} for row in read(flow/'stages.json')]
    if name=='robot_p1_prefix_recovery_01':
        recovery_flow=D/name/'flow'
        if (recovery_flow/'active_child.json').exists():
            stage=read(recovery_flow/'active_child.json');actual=process_identity(stage['pid'])
            if actual and actual['state']!='Z' and actual['start_ticks']==stage['start_ticks']:
                flow_stage=dict(phase=stage.get('tag',stage.get('phase')),pid=stage['pid'],start_ticks=stage['start_ticks'],verified_live=True,actual_process=actual)
    owners.append(dict(queue_directory=str(q),queue_generation=q.name.replace('queue_','') if q.name.startswith('queue_priority_') else 'original',flow_active_stage=flow_stage,completed_flow_stages=completed_flow_stages,batch=name,wait_channel=wait_channel,effective_wait='shared_serial_slot' if wait_channel and wait_channel.startswith('locks_lock') and phase['status'].startswith('waiting') else None,registration=str(q/'registration.json'),pid=reg['pid'],start_ticks=reg['start_ticks'],
        verified_live=live is not None,actual_process=live,actual_child=child,
        phase_status='terminal' if terminal else phase['status'],case_or_phase=phase.get('case',phase.get('phase')),terminal_receipt=None if terminal is None else str(q/'completion.json'),
        terminal_passed=None if terminal is None else terminal['passed'],observed_at=now))
checkpoint=[]
for n in ['stable_seed_transfer_dev_01/bnn_R1_native','stable_seed_transfer_recovery_01/bnn_Tf_native']:
    v=read(D/n/'current_state.json');checkpoint.append(dict(batch=n,accepted_steps=v['accepted_steps'],state=v['state'],
        original_final_pool_seal_present=(D/n/'pool/completion.json').exists(),recovery='native_checkpoint_recovery_03',recovery_successfully_closed=True,actual_completion=str(D/('native_checkpoint_recovery_03/bnn_R1_native/completion.json' if 'R1' in n else 'native_checkpoint_recovery_02/bnn_Tf_native/completion.json'))))
summary=read(D/'multiobjective_completed_feedback_01/composition_summary.json')
paper=read(D/('complete_input_paper_binding_07.json' if (D/'complete_input_paper_binding_07.json').exists() else 'native_ablation_paper_binding_06.json'))
if (D/'qualified_complete_paper_binding_08.json').exists():paper=read(D/'qualified_complete_paper_binding_08.json')
seed=read(D/'completed_seed_transfer_summary_02.json')
live_checkpoints=[]
for name in ['query_reduction_resource_dev_01/bnn_A0_paired','stable_seed_transfer_recovery_02/bnn_Tf_paired',
             'native_checkpoint_recovery_03/bnn_R1_native','native_checkpoint_recovery_02/bnn_Tf_native','rejection_feedback_controller_dev_01/endpoint','direct_scope_resource_equivalence_recovery_02/bnn_A0_paired','budget47_current_timing_composition_01/native_full462/timing','budget47_current_timing_composition_01/guided_budget54/timing','complete_resource_timing_full_flow_01/bnn_native/flow/resource_flow/repair','complete_resource_timing_full_flow_01/bnn_native/flow/timing','complete_resource_timing_full_flow_01/bnn_domain/flow/resource_flow/repair','complete_resource_timing_full_flow_01/bnn_domain/flow/timing','complete_BNN_joint_index_flow_01/bnn_native_joint_indexes/flow/resource_flow/repair','complete_BNN_joint_index_flow_01/bnn_native_joint_indexes/flow/timing','complete_BNN_closed_stream_flow_01/bnn_native_closed_stream/flow/resource_flow/repair','complete_BNN_closed_stream_flow_01/bnn_native_closed_stream/flow/timing']:
    actor=D/name
    if (actor/'current_state.json').exists():state=read(actor/'current_state.json')
    elif (actor/'resume_state.json').exists():
        resume=read(actor/'resume_state.json');state=dict(state=resume['current_state'],accepted_steps=len(read(actor/'steps.json')),round_number=resume['round_number'],anchor=resume['anchor'],checkpoint_kind='actual_portfolio_resume_state')
    else:continue
    attempts=read(actor/'attempts.json')
    live_checkpoints.append(dict(actor=name,observed_at=now,current_state=state,
        completed_attempt_records=len(attempts),actor_terminal=(actor/'completion.json').exists(),
        recent_attempts=[{k:v for k,v in row.items() if k in
            ['round','proposal','accepted','reason','after_CPD_s','after_resources','committed_evaluation']}
            for row in attempts[-2:]],
        qualification='Live checkpoint only; final workflow, cost and context seals require terminal receipts.'))
postprocessors=[]
q=D/'query_reduction_resource_dev_01/analysis_03';r=read(q/'registration.json');p=process_identity(r['pid'])
postprocessors.append(dict(directory='query_reduction_resource_dev_01/analysis_03',pid=r['pid'],start_ticks=r['start_ticks'],verified_live=bool(p and p['state']!='Z' and p['start_ticks']==r['start_ticks']),status=read(q/'status.json'),native_calls=0))
for rel in ['complete_serial_seed_transfer_01/analysis','complete_serial_timing_budget_01/analysis','R1_crossing_source_probe_01/analysis','R1_owner_release_joint_probe_01/analysis','complete_serial_additional_circuits_01/analysis','complete_serial_lazy_source_snapshot_01/analysis','complete_resource_timing_full_flow_01/analysis','complete_resource_timing_full_flow_01/domain_archive_analysis','R1_BFS_native_timing_prediction_01/analysis','unified_input_integration_01/analysis','BNN_terminal_wire_qualified_comparison_02/analysis']:
    q=D/rel;r=read(q/'registration.json');p=process_identity(r['pid']);live=bool(p and p['state']!='Z' and p['start_ticks']==r['start_ticks'])
    postprocessors.append(dict(directory=rel,pid=r['pid'],start_ticks=r['start_ticks'],verified_live=live,status=read(q/'status.json'),native_calls=0))
status=dict(observed_at=now,postprocessors=postprocessors,research_status='active',public_reference='9734eee83b62fc012f0bb137f75aba919df514e4',publication_receipt='../../docs/github_progress_publication_receipt_20261115.json',
    current_archive='multiobjective_closed_stream_quality_01',legal_observations=671,complete_configurations=34,complete_observer_measured_configurations=33,qualified_GNU_only_configurations=1,paper_archive='multiobjective_closed_stream_quality_01',paper_archive_records=671,paper_figure_archive_records=640,
    paper_pdf=paper['pdf'],paper_pages=6,new_work_pushed=False,owners=owners,private_checkpoints=checkpoint,
    unintegrated_verified_domain_archive=None,
    closed_domain_resource_phase=(read(D/'complete_resource_timing_full_flow_01/bnn_domain/flow/resource_flow/completion.json') if (D/'complete_resource_timing_full_flow_01/bnn_domain/flow/resource_flow/completion.json').exists() else None),
    pending_structural_proposals=[read(D/'BNN_wire_timing_composition_01/completion.json')],completed_structural_proposal_validation='partial_escape_owner_intervention_01/verification.json',
    readonly_diagnostics=dict(owner_local_reachability=read(D/'R1_owner_release_local_reachability_02/completion.json'),unsigned_edge_lookup=read(D/'rr_unsigned_edge_lookup_validation_01/completion.json')),
    live_actor_checkpoints=live_checkpoints,
    evidence=dict(unified_implementation='unified_confirmation_candidate_01/implementation_status_01.json',owner_adapter='current_owner_transaction_validation_01/completion.json',unified_noop='unified_resource_noop_preflight_01/completion.json',unified_input_queue='unified_input_integration_01/queue/registration.json',unified_paper='unified_structure_paper_binding_01.json',confirmation_contract='unified_confirmation_candidate_01/integration_contract.json',confirmation_inputs='confirmation_input_inventory_01/completion.json',main_table_endpoints='unified_main_table_evidence_01/completion.json',budget_fragmentation='budget64_fragmentation_analysis_01/completion.json',query_reduction_grouping='query_reduction_grouping_validation_01/completion.json',query_reduction_queue='query_reduction_resource_dev_01/queue/registration.json',terminal_wire_full_flow='complete_BNN_terminal_wire_flow_01/plan.json',latest_archive='multiobjective_closed_stream_quality_01/verification.json',additional_circuits='complete_serial_additional_circuits_01/comparison.json',partial_owner='partial_escape_owner_intervention_01/verification.json',BFS_native_model='R1_BFS_native_timing_prediction_01/analysis/completion.json',robot_first_scope='robot_domain_first_scope_analysis_02/completion.json',terminal_policy_verified='terminal_timing_envelope_policy_01/verification.json',terminal_policy_robot_transfer='robot_terminal_wire_transfer_01/completion.json',robot_release_ablation='robot_domain_release_ablation_01/plan.json',joint_indexes_complete='complete_BNN_joint_index_flow_01/comparison.json',lazy_source_complete='complete_serial_lazy_source_snapshot_01/comparison.json',publication_guide='../../docs/GitHub_progress_20261115.md',R1_native_closed_archive='multiobjective_closed_R1_native_01/verification.json',terminal_timing_policy='terminal_timing_envelope_policy_01/registration.json',all_eight_own_current_controls_closed='closed_seed_transfer_eight_roles_01.json',R1_joint_owner_escape_archive='multiobjective_R1_joint_owner_escape_01/verification.json',Tf_native_archive='multiobjective_closed_Tf_native_01/verification.json',R1_recovery03_validation='native_checkpoint_adapter_v4_replay_01/completion.json',R1_recovery03='native_checkpoint_recovery_03/queue/registration.json',complete_measurements03='complete_route_resource_measurements_03/queue/registration.json',strict04='vector_then_strict_comparison_04/queue/registration.json',complete_BNN_domain_case='complete_resource_timing_full_flow_01/bnn_domain/completion.json',complete_BNN_domain_costs='complete_BNN_domain_cost_analysis_01/summary.json',actual_cold_pair='complete_resource_timing_full_flow_01/comparison.json',native_cost_ranking='BNN_complete_transaction_cost_rank_01/completion.json',domain_wire_delta='cold_domain_wire_delta_analysis_01/completion.json',Tf_native_recovery_closed='native_checkpoint_recovery_02/bnn_Tf_native/completion.json',domain_archive_postprocessing='BNN_domain_archive_postprocessing_preflight_01.json',actual_case_cost_parser_validation='complete_BNN_case_cost_v2_validation_01.json',terminal_wire_alternative='BNN_terminal_wire_alternative_01/completion.json',terminal_rule_and_merge_validation='terminal_wire_selector_merge_validation_01/completion.json',terminal_wire_composition='BNN_wire_timing_composition_01/completion.json',terminal_composition_prediction='BNN_wire_composition_timing_prediction_01/completion.json',terminal_composition_native_plan='BNN_wire_timing_native_validation_01/plan.json',complete_BNN_cache_boundary='BNN_complete_cache_boundary_01/completion.json',existing_streaming_current='existing_streaming_loader_current_validation_01/completion.json',preparation_profile='BNN_portfolio_preparation_profile_01/completion.json',closed_stream_full_flow='complete_BNN_closed_stream_flow_01/plan.json',native_timing_protocol_identity='native_timing_protocol_identity_analysis_01/completion.json',cold_native_extra_retry='cold_native_extra_retry_diagnostic_01/completion.json',frozen_binary_RRG_capability='frozen_binary_RRG_format_capability_01.json',joint_index_component='joint_graph_indexes_BNN_payload_validation_01/completion.json',joint_index_full_flow_plan='complete_BNN_joint_index_flow_01/plan.json',joint_index_full_flow_preflight='complete_BNN_joint_index_flow_01/preflight.json',joint_index_equivalence_guard='complete_resource_timing_equivalence_validation_01/completion.json',cold_BNN_pair_initial_identity='BNN_cold_pair_initial_identity_01.json',cold_native_source_identities='cold_native_source_identity_analysis_01/completion.json',complete_BNN_native_case='complete_resource_timing_full_flow_01/bnn_native/completion.json',complete_BNN_native_costs='complete_BNN_native_cost_analysis_01/summary.json',R1_native_float32_delays='R1_native_float32_route_delay_validation_01/completion.json',BFS_native_timing_prediction='R1_BFS_native_timing_prediction_01/completion.json',bounded_perturbation_screen_validation='bounded_route_perturbation_screen_validation_01/completion.json',owner_local_reachability='R1_owner_release_local_reachability_02/completion.json',unsigned_edge_lookup_validation='rr_unsigned_edge_lookup_validation_01/completion.json',owner_BFS_structural_proposal='R1_escape_owner_BFS_candidate_01/completion.json',partial_owner_intervention='partial_escape_owner_intervention_01/plan.json',partial_owner_intervention_preflight='partial_escape_owner_intervention_01/preflight.json',BNN_full_pair_postprocessing='complete_BNN_pair_postprocessing_preflight_01.json',R1_single_net_local_minimum='R1_single_net_vertical_local_minimum_01/completion.json',R1_local_certificate_artifacts='R1_local_minimum_artifact_validation_01.json',generic_escape_owner_selector='current_escape_owner_selector_validation_01/completion.json',checkpoint_adapter_actual_replay='native_checkpoint_adapter_v2_replay_01/completion.json',sealed_native_partial_observations='multiobjective_revalidated_native_checkpoints_01/checkpoint_and_pending_summary.json',additional_circuits_plan='complete_serial_additional_circuits_01/plan.json',lazy_snapshot_composition_plan='complete_serial_lazy_source_snapshot_01/plan.json',complete_flow_equivalence='complete_flow_equivalence_validation_01/completion.json',R1_explicit_single_net_failure='R1_crossing_source_probe_01/verification.json',R1_local_escape_cut='R1_local_escape_owner_diagnostic_01/completion.json',R1_joint_owner_plan='R1_owner_release_joint_probe_01/plan.json',recovery_queue_reconciliation='native_chain_queue_failure_reconciliation_01/completion.json',SB_fixed_budget_pair='complete_serial_timing_budget_01/comparison.json',recovery_representation='native_checkpoint_representation_diagnostic_01/completion.json',source_snapshot_complete='complete_serial_source_snapshot_01/comparison_v2.json',R1_whole_net_probe_complete='R1_whole_net_residual_probe_01/verification.json',R1_explicit_crossing_source_probe='R1_crossing_source_probe_01/plan.json',archive='multiobjective_connection_budget_closed_01/completion.json',
        quality='multiobjective_completed_feedback_01/composition_summary.json',paper='R1_native_closure_paper_binding_01.json',
        feedback_exchange='feedback_exchange_candidates_validation_01/completion.json',feedback_successor='feedback_successor_candidates_validation_01/completion.json',seed_transfer='completed_seed_transfer_summary_02.json',Tf_terminal='Tf_fixed_seed_resource_closure_01.json',R1_mechanism='R1_fixed_seed_resource_mechanism_01.json',
        checkpoint_preflight='native_checkpoint_recovery_preflight_01/completion.json',
        feedback_controller_proposal_validation='current_rejection_feedback_validation_01/completion.json',
        transitive_reuse_diagnostic='transaction_history_resolution_validation_01.json',
        full_flow_measurement_plan='complete_route_resource_measurements_01/plan.json',
        process_tree_measurement_validation='process_tree_measurement_validation_01/completion.json',
        controller_terminal='controller_feedback_closure_01.json',actual_feedback_controller_transition='controller_feedback_transition_01.json',
        fresh_route_entry_tiny='fresh_route_entry_preflight_01/completion.json',
        fresh_route_entry_eltwise='fresh_route_entry_preflight_02_eltwise/completion.json',
        serial_complete_measurement='complete_serial_resource_measurement_dev_01/completion.json',
        serial_paired_measurement='complete_serial_resource_measurement_paired_dev_01/completion.json',serial_complete_comparison='complete_serial_pair_comparison_01.json',
        serial_graph_reuse='complete_serial_cache_comparison_01.json',
        serial_seed_policy_plan='complete_serial_seed_policy_dev_01/plan.json',serial_seed_policy_comparison='complete_serial_seed_policy_dev_01/comparison.json',direct_four_roles='direct_completed_roles_validation_02/completion.json',seed19_plan='complete_serial_seed_transfer_01/plan.json',census_four_roles='census_completed_roles_validation_02/completion.json',seed_transfer_analysis='complete_serial_seed_transfer_01/analysis/registration.json',SB_fixed_budget_replay='SB_fixed_timing_budget_replay_01/completion.json',SB_fixed_budget_plan='complete_serial_timing_budget_01/plan.json',source_snapshot_build='source_snapshot_stage_01/build_verification.json',source_snapshot_flow_plan='complete_serial_source_snapshot_01/plan.json',budget47_intermediate='multiobjective_budget47_complete_pair_01/complete_pair_summary.json',budget47_pair_terminal='budget47_current_timing_composition_01/comparison.json',seed19_completion='complete_serial_seed_transfer_01/comparison.json',budget47_native_terminal='budget47_native_timing_terminal_validation_01/completion.json',budget47_first_timing_transfer='budget47_first_timing_transfer_validation_01/completion.json',complete_BNN_resource_timing_plan='complete_resource_timing_full_flow_01/plan.json',cold_timing_cli_integration='cold_timing_cli_integration_01/completion.json',BNN_vertical_cut_bound='BNN_vertical_cut_bound_01/completion.json',R1_last_vertical_excess='R1_last_vertical_excess_diagnostic_01/completion.json',R1_whole_net_probe='R1_whole_net_residual_probe_01/plan.json',standalone_fused_registration='serial_fused_candidate_validation_02/registration.json',standalone_fused_failed_guard='serial_fused_candidate_validation_01/completion.json',standalone_fused_serialization='serial_fused_serialization_validation_01/completion.json',complete_fused_plan='complete_serial_fused_dev_01/plan.json',complete_transfer_plan='complete_serial_transfer_dev_01/plan.json',complete_spmv_zero_scope='complete_serial_transfer_dev_01/spmv_pair_completion.json',complete_transfer_comparison='complete_serial_transfer_dev_01/comparison.json',callback_report_precision='callback_report_precision_validation_02/completion.json',corrected_fused_plan='complete_serial_fused_dev_03/plan.json',lazy_scheduling_validation='lazy_resource_scheduling_validation_01/completion.json',lazy_complete_plan='complete_serial_lazy_dev_01/plan.json',complete_fused_comparison='complete_serial_fused_dev_03/comparison.json',connection_budget_scope_plan='connection_budget_scope_probe_01/plan.json',lazy_complete_comparison='complete_serial_lazy_dev_01/comparison.json',lazy_transfer_plan='complete_serial_lazy_transfer_dev_01/plan.json',budget_scope_verification='connection_budget_scope_probe_01/verification.json',lazy_transfer_comparison='complete_serial_lazy_transfer_dev_01/comparison.json',architecture_transfer_plan='complete_serial_architecture_transfer_01/plan.json',architecture_transfer_comparison='complete_serial_architecture_transfer_01/comparison.json',actual_lazy_fallback='lazy_real_fallback_validation_01/completion.json',CB_vertical_lower_bound='cb_terminal_cut_bound_01/completion.json',budget47_timing_plan='budget47_current_timing_composition_01/plan.json',
        standalone_seed_validation='serial_seed_standalone_validation_01/completion.json',current_binary_native_seed_control='complete_serial_seed_policy_dev_01/native_seed_paired/explicit_policy_verification.json',
        vector_then_strict_registration='vector_then_strict_comparison_01/queue/registration.json',
        vector_then_strict_preflight='vector_then_strict_preflight_01/completion.json',
        connection_budget_registration='connection_budget_resource_dev_01/queue/registration.json',
        connection_budget_validation='connection_budget_grouping_validation_01/completion.json'),
    verified_results=dict(cold_native_source_identities=read(D/'cold_native_source_identity_analysis_01/completion.json'),complete_BNN_native_case=read(D/'complete_resource_timing_full_flow_01/bnn_native/completion.json'),complete_BNN_native_costs=read(D/'complete_BNN_native_cost_analysis_01/summary.json'),R1_native_float32_delays=read(D/'R1_native_float32_route_delay_validation_01/completion.json'),BFS_native_timing_prediction=read(D/'R1_BFS_native_timing_prediction_01/completion.json'),R1_single_net_local_minimum=read(D/'R1_single_net_vertical_local_minimum_01/completion.json'),generic_escape_owner_selector=read(D/'current_escape_owner_selector_validation_01/completion.json'),checkpoint_adapter_actual_replay=read(D/'native_checkpoint_adapter_v2_replay_01/completion.json'),sealed_native_partial_observations=read(D/'multiobjective_revalidated_native_checkpoints_01/checkpoint_and_pending_summary.json'),R1_local_escape_cut=read(D/'R1_local_escape_owner_diagnostic_01/completion.json'),R1_explicit_single_net_failure=read(D/'R1_crossing_source_probe_01/verification.json'),SB_fixed_budget_pair=read(D/'complete_serial_timing_budget_01/comparison.json'),source_snapshot_complete=read(D/'complete_serial_source_snapshot_01/comparison_v2.json'),R1_whole_net_probe=read(D/'R1_whole_net_residual_probe_01/verification.json'),budget47_pair_terminal=read(D/'budget47_current_timing_composition_01/comparison.json'),seed19_complete=read(D/'complete_serial_seed_transfer_01/comparison.json'),BNN_vertical_cut_bound=read(D/'BNN_vertical_cut_bound_01/completion.json'),R1_last_vertical_excess=read(D/'R1_last_vertical_excess_diagnostic_01/completion.json'),budget47_first_timing_transfer=read(D/'budget47_first_timing_transfer_validation_01/completion.json'),native47_timing_terminal=read(D/'budget47_native_timing_terminal_validation_01/completion.json'),native_census_completed_roles=read(D/'census_completed_roles_validation_02/completion.json'),SB_fixed_timing_budget_replay=read(D/'SB_fixed_timing_budget_replay_01/completion.json'),equal_CPD_ns=13.228145689936355,native_wire_SB_CB=[2059627,82,5062],
        paired_wire_SB_CB=[2061389,43,5060],full_setup_native_to_paired=[550,799],
        independent_45SB_feedback_CPD_ns=summary['feedback_CPD_ns'],feedback_gain_ps=summary['feedback_CPD_gain_ps'],
        feedback_wire_SB_CB=[2061253,45,5060],feedback_setup_improved_regressed=[10,0],
        completed_seed_transfer_roles=read(D/'closed_seed_transfer_eight_roles_01.json')['successfully_closed_menus'],registered_seed_transfer_roles=8,historical_summary_completed_roles=seed['completed_roles'],
        R1_paired=seed['R1_paired'],A0_seed_transfer=seed['paired_A0_cases'],
        native_order_wire_comparison=seed['previous_native_order_wire_comparison'],complete_transfer=read(D/'complete_serial_transfer_dev_01/comparison.json')['results'],lazy_scheduling=read(D/'complete_serial_lazy_dev_01/comparison.json'),fused_complete=read(D/'complete_serial_fused_dev_03/comparison.json'),budget_scope=read(D/'connection_budget_scope_probe_01/verification.json')['roles'],lazy_transfer=read(D/'complete_serial_lazy_transfer_dev_01/comparison.json')['comparisons'],architecture_transfer=read(D/'complete_serial_architecture_transfer_01/comparison.json')['outcomes'],CB_vertical_lower_bound=read(D/'cb_terminal_cut_bound_01/completion.json')),
    outstanding=[
        'GitHub snapshot9734eee83b62fc012f0bb137f75aba919df514e4 pushed and independently read back; main/live HEAD/index preserved. New terminal-wire full-flow registration is subsequent local work, not included in that published snapshot.',
        'C223integrates budget64negative trajectory/fragmentation and two-connection owner dominance; Figure34uses640archive/391BNN/232coords; robot2success/2initialfail and actual whole BNN single-pass indexes retained; latest verified archive640adds all48budget64legal candidates (14policy rejects), preserving prior592including robot11states and3partial-owner observations,26successful complete configurations/5known successful circuits/3families. Failed conv_layer2roles remain in registered4denominator with actual260.10/254.57s failed costs/no legal quality. Integrate later completed cohorts into the next manuscript/archive without inferred count additions.',
        'Single-pass-index BNN full flow CLOSED: same13.228145689936355ns/2059631wire/82SB/5062CB, all graph payloads and downstream actual states/requests/native work exact;7463.17417890951s versus7933.245508622378s. Report actual470.07132971286774s descriptive difference, not standalone405.86s projection or statistical speedup. Continue explicit same-flow cache/streaming full control with all frozen gates.',
        'Two-connection BFS/native/retained-CB observations all legal at2070657wire/32SB/5071CB with original full vector, dominated by five-connection2070653wire point. Two native arms agree; actual2queries/4attempts do not show core speedup over5queries/9attempts. Registered five-connection float32 predictions match actual BFS LOAD. Preserve different binaries/constructions and shared-component cost boundaries.',
        'Budget64four roles CLOSED; BNNpaired2061423wire/43SB/5060CB at13.607436066820355ns,16accepts and10568.532993219793s imported workflow,46morewire than original fixedK8paired2061377. Preserve negative result and own-current controls. direct_strict/vector_then_strict CLOSED at2061301/2061293wire,45SB/5060CB and13.228145689936355ns; vector prefix adds opportunity and full combined cost remains unknown.',
        'Full measurement03and source-snapshot/lazy combination CLOSED with exact declared equivalence. Keep conditional graph-reuse versus fresh-build boundaries, tiny validation separate, and actual per-command quality/time/memory. Retain all prior pre-execution failures/reconciliation; no repeated completed roles.',
        'Continue registered BNN_wire_timing_native_validation_01 after closed-stream control:2059607wire structural composition still pending own native FULL/STA/model check and no old whole cost assignment. Robot release-only ablation registered afterward, one same-source scope with only release flag disabled; no execution/result yet.',
        'Resource-terminal-wire→timing full-flow batch complete_BNN_terminal_wire_flow_01 is now registered and queued after robot release ablation. Actual positive/zero/foreign-flow handoff checks and three CLI checks passed. Same original physical inputs, seed, phase binaries and current-state policies; optional same-flow endpoint-safe lower-wire handoff precedes fresh timing selection. Independent resource-prefix comparison and actual whole wall/PSS/RSS are required. No full result yet.'],
    pending_engineering_component=dict(joint_indexes=read(D/'joint_graph_indexes_BNN_payload_validation_01/completion.json'),registered_full_flow='complete_BNN_joint_index_flow_01',actual_full_result_exists=(D/'complete_BNN_joint_index_flow_01/bnn_native_joint_indexes/completion.json').exists(),actual_full_result=(read(D/'complete_BNN_joint_index_flow_01/bnn_native_joint_indexes/completion.json') if (D/'complete_BNN_joint_index_flow_01/bnn_native_joint_indexes/completion.json').exists() else None)),
    complete_research=False)
recovery=D/'supervision_recovery_20261115_01'
intervention=read(recovery/'intervention.json');original=intervention['original_measured_process']
actual=process_identity(original['pid'])
status['original_flow_recovery']=dict(original_measured_process=actual,verified_live=bool(actual and actual['state']!='Z' and actual['start_ticks']==original['start_ticks']),original_observer_missing=True,original_complete_measurement_available=False,supervisor=read(recovery/'status.json'),receipt=str(recovery/'intervention.json'))
for owner in status['owners']:
    if owner.get('actual_process',{} ) and owner['actual_process']['state'] in ['T','t']:
        owner['effective_wait']='scheduler_gate_original_orphaned_flow'
status['outstanding']=[
 'Resume only verified never-executed tasks through unexecuted_recovery_20261115_01; preserve old missing/failed owners and original live descendants. Original observer gap/brief overlap prevent complete sampled PSS or undisturbed timing claims.',
 'Unified development entry now implements current resource/owner escalation/reentry/terminal wire/current STA pipeline. Actual owner adapter reproduces native-affecting fields, zero-op SPMV execution passes without native work. Four fixed attention and robot-s23-SDC paired roles registered behind recovery; await real full-flow outcomes before standalone freeze.',
 'Prioritize distinct circuits, actual placement/routing-root identities and applicable architectures. Same-tree seeds are repeats. Preserve no-cut, route failure, no-gain and worse. Explicit SDC required for application timing claims.',
 'Separate domain/release/owner attribution; equal native/domain owner outcomes support coordination scope. Seek general selection based on crossing redundancy, capacity and slack.',
 'Record CPD/wire/SB/CB/full endpoint changes and exact whole time. SB82to43=47.56%; total SB+CB reduction=0.797%; original whole BNN overhead22.95%. Apply engineering changes to both matched arms before interleaved timing.',
 'Restructure six pages around problem, mechanism, complete results, tradeoffs, ablations and overhead/scope. Move local trajectories and recovery audit to supplement. Correct inherited aggregate counts: archive640 has30 and archive658 has33 complete modern configurations, never independent sample counts.'
]
status['standalone_runtime_component']=read(D/'standalone_native_runtime_artifact_01/completion.json')
status['standalone_runtime_component']['physical_validation']='standalone_physical_audit_validation_01/completion.json'
status['standalone_runtime_component']['execution_validation']='standalone_native_runtime_validation_01/completion.json'
publication=D.parents[1]/'docs/github_BNN_interleaved_registration_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_BNN_engineering_complete_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_complete_tradeoff_paper_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_cp1_restore_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_BNN_cost_hierarchy_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_robot_union_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_robot_composition_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_cp1_cohort_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_cp1_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_input_contract_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_complete_inputs_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_terminal_wire_complete_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_current_entry_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_terminal_comparison_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_domain_engineering_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_robot_p1_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_native_ablation_links_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_native_ablation_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_query_terminal_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_routing_position_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_robot_owner_scope_publication_receipt_20261116.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_mechanism_inputs_publication_receipt_20261115.json'
if not publication.exists(): publication=D.parents[1]/'docs/github_unified_method_publication_receipt_20261115.json'
new_publication=D.parents[1]/'docs/github_runtime_recovery_publication_receipt_20261116.json'
if new_publication.exists():publication=new_publication
pair_publication=D.parents[1]/'docs/github_CP1r2_first_pair_publication_receipt_20261116.json'
if pair_publication.exists():publication=pair_publication
cohort_publication=D.parents[1]/'docs/github_cohort_mechanism_publication_receipt_20261116.json'
if cohort_publication.exists():publication=cohort_publication
precision_publication=D.parents[1]/'docs/github_precision_registration_publication_receipt_20261116.json'
if precision_publication.exists():publication=precision_publication
prefix_publication=D.parents[1]/'docs/github_prefix_recovery_publication_receipt_20261116.json'
if prefix_publication.exists():publication=prefix_publication
mechanism_publication=D.parents[1]/'docs/github_mechanism_selection_publication_receipt_20261116.json'
if mechanism_publication.exists():publication=mechanism_publication
distinct_publication=D.parents[1]/'docs/github_CP1r3_distinct_protocol_publication_receipt_20261116.json'
if distinct_publication.exists():publication=distinct_publication
interrupted_publication=D.parents[1]/'docs/github_interrupted_stage_publication_receipt_20261116.json'
if interrupted_publication.exists():publication=interrupted_publication
flow_publication=D.parents[1]/'docs/github_interrupted_flow_publication_receipt_20261116.json'
if flow_publication.exists():publication=flow_publication
native_timing_publication=D.parents[1]/'docs/github_BNN_timing03_native0_publication_receipt_20261116.json'
if native_timing_publication.exists():publication=native_timing_publication
priority_publication=D.parents[1]/'docs/github_confirmation_priority_publication_receipt_20261116.json'
if priority_publication.exists():publication=priority_publication
seed_publication=D.parents[1]/'docs/github_input_seed_publication_receipt_20261116.json'
if seed_publication.exists():publication=seed_publication
domain_timing_publication=D.parents[1]/'docs/github_BNN_timing03_domain0_publication_receipt_20261116.json'
if domain_timing_publication.exists():publication=domain_timing_publication
sharing_position_publication=D.parents[1]/'docs/github_sharing_prior_art_publication_receipt_20261116.json'
if sharing_position_publication.exists():publication=sharing_position_publication
for name in ['github_BNN_timing03_domain1_publication_receipt_20261116.json',
             'github_BNN_timing03_balanced_publication_receipt_20261116.json',
             'github_balanced_cost_paper_publication_receipt_20261116.json',
             'github_CP1r3_native_failure_publication_receipt_20261117.json',
             'github_research_status_publication_receipt_20261117.json',
             'github_submission_candidate_publication_receipt_20261117.json',
             'github_CP1r3_raw_admission_publication_receipt_20261117.json',
             'github_LSTM_cost_progress_publication_receipt_20261117.json',
             'github_owner_binding_development_publication_receipt_20261117.json',
             'github_dependency_narrative_publication_receipt_20261117.json',
             'github_vertical_cost_queue_publication_receipt_20261117.json',
             'github_closing_menu_inputs_publication_receipt_20261117.json',
             'github_submission_export_publication_receipt_20261117.json',
             'github_LSTM_tradeoffs_publication_receipt_20261117.json',
             'github_LSTM_incident_publication_receipt_20261117.json',
             'github_submission_clarifications_publication_receipt_20261117.json',
             'github_priority05_status_publication_receipt_20261117.json',
             'github_lstm_complete_execution_publication_receipt_20261117.json',
             'github_dla_initial_failure_publication_receipt_20261117.json']:
    candidate=D.parents[1]/'docs'/name
    if candidate.exists():publication=candidate
terminal_publication=D.parents[1]/'docs/github_CP1r3_terminal_publication_receipt_20261117.json'
if terminal_publication.exists():publication=terminal_publication
vertical_terminal_publication=D.parents[1]/'docs/github_vertical_cost_terminal_publication_receipt_20261117.json'
if vertical_terminal_publication.exists():publication=vertical_terminal_publication
legacy_recovery_publication=D.parents[1]/'docs/github_legacy_recovery_publication_receipt_20261117.json'
if legacy_recovery_publication.exists():publication=legacy_recovery_publication
reduction_native_publication=D.parents[1]/'docs/github_reduction_native_publication_receipt_20261117.json'
if reduction_native_publication.exists():publication=reduction_native_publication
confirmed_cost_publication=D.parents[1]/'docs/github_confirmed_cost_publication_receipt_20261117.json'
if confirmed_cost_publication.exists():publication=confirmed_cost_publication
cp1r4_gemm_publication=D.parents[1]/'docs/github_CP1r4_GEMM_publication_receipt_20261117.json'
if cp1r4_gemm_publication.exists():publication=cp1r4_gemm_publication
gemm_timeout_publication=D.parents[1]/'docs/github_GEMM_native_timeout_publication_receipt_20261117.json'
if gemm_timeout_publication.exists():publication=gemm_timeout_publication
latest_GEMM_LSTM_publication=D.parents[1]/'docs/github_GEMM_LSTM_submission_publication_receipt_20261117.json'
if latest_GEMM_LSTM_publication.exists():publication=latest_GEMM_LSTM_publication
latest_LSTM_admission_publication=D.parents[1]/'docs/github_LSTM_admission_publication_receipt_20261117.json'
if latest_LSTM_admission_publication.exists():publication=latest_LSTM_admission_publication
latest_LSTM_mechanisms_publication=D.parents[1]/'docs/github_LSTM_mechanisms_publication_receipt_20261117.json'
if latest_LSTM_mechanisms_publication.exists():publication=latest_LSTM_mechanisms_publication
status['latest_incremental_publication']=read(publication if publication.exists() else D.parents[1]/'docs/github_resource_controller_publication_receipt_20261115.json')
analysis=D/'orphaned_BNN_quality_analysis_01'
areg=read(analysis/'registration.json');ap=process_identity(areg['pid'])
status['orphaned_BNN_quality_analysis']=dict(registration=areg,actual_process=ap,
    verified_live=bool(ap and ap['state']!='Z' and ap['start_ticks']==areg['start_ticks']),
    phase=read(analysis/'status.json'),completion=read(analysis/'completion.json') if (analysis/'completion.json').exists() else None,
    native_calls=0,original_experiment_receipts_untouched=True)
status['orphaned_BNN_quality_analysis'].update(subsequent_v2_passed=True,subsequent_v2_receipt='orphaned_BNN_quality_analysis_02/completion.json',first_failure_preserved=True)
status['completed_closed_stream_engineering']=read(D/'orphaned_BNN_engineering_comparison_01/completion.json')
status['queue_timing_qualification']=read(D/'query_reduction_timing_qualification_01/completion.json')
status['evidence'].update(observation_dependencies='standalone_observation_dependencies_validation_02/completion.json',native_observation_plan='standalone_native_observation_equivalence_01/plan.json',unified_implementation='unified_confirmation_candidate_01/implementation_status_08.json',unified_paper='routing_position_paper_binding_05.json',paper='routing_position_paper_binding_05.json',main_table_endpoints='unified_main_table_evidence_02/completion.json',archive='multiobjective_closed_stream_quality_01/verification.json')
status['outstanding'][0]='Original full BNN completed and quality/work equivalence verified; keep original observer loss/overlap and qualified GNU time. Query-reduction queue resumed and continues BNN roles; follow existing recovery/integration chain without repeating completed roles.'
status['standalone_observation_dependencies']=read(D/'standalone_observation_dependencies_validation_02/dependency_test.json')
status['standalone_observation_dependencies'].update(native_execution_completed=False,native_queue='standalone_native_observation_equivalence_01/queue/registration.json')
status['standalone_selection_validation']=read(D/'standalone_selection_validation_01/completion.json')
status['completed_query_reduction_comparison']=read(D/'query_reduction_completed_comparison_02/rows.json')
status['evidence'].update(portable_selectors='standalone_selection_validation_01/completion.json',completed_query_grouping='query_reduction_completed_comparison_02/completion.json')
status['archive_coverage']=read(D/'multiobjective_closed_stream_quality_01/verification.json')
status['standalone_transaction_dependencies']=read(D/'standalone_transactions_validation_03/completion.json')
status['standalone_transaction_guards']=read(D/'standalone_transaction_guards_01/completion.json')
status['evidence'].update(portable_transactions='standalone_transactions_validation_03/completion.json',portable_transaction_guards='standalone_transaction_guards_01/completion.json')
status['standalone_release_replay']=read(D/'standalone_release_replay_01/completion.json')
status['standalone_native_transaction_plan']='standalone_transaction_native_check_01/plan.json'
status['evidence'].update(portable_release='standalone_release_replay_01/completion.json',native_transaction_plan='standalone_transaction_native_check_01/plan.json')
status['portable_resource_controller']=read(D/'standalone_resource_controller_component_03.json')
status['evidence'].update(portable_resource_controller='standalone_resource_controller_component_03.json')
status['portable_unified_method']=read(D/'standalone_unified_method_component_03.json')
status['evidence'].update(portable_unified_method='standalone_unified_method_component_03.json',unified_implementation='unified_confirmation_candidate_01/implementation_status_10.json',whole_method_execution_plan='standalone_whole_method_check_01/plan_v2.json')
status['outstanding'].insert(1,'Original complete serial timing portfolio and outer method now relocated. Actual feedback/portfolio/query reuse and worker boundary tests passed; native whole-method execution is appended after existing native interface checks. Keep versions fixed; verify positive owner reentry and distinct-input outcomes before confirmation freeze.')
status['structural_input_screen']=read(D/'structural_input_screen_01/completion.json')
status['robot_conditional_domain_obstruction']=read(D/'robot_release_capacity_cut_01/completion.json')
status['robot_current_owner_screen']=read(D/'robot_current_owner_screen_01/completion.json')
status['evidence'].update(structural_inputs='structural_input_screen_01/completion.json',robot_capacity_domain='robot_release_capacity_cut_01/completion.json',robot_owner_proposals='robot_current_owner_screen_01/completion.json',portable_clstm_pair='portable_clstm_pair_01/plan.json')
status['outstanding'].insert(2,'Fixed dev03 clstm native/domain pair appended after whole-method execution check; prerequisite must pass before native work. Exact robot release-domain capacity proof completed; no-release native ablation remains queued. Current generic selector finds 16 slack-eligible owner proposals, not executed gains. Target-only versus added-owner scope on same robot root is now separately registered; do not tune BNN IDs or repeat completed roles.')
status['robot_owner_scope_plan']='robot_owner_scope_pair_01/plan.json'
status['robot_owner_local_reachability']=read(D/'robot_owner_local_reachability_01/completion.json')
status['evidence'].update(robot_owner_scope='robot_owner_scope_pair_01/plan.json',robot_owner_local_reachability='robot_owner_local_reachability_01/completion.json')
status['outstanding'].insert(2,'Robot same-root unrestricted target-only vs added-owner scope pair registered after clstm. Generic rank0 frozen before native outcomes;18 actual residual reachability checks give2 target-only no-path and16 owner unlock models. Owner replacement/native FULL/STA and costs still pending; do not count these as completed repairs or independent inputs.')
status['evidence'].update(query_reduction_terminal_analysis='query_reduction_resource_dev_01/analysis_03/registration.json',query_reduction_terminal_analysis_validation='query_reduction_terminal_03_validation.json')
status['portable_robot_p1_plan']='portable_robot_p1_pair_01/plan.json'
status['portable_robot_p1_identity']=read(D/'portable_robot_p1_pair_01/physical_identity_check.json')
status['evidence'].update(portable_robot_p1='portable_robot_p1_pair_01/plan.json',robot_p1_identity='portable_robot_p1_pair_01/physical_identity_check.json')
status['outstanding'].append('Fixed dev03 robot p1 native/domain full-method pair registered after robot owner scope. Different actual packing and normalized placement coordinates from modern p0, same circuit/architecture. Known historical development input; fresh routing and actual mechanism triggers/outcomes remain pending. No old route import or target injection; same owner opportunity in both arms.')
status['completed_composition_validation']=read(D/'BNN_wire_timing_native_validation_01/verification.json')
status['completed_robot_no_release_ablation']=read(D/'robot_domain_release_ablation_01/verification.json')
status['pending_structural_proposals']=[]
status['evidence'].update(unified_paper='native_ablation_paper_binding_06.json',paper='native_ablation_paper_binding_06.json',native_composition='BNN_wire_timing_native_validation_01/verification.json',robot_no_release='robot_domain_release_ablation_01/verification.json')
status['outstanding'][0]='BNN grouping, fixed three-net composition LOAD and robot no-release ablation are terminal. Keep their imported cost scopes separate. Original recovery queue has entered complete terminal-wire BNN; follow the existing integration chain without repeating completed roles. Four-role endpoint/workload comparison waits for the shared serial slot.'
status['outstanding']=[s.replace('no-release native ablation remains queued.', 'no-release native ablation now fails with exact rollback on the same request; actual owner scope remains queued.') for s in status['outstanding']]
grouping_terminal=D/'query_reduction_resource_dev_01/bnn_A0_paired/completion.json'
if grouping_terminal.exists() and read(grouping_terminal).get('passed'):
    grouping=read(grouping_terminal);control_path=D/'stable_seed_transfer_dev_01/bnn_A0_paired/completion.json';control=read(control_path)
    status['query_reduction_terminal_observation']=dict(
        completion=str(grouping_terminal),completion_sha256=sha(grouping_terminal),
        control_completion=str(control_path),control_completion_sha256=sha(control_path),
        accepted_steps=grouping['accepted_steps'],final_resources=grouping['final_resources'],CPD_s=grouping['final_CPD_s'],
        imported_workflow_seconds=grouping['complete_imported_algorithm_workflow_seconds'],
        K8_imported_workflow_seconds=control['complete_imported_algorithm_workflow_seconds'],
        K8_wire_delta=grouping['final_resources']['wirelength']-control['final_resources']['wirelength'],
        historical_time_difference_percent=100*(grouping['complete_imported_algorithm_workflow_seconds']/control['complete_imported_algorithm_workflow_seconds']-1),
        full_four_role_comparison_pending=not (D/'query_reduction_completed_comparison_03/completion.json').exists(),
        interpretation='No cost benefit established for the factor-two proposed-query grouping heuristic. Do not promote it into the registered dev03 confirmation candidate or tune a few BNN wire units. Retain the actual tradeoff and prioritize queued cross-input and mechanism checks.',
        qualification='Terminal receipt observation only; historical imported-state times are not interleaved causal speed measurements or complete cold-configuration costs. Full endpoint/workload comparison waits for the shared serial slot.')
status['domain_engineering_plan']='complete_BNN_domain_engineering_01/plan.json'
status['evidence'].update(domain_engineering='complete_BNN_domain_engineering_01/plan.json',domain_engineering_preflight='complete_BNN_domain_engineering_01/preflight.json')
engineering_root=D/'complete_BNN_domain_engineering_01'
engineering_case=engineering_root/'bnn_domain_closed_stream'
engineering_resource=engineering_case/'flow/resource_flow/repair'
engineering_timing=engineering_case/'flow/timing'
if (engineering_resource/'steps.json').exists():
    resource_steps=read(engineering_resource/'steps.json')
    timing_steps=read(engineering_timing/'steps.json') if (engineering_timing/'steps.json').exists() else []
    resource_done=read(engineering_resource/'completion.json') if (engineering_resource/'completion.json').exists() else None
    progress=dict(resource_accepted_steps=len(resource_steps),timing_accepted_steps=len(timing_steps),
        resource_phase_verified_terminal=bool(resource_done and resource_done.get('passed')),
        resource_completion=str(engineering_resource/'completion.json') if resource_done else None,
        current_CPD_s=None,current_resources=None,current_state=None,
        whole_case_verified=False,whole_case_receipt=None,full_comparison=None)
    if resource_steps:
        last=resource_steps[-1];role=last['roles'][last['accepted_role']]
        progress.update(current_CPD_s=role['cpd_s'],current_resources=role['resources'],current_state=last['committed_evaluation'])
    if timing_steps:
        last=timing_steps[-1]
        progress.update(current_CPD_s=last['after_CPD_s'],current_resources=last['after_resources'],current_state=last['evaluation'])
    if (engineering_case/'completion.json').exists():
        actual=read(engineering_case/'completion.json')
        progress['whole_case_receipt']=str(engineering_case/'completion.json')
        progress['whole_case_verified']=bool(actual.get('passed'))
        if actual.get('passed'):
            progress.update(final_CPD_ns=actual['CPD_ns'],final_resources=actual['resources'],complete_wall_seconds=actual['complete_wall_seconds'],
                sampled_tree_PSS_peak_kib=actual['sampled_tree_PSS_peak_kib'],missing_memory_observations=actual['missing_memory_observations'])
    if (engineering_root/'comparison.json').exists():
        comparison=read(engineering_root/'comparison.json')
        progress['full_comparison']={k:comparison[k] for k in ['passed','successful_new_roles','failure_stage','same_role_execution_exact',
            'comparable_engineering_cost_observation','descriptive_same_role_seconds_difference','descriptive_same_role_percent_difference',
            'actual_complete_seconds','optimized_pair_cost_ratio_established','stable_interleaved_timing_complete'] if k in comparison}
        status['evidence']['domain_engineering_comparison']='complete_BNN_domain_engineering_01/comparison.json'
    progress['qualification']='Intermediate accepted states are not complete outputs. Only a verified whole case supplies final cost; same-role engineering attribution requires completed execution equivalence. No independent input or interleaved timing claim.'
    status['domain_engineering_actual_progress']=progress
status['evidence'].update(terminal_wire_qualified_comparison='BNN_terminal_wire_qualified_comparison_02/plan.json',terminal_wire_comparison_validation='BNN_terminal_wire_qualified_comparison_validation_02.json')
terminal_case=D/'complete_BNN_terminal_wire_flow_01/bnn_native_terminal_wire'
terminal_flow=terminal_case/'flow'
if (terminal_flow/'terminal_resource_handoff.json').exists():
    handoff=read(terminal_flow/'terminal_resource_handoff.json')
    selection=read(terminal_flow/'terminal_wire_selection/completion.json')
    chosen=selection.get('selected')
    stage=read(terminal_flow/'active_child.json') if (terminal_flow/'active_child.json').exists() else None
    actual=process_identity(stage['pid']) if stage else None
    stage_live=bool(actual and actual['state']!='Z' and actual['start_ticks']==stage['start_ticks'])
    verified=(terminal_case/'completion.json').exists() and read(terminal_case/'completion.json').get('passed',False)
    status['terminal_wire_actual_handoff_observation']=dict(
        resource_stage_passed=read(terminal_flow/'resource_flow/completion.json')['passed'],
        handoff_passed=handoff['passed'],terminal_wire_commits=handoff['terminal_wire_commits'],
        before_resources=selection['current_resources'],selected_resources=chosen['resources'] if chosen else selection['current_resources'],
        selected_CPD_s=chosen['CPD_s'] if chosen else None,setup_improved=chosen['setup_improved'] if chosen else 0,
        setup_regressed=chosen['setup_regressed'] if chosen else 0,selected_checks=chosen['checks'] if chosen else {},
        actual_same_source_candidates=selection['actual_same_source_candidates'],eligible_candidates=selection['eligible_candidates'],
        current_native_phase=stage['phase'] if stage else None,current_native_phase_verified_live=stage_live,
        current_native_phase_process=actual if stage_live else None,complete_configuration_verified=bool(verified),
        handoff_receipt=str(terminal_flow/'terminal_resource_handoff.json'),
        qualification='Actual same-flow intermediate handoff only; fresh native handoff, complete timing and final whole-cost verification remain distinct. No new independent input or historical time splice.')
timing_steps=terminal_flow/'timing/steps.json'
if timing_steps.exists():
    steps=read(timing_steps)
    if steps:
        latest=steps[-1]
        decision=Path(latest['evaluation']).parent.parent/'policy_decisions.json'
        endpoint_summary=None
        if decision.exists():
            detail=read(decision).get('timing_under_resources',{}).get('endpoint_comparison')
            if detail:
                endpoint_summary={k:detail[k] for k in ['compatible','setup_improved','setup_regressed','hold_violation_regressions']}
        status['terminal_wire_current_timing_observation']=dict(accepted_steps=len(steps),
            current_CPD_s=latest['after_CPD_s'],current_resources=latest['after_resources'],
            last_before_CPD_s=latest['before_CPD_s'],last_before_resources=latest['before_resources'],
            current_state=latest['evaluation'],last_step_endpoint_summary=endpoint_summary,
            receipt=str(timing_steps),complete_configuration_verified=(terminal_case/'completion.json').exists() and read(terminal_case/'completion.json').get('passed',False),
            qualification='Current accepted timing checkpoint only; endpoint summary is relative to the immediately preceding state, not the baseline final or original root. Whole result/cost remain tied to the final verified configuration.')
if (terminal_case/'completion.json').exists() and read(terminal_case/'completion.json').get('passed'):
    flow_done=read(terminal_flow/'completion.json')
    measured=read(terminal_case/'measurement/completion.json')
    comparison_path=D/'BNN_terminal_wire_qualified_comparison_02/completion.json'
    status['completed_terminal_wire_observation']=dict(
        verified_configuration=str(terminal_case/'completion.json'),
        final_CPD_s=flow_done['final_CPD_s'],resources=flow_done['final_resources'],
        resource_accepted_steps=flow_done['resource_accepted_steps'],
        terminal_wire_commits=flow_done['terminal_wire_commits'],
        timing_accepted_steps=flow_done['timing_accepted_steps'],
        complete_command_wall_seconds=measured['complete_command_wall_seconds'],
        sampled_tree_PSS_peak_kib=measured['sampled_tree_PSS_peak_kib'],
        missing_memory_observations=measured['missing_memory_observations'],
        live_descendants_after_command_exit=measured['live_descendants_after_command_exit'],
        qualified_baseline_comparison_pending=not comparison_path.exists(),
        comparison_receipt=str(comparison_path),
        qualification='Verified fresh-route complete native terminal-wire configuration. Same historical BNN physical input; not independent evidence or full dev03 confirmation. Baseline prefix equivalence, final endpoint comparison and qualified GNU-to-GNU cost difference require the separate comparator. Memory sampling gaps and uncontrolled shared-host/page-cache conditions retained.')
    status['outstanding'][0]='BNN composition, robot no-release ablation and complete terminal-wire BNN are verified terminal. Original recovery owner exited normally and the registered cross-input chain can continue. Qualified terminal-wire baseline comparison and four-role endpoint/workload analysis wait for the shared serial slot; do not repeat native roles or infer comparisons from matching scalar metrics.'
    status['evidence']['complete_terminal_wire']='complete_BNN_terminal_wire_flow_01/bnn_native_terminal_wire/completion.json'
environment_note=D/'unified_input_integration_01/measurement_environment_note_01.json'
if environment_note.exists():
    status['measurement_environment_notes']=[read(environment_note)]
    status['evidence']['attention_measurement_environment_note']=str(environment_note)
input_results_path=D/'unified_input_integration_01/queue/results.json'
if input_results_path.exists():
    actual_input_results=read(input_results_path)
    input_plan=read(D/'unified_input_integration_01/plan.json')
    status['unified_input_actual_outcomes']=dict(
        receipt=str(input_results_path),registered_roles=len(input_plan['fixed_order']),
        terminal_roles=len(actual_input_results),
        verified_legal_roles=sum(v['status']=='complete_legal_verified' for v in actual_input_results.values()),
        results=actual_input_results,
        pending_roles=[r for r in input_plan['fixed_order'] if r not in actual_input_results],
        qualification='Actual closed roles, including initial-route failure and its full command cost. No legal quality is inferred from intermediate failed-route metrics. Native/domain arms of one physical input are not separate independent inputs; matched interpretation awaits both actual outcomes and root checks. Earlier registered development version, not dev03 confirmation.')
    status['evidence']['unified_input_actual_outcomes']=str(input_results_path)
attention_failure_pair=D/'attention_initial_failure_pair_01/completion.json'
if attention_failure_pair.exists():
    status['attention_initial_failure_pair']=read(attention_failure_pair)
    status['evidence']['attention_initial_failure_pair']=str(attention_failure_pair)
status['portable_reduction_plan']='portable_reduction_pair_01/plan.json'
status['evidence'].update(portable_reduction='portable_reduction_pair_01/plan.json',portable_reduction_preflight='portable_reduction_pair_01/preflight.json',portable_reduction_review='portable_reduction_pair_01/implementation_review.json')
status['outstanding'].append('One fixed-dev03 reduction_layer native/domain pair is appended after the already registered domain engineering arm, with the same whole-method prerequisite. Historical n125 Hybrid-O root has268 sharing scopes on62 nets and0 supported owner cuts; fresh eligibility/outcomes unknown. Motivation: actual attention paired initial failures and zero current resource candidates on robot-SDC. No native work or physical copies yet; full input hashing/copy/guarded admission deferred inside the serial slot. Preserve every failed/no-gain/worse result; do not count historical scopes as benefits or change existing queue order.')
input_comparison=D/'unified_input_integration_01/comparison.json'
if input_comparison.exists():
    status['unified_input_complete_comparison']=read(input_comparison)
    status['evidence']['unified_input_comparison']=str(input_comparison)
    status['unified_input_actual_outcomes']['qualification']='Four registered roles closed. Robot pair has identical actual initial route bodies/full vectors and final endpoint vectors; zero quality benefit. Attention initial failure remains quality=None. Known physical inputs, not unseen or frozen-controller evidence; times are descriptive shared-host observations.'
for key,rel in [('portable_observation_actual','standalone_native_observation_equivalence_01/completion.json'),('portable_transaction_actual','standalone_transaction_native_check_01/completion.json'),('complete_input_rows','complete_input_paper_evidence_07/completion.json')]:
    receipt=D/rel
    if receipt.exists():
        status[key]=read(receipt)
        status['evidence'][key]=rel
if (D/'complete_input_paper_binding_07.json').exists():
    status['evidence'].update(unified_paper='complete_input_paper_binding_07.json',paper='complete_input_paper_binding_07.json')
    status['complete_input_paper_update']=dict(complete_attempt_rows=27,scoped_component_rows=2,initial_failure_rows=4,historical_archive_counts_unchanged=True)
for key,rel in [('qualified_terminal_comparison','BNN_terminal_wire_qualified_comparison_02/completion.json'),('portable_whole_method_actual','standalone_whole_method_check_01/completion.json')]:
    if (D/rel).exists():
        status[key]=read(D/rel)
        status['evidence'][key]=rel
if (D/'qualified_complete_paper_binding_08.json').exists():
    status['evidence'].update(unified_paper='qualified_complete_paper_binding_08.json',paper='qualified_complete_paper_binding_08.json')
if (D/'clstm_input_contract_pair_02/failure_reclassification.json').exists():
    status['clstm_input_compatibility_failure']=read(D/'clstm_input_contract_pair_02/failure_reclassification.json')
    status['evidence'].update(clstm_failure_reclassification='clstm_input_contract_pair_02/failure_reclassification.json',clstm_corrected_input_plan='clstm_input_contract_pair_02/plan.json')
    status['outstanding'].append('Preserve both clstm pre-routing$undef input-compatibility failures; do not count them as congestion failures. The separately registered clstm_input_contract_pair_02 preserves historical merge_constant_generators=off in both arms and waits after reduction. Same dev03 and physical input, not a new independent sample. Validate actual guarded admission and new execution; no automatic retry of completed old roles.')
if (D/'robot_p1_input_contract_pair_02/failure_reclassification.json').exists():
    status['robot_p1_input_compatibility_failure']=read(D/'robot_p1_input_contract_pair_02/failure_reclassification.json')
    status['evidence'].update(robot_p1_failure_reclassification='robot_p1_input_contract_pair_02/failure_reclassification.json',robot_p1_corrected_input_plan='robot_p1_input_contract_pair_02/plan.json',robot_owner_scope_actual='robot_owner_scope_pair_01/verification.json')
    owner_result=read(D/'robot_owner_scope_pair_01/verification.json')
    status['robot_owner_scope_actual']=dict(passed=owner_result['passed'],complete_imported_pair_seconds=owner_result['complete_imported_pair_seconds'],source_resources=owner_result['source_resources'],outcomes={k:dict(status=v['status'],quality=v['quality'],endpoint_summary={a:b for a,b in v['endpoint_comparison'].items() if a!='changes'},resource_policy_accepted=v['resource_policy_decision']['accepted'],endpoint_policy_accepted=v['all_policies']['endpoint_vector']['accepted'],committed_to_original_actor=False) for k,v in owner_result['outcomes'].items()},qualification='Same-source unrestricted owner-scope ablation;31endpoint improvements for+12wire/+1CB relative to target-only. Not resource reduction or complete-flow cost; no original actor committed.')
if (D/'owner_contract_paper_binding_09.json').exists():
    paper=read(D/'owner_contract_paper_binding_09.json');status['paper_pdf']=paper['pdf']
    status['evidence'].update(unified_paper='owner_contract_paper_binding_09.json',paper='owner_contract_paper_binding_09.json',unified_implementation='unified_confirmation_candidate_01/implementation_status_11.json',confirmation_release='confirmation_release_cp1_01/completion.json')
    status['confirmation_release']=read(D/'confirmation_release_cp1_01/completion.json')
    status['owner_contract_paper_update']=True
    status['outstanding']=[
      'Preserve actual BNN domain engineering owner and reduction, corrected clstm, corrected robot-p1 queues; no completed batch reruns.',
      'CP1 source/rules fixed and relocated admission validated. Preregister distinct physical-input confirmation cohorts; do not reclassify previous development. Positive integrated owner reentry and timing feedback remain unconfirmed.',
      'Separate domain restriction, failed-domain release and owner scope. Robot owner trades12wire/1CB for31setup improvements; no fixed-resource commit. General triggers use redundancy, capacity and slack.',
      'Keep no-cut/no-gain/worse, initial-route failure and input-loading failure distinct. Corrected input compatibility is not yet established by native execution.',
      'Close matched domain engineering cost; retain original22.95% whole overhead,47.56% SB and0.797% total reductions until qualified new pair completes. Stable symmetric interleaved timing pending.',
      'Six-page09 sealed with31complete attempts and2scoped rows. Continue evidence-to-claim integration; no universal gain or external application timing claim.'
    ]
if (D/'complete_tradeoff_paper_binding_10.json').exists():
    paper=read(D/'complete_tradeoff_paper_binding_10.json');status['paper_pdf']=paper['pdf']
    status['evidence'].update(unified_paper='complete_tradeoff_paper_binding_10.json',paper='complete_tradeoff_paper_binding_10.json')
    status['complete_tradeoff_paper_update']=True
    status['paper_figure_archive_records']=None
    status['paper_figure_legal_configuration_pairs']=9
    status['outstanding']=[s.replace('Six-page09 sealed with31complete attempts and2scoped rows.', 'Six-page10 sealed with31complete attempts and2scoped rows; complete-pair figure replaces historical BNN projection, now supplementary.') for s in status['outstanding']]
if (D/'cp1_cross_circuit_cohort_01/launch.json').exists():
    cohort=read(D/'cp1_cross_circuit_cohort_01/plan.json')
    status['cp1_prospective_cohort']=dict(plan='cp1_cross_circuit_cohort_01/plan.json',launch='cp1_cross_circuit_cohort_01/launch.json',release_manifest_sha256=cohort['release_manifest_sha256'],registered_inputs=2,registered_roles=4,inputs=[x['id'] for x in cohort['inputs']],terminal=(D/'cp1_cross_circuit_cohort_01/comparison.json').exists(),qualification='New known historical conv_layer_hls and tpu_like.small.ws physical inputs; CP1 fixed before outcomes. Different circuits, not route seeds. No new results until actual completion.')
    status['evidence']['cp1_prospective_cohort']='cp1_cross_circuit_cohort_01/plan.json'
    status['outstanding'].insert(1,'CP1 first prospective cohort conv_layer_hls/tpu_like.small.ws has4roles, single owner after corrected robot-p1. Keep historical success/failure inputs; full3.32GB physical provisioning waits for serial slot; actual native compatibility/outcomes unknown. No independent result claimed at registration.')
if (D/'robot_mechanism_composition_screen_01/completion.json').exists():
    screen=read(D/'robot_mechanism_composition_screen_01/completion.json')
    status['robot_mechanism_composition_screen']={k:v for k,v in screen.items() if k not in ['source_sha256','root_to_candidate_endpoints']}
    status['evidence']['robot_mechanism_composition_screen']='robot_mechanism_composition_screen_01/completion.json'
if (D/'robot_union_mechanism_01/launch.json').exists():
    status['robot_union_mechanism_plan']=dict(plan='robot_union_mechanism_01/plan.json',launch='robot_union_mechanism_01/launch.json',roles=3,connections=25,domain_nets=3,new_independent_results=0,qualification='Same-root development union and separate domain/release controls; queued after independent CP1 cohort, never changing CP1.')
    status['evidence']['robot_union_mechanism_plan']='robot_union_mechanism_01/plan.json'
if (D/'complete_BNN_cost_hierarchy_01/completion.json').exists():
    cost=read(D/'complete_BNN_cost_hierarchy_01/completion.json')
    status['complete_BNN_cost_hierarchy']={k:v for k,v in cost.items() if k not in ['arms','source_sha256']}
    status['evidence']['complete_BNN_cost_hierarchy']='complete_BNN_cost_hierarchy_01/completion.json'
if (D/'cp1_public_source_restoration_01/completion.json').exists():
    status['cp1_public_source_restoration']=dict(passed=True,receipt='cp1_public_source_restoration_01/completion.json',restored_dependency_files=1166,verified_bound_files=1289,actual_extension_import_and_fixed_admission=True,native_calls=0,CP1_changed=False)
    status['evidence']['cp1_public_source_restoration']='cp1_public_source_restoration_01/completion.json'
if (D/'BNN_engineering_paper_binding_11.json').exists():
    paper=read(D/'BNN_engineering_paper_binding_11.json');status['paper_pdf']=paper['pdf']
    status['evidence'].update(unified_paper='BNN_engineering_paper_binding_11.json',paper='BNN_engineering_paper_binding_11.json',domain_engineering_comparison='complete_BNN_domain_engineering_01/comparison.json')
    status['BNN_engineering_paper_update']=True
    status['outstanding']=[s for s in status['outstanding'] if not s.startswith(('Preserve actual BNN domain engineering','Close matched domain engineering cost','Six-page10'))]
    status['outstanding'].insert(0,'BNN domain engineering closed at9116.396s, same-role graphs/states/requests/native work/full endpoint vectors exact. Preserve active reduction and corrected input queues; no reruns of completed roles.')
    status['outstanding'].append('Original matched22.95% overhead remains. Domain same-role descriptive -637.916s/-6.540% is not an optimized pair ratio; native observer/PSS loss and overlap remain. Stable symmetric interleaved timing pending after priority distinct-input cohort.')
    status['outstanding'].append('Six-page11 sealed:32complete attempts and2scoped rows; one new complete engineering execution, zero new independent inputs. CP1 and prior paired figure unchanged.')
reduction_root=D/'portable_reduction_pair_01'
if (reduction_root/'admission.json').exists():
    admission=read(reduction_root/'admission.json')
    status['portable_reduction_actual']=dict(admission_passed=bool(admission.get('passed')),
        physical_inputs_rehashed_and_copied=admission.get('physical_inputs_rehashed_and_copied'),
        preparation_seconds_outside_measured_arms=admission.get('complete_preparation_seconds'),
        receipt='portable_reduction_pair_01/admission.json',native_input_observation=None)
    observed=reduction_root/'actual_native_input_observation_01.json'
    if observed.exists():
        status['portable_reduction_actual']['native_input_observation']=read(observed)
        status['evidence']['portable_reduction_input_observation']='portable_reduction_pair_01/actual_native_input_observation_01.json'
if (D/'BNN_interleaved_timing_01/launch.json').exists():
    status['BNN_interleaved_timing_plan']=dict(plan='BNN_interleaved_timing_01/plan.json',validation='BNN_interleaved_timing_01/validation.json',
        fixed_order=['native_0','domain_0','domain_1','native_1'],predecessor='robot_union_mechanism_01',new_independent_inputs=0,
        qualification='New balanced repeated complete measurements after priority independent-input and mechanism batches. Registered sources/rules fixed; no new timing outcome until actual receipts. Not a Goal stopping condition.')
    status['evidence']['BNN_interleaved_timing']='BNN_interleaved_timing_01/plan.json'
    status['outstanding']=[s.replace('Stable symmetric interleaved timing pending after priority distinct-input cohort.', 'Stable symmetric interleaved timing registered as N/D/D/N after robot union; preserve original priority cohorts and all attempts.') for s in status['outstanding']]
if (reduction_root/'plan.json').exists():
    workspace=Path(read(reduction_root/'plan.json')['workspace'])
    initial=workspace/'native/flow/resource_flow/initial'
    if (initial/'completion.json').exists() and read(initial/'completion.json').get('passed'):
        initial_done=read(initial/'completion.json');audit=read(initial/'runs/state/independent_audit.json')
        assert audit['audit']['passed']
        status['portable_reduction_actual']['native_initial_legal']=dict(receipt=str(initial/'completion.json'),CPD_ns=initial_done['full_precision_cpd_s']*1e9,
            wirelength=audit['physical_metrics']['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=audit['physical_metrics']['sb_pairs_used'],CB_sources=audit['physical_metrics']['cb_crossing_output_sources_used'],
            route_body_sha256=initial_done['route_body_sha256'],qualification='Legal fresh starting state only, not final method output or paired mechanism benefit.')
if status.get('portable_reduction_actual'):
    workspace=Path(read(reduction_root/'plan.json')['workspace'])
    resource_progress={}
    for arm in ['native','domain']:
        repair=workspace/arm/'flow/resource_flow/repair'
        if not (repair/'steps.json').exists():continue
        steps=read(repair/'steps.json')
        progress=dict(accepted_steps=len(steps),last_accepted_resources=None,last_accepted_CPD_ns=None,
            qualification='Resource trajectory only; complete method verification is a separate receipt, not inferred here.')
        if steps:
            last=steps[-1];role=last['roles'][last['accepted_role']]
            progress.update(last_accepted_resources=role['resources'],last_accepted_CPD_ns=role['cpd_s']*1e9)
        resource_progress[arm]=progress
    status['portable_reduction_actual']['resource_progress']=resource_progress
    first=reduction_root/'first_native_resource_acceptance_01.json'
    if first.exists():
        status['portable_reduction_actual']['first_native_resource_acceptance']={k:v for k,v in read(first).items() if k!='source_sha256'}
        status['evidence']['reduction_first_native_resource']='portable_reduction_pair_01/first_native_resource_acceptance_01.json'
reconciliation=D/'execution_reconciliation_20261116_01/completion.json'
if reconciliation.exists():
    status['execution_reconciliation_20261116']=read(reconciliation)
    status['confirmation_release_cp1r1']=read(D/'confirmation_release_cp1r1_01/completion.json')
    status['evidence'].update(proc_race_reconciliation=str(reconciliation),CP1r1='confirmation_release_cp1r1_01/completion.json',CP1r1_cohort='cp1r1_cross_circuit_cohort_01/plan.json',robot_union_current='robot_union_mechanism_02/plan.json',BNN_interleaved_current='BNN_interleaved_timing_02/plan.json')
    status['outstanding']=[
        'Continue actual CP1r1 conv_hls/tpu_ws native/domain cohort, then robot_union_mechanism_02 and BNN_interleaved_timing_02. Old owners are terminal; only new registered owners may execute these previously unexecuted roles.',
        'Five interrupted development arms have legal initial routes but no complete-method output. Preserve partial states, all measured failure costs and missing supervision receipts. Never count them as routing or scientific negatives, or use partial terminal metrics in whole-flow comparisons.',
        'CP1 and dev03 remain immutable. CP1r1 only changes vanished-proc handling and release seals; fixed algorithm/rules and original prospective circuit selection preserved. New complete native evidence is pending.',
        'Original robot-p1/domain never executed. Revisit the interrupted reduction/CLSTM/robot-p1 development flows under a separately registered recovery/new-version experiment after independent confirmation, preserving prior attempts and distinguishing recovered costs from complete fresh costs. Do not retry original output directories.',
        'Integrate interrupted attempts and corrected input-loading evidence into six-page main table and supplement, then publish reviewed source/PDF and exact evidence without altering local HEAD/index or main.',
        'Do not stop the research Goal for queue/matrix/publication completion or ordinary negative results. No fixed date or total-call stop.']
    if (D/'proc_race_paper_binding_12.json').exists():
        paper=read(D/'proc_race_paper_binding_12.json');status['paper_pdf']=paper['pdf'];status['paper_pages']=6
if (D/'CP1r1_packaging_failure_01/completion.json').exists():
    status['CP1r1_packaging_failure']=read(D/'CP1r1_packaging_failure_01/completion.json')
    status['confirmation_release_cp1r2']=read(D/'confirmation_release_cp1r2_01/completion.json')
    status['outstanding'][0]='Continue robot_union_mechanism_02 already running; CP1r2 cohort waits for shared serial slot, BNN_interleaved_timing_02 waits for robot union then the same slot. Verify actual lock holder and do not overlap. Original CP1r1 four arms failed to launch VPR (guard mode126); keep attempts, no scientific-negative claim.'
    status['outstanding'][2]='CP1/dev03/CP1r1 remain immutable. CP1r2 fixes vanished-proc reads and preserves/admission-checks executable guard mode; real guard tests pass in original and public-source-restored runtime. Fixed algorithms, rules and prospective circuits unchanged; independent complete outcomes pending.'
    status['evidence'].update(CP1r1_packaging='CP1r1_packaging_failure_01/completion.json',CP1r2='confirmation_release_cp1r2_01/completion.json',CP1r2_reproduction='confirmation_release_cp1r2_01/public_source_reconstruction.json',CP1r2_cohort='cp1r2_cross_circuit_cohort_01/plan.json')
    if (D/'runtime_recovery_paper_binding_13.json').exists():
        paper=read(D/'runtime_recovery_paper_binding_13.json');status['paper_pdf']=paper['pdf'];status['paper_pages']=6
if (D/'robot_union_verification_recovery_01/plan.json').exists():
    status['outstanding'][0]='CP1r2 cohort is running. Robot union02 native work completed, but original readonly verifier misread compact schemas; no-native verification_recovery01 waits for serial lock. BNN_interleaved_timing03 is the sole pending measurement owner after that audit;01/02 never executed. No duplicate native work.'
    status['evidence'].update(robot_union_readonly_recovery='robot_union_verification_recovery_01/plan.json',BNN_interleaved_current='BNN_interleaved_timing_03/plan.json')
native_confirmation=D/'cp1r2_cross_circuit_cohort_01/conv_hls_native_evidence_01/evidence.json'
if native_confirmation.exists():
    status['first_complete_CP1r2_native_arm']=read(native_confirmation)
    status['evidence']['first_complete_CP1r2_native']='cp1r2_cross_circuit_cohort_01/conv_hls_native_evidence_01/evidence.json'
pair=D/'cp1r2_cross_circuit_cohort_01/conv_hls_comparison.json'
if pair.exists():
    v=read(pair)
    status['first_complete_CP1r2_pair']=dict(passed=v['passed'],verified_legal_roles=v['verified_legal_roles'],matched_initial=v['matched_comparison']['matched_initial_route_and_full_vector'],results={a:{k:r[k] for k in ['status','quality','complete_seconds','sampled_PSS_kib','missing_memory_observations']} for a,r in v['results'].items()},endpoint_summary={k:x for k,x in v['matched_comparison']['endpoint_changes'].items() if k!='changes'},qualification='One distinct known input prospectively confirmed as fixed-menu no-op. No positive mechanism or statistical speedup claim.')
    status['evidence']['first_complete_CP1r2_pair']='cp1r2_cross_circuit_cohort_01/conv_hls_comparison.json'
if (D/'CP1r2_pair_paper_binding_14.json').exists():
    paper=read(D/'CP1r2_pair_paper_binding_14.json');status['paper_pdf']=paper['pdf'];status['paper_pages']=6
if (D/'robot_owner_reentry_audit_01/pending_observation.json').exists():
    status['robot_owner_reentry_pending_audit']=read(D/'robot_owner_reentry_audit_01/pending_observation.json')
    status['evidence']['robot_owner_reentry_audit']='robot_owner_reentry_audit_01/plan.json'
    status['outstanding'].append('Readonly owner-reentry audit01 waits for serial slot: four robot-p1 native owner commits observed, but exact existing reload-vector comparison remains pending; full/rounded CPD manifest mismatch is an additional latent check failure. Keep frozenCP1r2 immutable and require a separate corrected version only after actual audit. No rerouting or original receipt rewrite.')
precision_patch=D/'observation_precision_patch_01/preparation.json'
if precision_patch.exists():
    status['observation_precision_patch']=read(precision_patch)
    status['evidence']['observation_precision_patch']='observation_precision_patch_01/preparation.json'
    status['outstanding'].append('Precision patch01 stages both observation workers with display normalization plus exact full-vector identity and bound source vectors; not installed. Await actual readonly trace audit before new runtime packaging/registration. Do not mutate CP1r2 or repeat native work.')
tpu_timeout=D/'cp1r2_cross_circuit_cohort_01/tpu_ws_native_timeout_evidence_01/evidence.json'
if tpu_timeout.exists():
    v=read(tpu_timeout)
    status['CP1r2_tpu_native_timeout']={k:x for k,x in v.items() if k not in ['copied_receipts','registered_input_identity']}
    status['evidence']['CP1r2_tpu_native_timeout']='cp1r2_cross_circuit_cohort_01/tpu_ws_native_timeout_evidence_01/evidence.json'
if (D/'robot_owner_reentry_audit_02/plan.json').exists():
    status['evidence']['robot_owner_reentry_audit']='robot_owner_reentry_audit_02/plan.json'
    status['evidence']['observation_precision_patch']='observation_precision_patch_02/preparation.json'
    status['observation_precision_patch']=read(D/'observation_precision_patch_02/preparation.json')
    status['observation_format_regression']=read(D/'observation_timing_identity_validation_02/completion.json')
    status['outstanding']=[x.replace('audit01','audit02').replace('patch01','patch02') for x in status['outstanding']]
    status['outstanding'].append('Readonly owner audit01 superseded before execution after exact live wait-channel/no-child check: JSON endpoint lists and parser tuples need semantic canonicalization. Audit02 and precision patch02 use helperv2; no order/numeric relaxation. Original01scripts/registration and cancellation receipt retained; all native runs unchanged.')
empty_query_patch=D/'empty_query_patch_01/preparation.json'
if empty_query_patch.exists():
    status['empty_query_development_patch']=read(empty_query_patch)
    status['evidence']['empty_query_development_patch']='empty_query_patch_01/preparation.json'
    status['outstanding'].append('Empty-query patch01 stages exact empty protected/exchange exits after upstream digest/state checks, with graph argument/driver binding guards. Nonempty bodies unchanged; no runtime installed or savings measured. Validate completed empty+nonempty fixtures under serial lock, then new-version matched native/domain whole controls; do not alter fixed BNN timing03.')
if (D/'empty_query_patch_validation_01/plan.json').exists():
    status['evidence']['empty_query_actual_replay_queue']='empty_query_patch_validation_01/plan.json'
    status['outstanding'].append('Actual empty/nonempty fixture replay is now registered after BNN timing03; queue performs existing-input digest/state guards under serial lock, forbids mapping/query/native processes for empty branch, and stops nonempty execution at original mapping boundary. This tests branch behavior only, not complete method equivalence or measured savings. No completed routes or queries repeated.')
closed_cohort=D/'cp1r2_cross_circuit_cohort_01/terminal_evidence_01/completion.json'
if closed_cohort.exists():
    status['closed_CP1r2_cohort']={k:v for k,v in read(closed_cohort).items() if k!='source_sha256'}
    union=read(D/'robot_union_mechanism_02/verification_v2.json')
    status['verified_robot_union']=dict(passed=union['passed'],shared_imported_seconds=union['complete_imported_three_arm_seconds'],
        outcomes={role:dict(status=r['status'],quality=r['quality'],native_core_seconds=r['native_core_seconds'],
            endpoint_summary=None if not r.get('endpoint_comparison') else {k:v for k,v in r['endpoint_comparison'].items() if k!='changes'},
            resource_accepted=r.get('resource_policy_decision',{}).get('accepted'),committed=False) for role,r in union['outcomes'].items()})
    status['verified_robot_owner_reentry']={k:v for k,v in read(D/'robot_owner_reentry_audit_02/completion.json').items() if k!='source_sha256'}
    status['evidence'].update(closed_CP1r2_cohort=str(closed_cohort),verified_robot_union='robot_union_mechanism_02/verification_v2.json',verified_owner_reentry='robot_owner_reentry_audit_02/completion.json')
    status['outstanding']=[
        'Continue sole BNN_interleaved_timing03 owner in original N/D/D/N order; check real PID/start ticks and actual receipts. No role repeated, no runtime/config/algorithm changes. Empty-query fixture validation waits for its terminal receipt and the shared serial slot.',
        'CP1r2 cohort closed: conv_hls legal fixed-menu no-op pair, TPU N/D fixed 1800-s initial execution timeouts. Preserve all four original roles/costs; no timeout quality, infeasibility or domain delta inferred.',
        'Verified fixed-scope robot union: native legal but CB cap exceeded; no-release exact rollback; domain+release legal resource-accepted candidate,32 setup regressions. No actor commit or complete-controller claim. Four native robot-p1 owner commits/reentries and exact existing reload STA verified only on partial development path.',
        'Precision patch02 actual existing-vector identity now validated by audit02; stage a separately versioned runtime/recovery adapter while preserving original root envelopes, budgets and legal archive. No mutation of CP1r2 or repeated completed native prefixes; recovered suffix costs remain distinct from fresh full cost.',
        'Empty-query patch remains staged/unmeasured. Existing-fixture validation is queued after BNN03; require new-version symmetric whole-flow controls before savings claims. Nonempty replay stops at original graph boundary, not a full equivalence proof.',
        'Broaden genuinely different physical inputs and applicable architectures with prospective fixed rules, retaining no-cut/no-gain/degradation/failure outcomes. Develop crossing-redundancy/capacity/slack mechanism selection beyond a single BNN state.',
        'Publish reviewed six-page source/PDF and actual evidence without changing local HEAD/index or main. Goal stays active; cohort/matrix/publication completion and ordinary negatives do not stop research.']
    if (D/'cohort_mechanism_paper_binding_15.json').exists():
        paper=read(D/'cohort_mechanism_paper_binding_15.json');status['paper_pdf']=paper['pdf'];status['paper_pages']=6
if (D/'confirmation_release_cp1r3_01/plan.json').exists():
    status['evidence']['precision_release_preparation']='confirmation_release_cp1r3_01/plan.json'
    status['outstanding'].append('Precision-only CP1r3 source preparation is registered after the existing empty-query replay, then shared serial lock. It binds actual exact reload audit02, stages only two corrected observation workers plus helper, preserves selectors/root/acceptance/terminal rules and guard modes, and checks imports/guard without VPR calls. Not yet packaged or executed; no public reconstruction/new confirmation claimed. CP1r2 and current BNN03 stay unchanged.')
if (D/'robot_p1_prefix_recovery_01/plan.json').exists():
    status['evidence']['robot_prefix_recovery']='robot_p1_prefix_recovery_01/plan.json'
    status['robot_prefix_recovery_metadata_validation']=read(D/'robot_p1_prefix_recovery_01/metadata_validation.json')
    status['outstanding'].append('Robot-p1/native recovery adapter is implemented and registered after CP1r3 preparation and the serial lock. Metadata/24negative guards and exact reversible controller transforms pass. Heavy original-root/archive/trace proof precedes any new work; seven accepted prefix states, legal rejected archive and original envelopes are retained. Completed round7 native request/STA is consumed, not repeated. Continue through resource closure, terminal handoff and timing only after actual admission. Suffix wall/PSS remains separate from original failed attempt; no fresh full cost or confirmation claim. Other interrupted development cases and original unexecuted robot domain require separately verified adapters/registrations.')
if (D/'mechanism_trigger_paper_binding_16.json').exists():
    paper=read(D/'mechanism_trigger_paper_binding_16.json');status['paper_pdf']=paper['pdf'];status['paper_pages']=6
    status['mechanism_selection_metadata']=read(D/'mechanism_selection_evidence_01/completion.json')
    status['release_coverage_metadata']=read(D/'release_coverage_01/completion.json')
    status['mechanism_triage_development']=read(D/'mechanism_triage_validation_02/completion.json')
    status['evidence'].update(mechanism_input_context='mechanism_selection_evidence_01/completion.json',release_event_coverage='release_coverage_01/completion.json',mechanism_triage='mechanism_triage_validation_02/completion.json',current_paper='mechanism_trigger_paper_binding_16.json')
    status['outstanding'].append('Retrospective10configuration/9declared-physical-input metadata matrix shows initial sharing eligibility is not gain prediction; identical48SB-only candidate records need the distinct1.00/1.02CPD budget context. Every BNN guided resource role is audited(9roles,0release events); robot has3roles/5events. Draft objective-specific triage separates resource owner scopes from positive capacity-conflicting timing witnesses and per-net actual-failure release; it is uninstalled and no savings/generalization is proved. Keep fixed confirmations unchanged and validate any integrated new mechanism rule prospectively on genuinely different inputs.')
if (D/'independent_input_candidates_02/completion.json').exists():
    status['next_independent_circuit_candidates']=read(D/'independent_input_candidates_02/completion.json')
    status['evidence']['next_independent_circuit_candidates']='independent_input_candidates_02/completion.json'
    status['outstanding'].append('Two distinct known historical circuit/layout candidates are metadata-bound without QoR-based selection: LSTM seed21/p0 Hybrid-O n125 and DLA-like.small seed21/p0 Hybrid-O n100. Actual packed/place provenance metadata agrees and both require merge_constant_generators off. Declared netlist hashes differ from all10context-matrix inputs. No raw physical rehash/provisioning or registered execution yet; perform these under the serial lock, freeze new CP1r3 configs before outcomes, retain admission failures, count new actual roots correctly, and do not label different device sizes as new architecture families or known inputs as unseen.')
if (D/'cp1r3_distinct_input_cohort_01/protocol.json').exists():
    registration_root=D/'cp1r3_distinct_input_cohort_01'
    status['CP1r3_distinct_input_protocol']=dict(protocol='cp1r3_distinct_input_cohort_01/protocol.json',selected_inputs=3,registered_roles=6,
        active_configs_sealed=(registration_root/'plan.json').exists(),actual_preflight_passed=(read(registration_root/'preflight.json')['passed'] if (registration_root/'preflight.json').exists() else False),
        native_execution_not_inferred_from_registration=True,placement_control=read(registration_root/'placement_independence_01.json'))
    status['evidence'].update(next_independent_confirmation_protocol='cp1r3_distinct_input_cohort_01/protocol.json',SB_actual_placement_identity='cp1r3_distinct_input_cohort_01/placement_independence_01.json',next_cohort_metadata_checks='cp1r3_cohort_administration_validation_01/completion.json')
    status['outstanding']=[x for x in status['outstanding'] if not x.startswith('Two distinct known historical circuit/layout candidates are metadata-bound')]
    status['outstanding'].append('Next CP1r3 protocol is registered after original robot recovery: LSTM/DLA-like.small distinct known circuits plus eltwise SB-only actual alternate-placement control(1882of1883blocks changed against older table; same declared graph/packing). Three source inputs/sixroles; no new QoR yet. Actual CP1r3 release/configs, source+wheel reconstruction/guard/import/checker, placement/byte provisioning and per-input fresh roots are required under serial lock before confirmation. Freeze actual plan before first native; no triage/empty-query patch, outcome-selected replacement or old tree import. Keep input-admission/timeout/no-op/worse roles and all costs distinct. Do not claim three new circuits, unseen inputs, architecture causality or statistical speedup.')
if (D/'interrupted_stage_reconciliation_01/plan.json').exists():
    status['interrupted_stage_reconciliation']=dict(plan='interrupted_stage_reconciliation_01/plan.json',inventory='interrupted_stage_reconciliation_01/inventory.json',audit_complete=(D/'interrupted_stage_reconciliation_01/completion.json').exists(),new_native_calls=0,adoption_implemented=False)
    status['evidence']['remaining_interrupted_stage_inventory']='interrupted_stage_reconciliation_01/inventory.json'
    status['outstanding'].append('Four remaining CLSTM/reduction interrupted arms now have an actual stage inventory and registered readonly audit behind the distinct-input cohort. CLSTM/native resource/terminal/handoff are already complete; its timing native+audit and reduction/domain native+physical/domain audits must be preserved. reduction/native has raw GNU exit0/FULL/native COMPLETE269 but no worker completion: exact byte/source/STA audit is required; do not replay queries or fabricate completion. Empty candidate STA directories contain no result. No adoption adapter/new whole-method quality/cold cost yet; retain original failed costs and root/budget/legal archives.')
if (D/'interrupted_flow_recovery_01/protocol.json').exists():
    status['interrupted_full_flow_dispatch']=dict(protocol='interrupted_flow_recovery_01/protocol.json',validation='interrupted_flow_recovery_01/validation.json',registered_arms=4,original_roots_and_archives_retained=True,actual_audit_and_suffix_results_pending=not (D/'interrupted_flow_recovery_01/results.json').exists(),fresh_complete_cost_available=False,new_independent_inputs=0)
    status['evidence']['remaining_interrupted_full_flow_dispatch']='interrupted_flow_recovery_01/protocol.json'
    status['outstanding']=[x for x in status['outstanding'] if not x.startswith('Four remaining CLSTM/reduction interrupted arms now')]
    status['outstanding'].append('Four CLSTM/reduction full-flow prefix recoveries are now implemented and queued after their readonly stage audit. Exact source transforms, actual4role/root/cut-point metadata and31negative guards pass; tiny stage-side-effect fixtures pass5checks/20guards. Per-case actual serial audit hashes and CP1r3 package/unchanged algorithm admission remain mandatory before new native work. CLSTM/native skips closed resource/terminal/handoff and preserves its original timing portfolio/query work; others resume resource prefixes. No new recovered result, independent input or cold whole-cost yet. All failures and old costs retained separately; candidate STA/audit failures cannot be promoted to a complete recovery.')
if (D/'BNN_timing03_native0_receipt_02/completion.json').exists():
    receipt=read(D/'BNN_timing03_native0_receipt_02/completion.json')
    status['BNN_timing03_first_complete_arm']={k:receipt[k] for k in ['arm','quality','complete_command_seconds','sampled_tree_PSS_peak_kib','sampled_tree_PSS_peak_GiB','missing_memory_observations','observer_CPU_seconds','resource_commits','timing_commits','coarse_same_role_CPD_and_resources_equal','exact_same_role_trajectory_requests_native_work_and_graph_payload_equivalence','own_root_endpoint_summary','paired_domain_over_native_ratio','measured_identities_rechecked','completion_timestamps']}
    status['BNN_timing03_first_complete_arm']['scope']='Historical first-arm snapshot before original batch finish; current owner table is authoritative for active case.'
    status['evidence']['BNN_timing03_first_complete_arm']='BNN_timing03_native0_receipt_02/completion.json'
    status['outstanding'].append('BNN03 native_0 completed at14:12UTC and existing full verifier passed14:13UTC:13.228145690ns,2059631wire/82SB/5062CB,7329.044554s,PSS11.060657GiB,22missing memory samples;157recorded identities rechecked dead. Queue has already advanced to domain_0; never infer active case from native_0 old timing checkpoint. This is one known-input repeat; exact same-role graph/trajectory/request/native-work and own-root/paired endpoint comparisons await original four-role finish. No optimized N/D ratio or statistical speedup yet; do not overwrite original22.95percent paired overhead or add a new independent main-table row.')
if (D/'interrupted_entrypoint_startup_01/completion.json').exists():
    status['recovery_entrypoint_startup']=dict(receipt='interrupted_entrypoint_startup_01/completion.json',passed=read(D/'interrupted_entrypoint_startup_01/completion.json')['passed'],probes=7,native_calls=0,actual_CP1r3_package_or_recovery_execution=False)
    status['evidence']['recovery_entrypoint_startup']='interrupted_entrypoint_startup_01/completion.json'
if (D/'confirmation_priority_handoff_02/completion.json').exists():
    handoff=read(D/'confirmation_priority_handoff_02/completion.json');priority=read(D/'confirmation_priority_handoff_02/plan.json')
    status['confirmation_priority_handoff']=dict(receipt='confirmation_priority_handoff_02/completion.json',validation='confirmation_priority_handoff_02/validation.json',applied=handoff['passed'],schedule=[s['batch'] for s in priority['stages']],input_and_fixed_algorithm_rules_unchanged=True,old_cancellations_are_not_experiment_failures=True)
    status['evidence']['confirmation_priority_handoff']='confirmation_priority_handoff_02/completion.json'
    status['active_schedule_order']=['BNN_interleaved_timing_03',*[n['batch'] for n in priority['stages']]]
    status['superseded_unexecuted_queue_owners']=[dict(batch=n['batch'],registration=str(Path(n['old_queue'])/'registration.json'),receipt=str(Path(n['old_queue'])/'completion.json'),pid=n['pid'],start_ticks=n['start_ticks'],method_executed=False) for n in priority['stages']]
    predecessors={n['batch']:n['predecessor'] for n in priority['stages']}
    for owner in owners:
        if owner['batch'] in predecessors and owner['queue_generation']=='priority_02':
            owner['actual_predecessor_queue']=predecessors[owner['batch']]
            if owner['phase_status'].startswith('waiting'):owner['effective_wait']='priority_dependency: '+str(Path(predecessors[owner['batch']]).parent.name)
    remove_prefixes=['Continue sole BNN_interleaved_timing03','Precision-only CP1r3 source preparation is registered','Robot-p1/native recovery adapter is implemented','Next CP1r3 protocol is registered','Four CLSTM/reduction full-flow prefix recoveries','Empty-query patch remains staged']
    status['outstanding']=[x for x in status['outstanding'] if not any(x.startswith(prefix) for prefix in remove_prefixes)]
    status['outstanding'][:0]=[
        'Preserve active BNN03 N/D/D/N without interruption or source/rule change; native0 is already complete. Use actual current queue case/PID/start_ticks and whole receipts. Complete all4 and exact same-role graph/request/native work/root/endpoints before optimized ratios; never splice components or repeat an arm.',
        'Priority02: after the current balanced BNN batch, package CP1r3, then run the original preregistered3inputs/6roles immediately before any development recovery. Freeze actual config/release/source/public reconstruction and physical byte admission before first native. LSTM/DLA-like.small are distinct known circuits; eltwise on known SB-only family is an actual alternate placement, not a new circuit or new architecture sample. No outcomes yet.',
        'After fixed confirmation, run the registered four-arm readonly source/byte/full-request/FULL/STA/endpoint/physical audit. reduction/native raw GNU exit0/COMPLETE269 and running manifest must be independently reconciled; never fabricate old completion or repeat completed native queries. Only independently verified actual stages may be adopted; new candidate audits/STA and all new commands retain their own cost.',
        'Then continue robot-p1 and the4interrupted flows only through their original-root/archive/acceptance gates. Preserve all old failure/timeout/negative costs; suffix costs remain separate from cold complete cost and cannot become a complete N/D ratio. Empty-query fixture replay is last and its patch remains excluded from frozen confirmation.']
if (D/'interrupted_complete_request_audit_01/completion.json').exists():
    request_scope=read(D/'interrupted_complete_request_audit_01/completion.json')
    status['interrupted_complete_request_scope']=dict(receipt='interrupted_complete_request_audit_01/completion.json',passed=request_scope['passed'],registered_roles=4,matched_queries=request_scope['exactly_matched_registered_queries'],native_attempt_rows=request_scope['native_attempt_rows'],complete_readonly_seconds=request_scope['complete_readonly_seconds'],full_stage_admission_passed=False,new_native_calls=0)
    status['evidence']['interrupted_complete_request_scope']='interrupted_complete_request_audit_01/completion.json'
if (D/'interrupted_recovery_outcomes_01/DRAFT_STATUS.json').exists():
    status['deferred_unregistered_recovery_outcome_verifier']=read(D/'interrupted_recovery_outcomes_01/DRAFT_STATUS.json')
if (D/'input_seed_paper_binding_17.json').exists():
    paper=read(D/'input_seed_paper_binding_17.json');status['paper_pdf']=paper['pdf'];status['paper_pages']=6
    status['evidence'].update(current_paper='input_seed_paper_binding_17.json',actual_router_seed_provenance='input_seed_paper_evidence_17/seed_provenance.json')
    status['paper_router_seed_correction']=dict(command_manifests=8,BNN=11,Robot_SDC_upstream_s23=11,CP1r2_conv_hls=21,CP1r2_tpu_ws=21,new_independent_inputs=0,new_full_method_results=0,fresh_physical_byte_audit=False,quantitative_rows_unchanged=43)
if (D/'BNN_timing03_domain0_progress_01/completion.json').exists():
    status['evidence']['BNN_timing03_domain0_historical_phase_snapshot']='BNN_timing03_domain0_progress_01/completion.json'
if (D/'BNN_timing03_domain0_receipt_01/completion.json').exists():
    receipt=read(D/'BNN_timing03_domain0_receipt_01/completion.json')
    status['BNN_timing03_first_complete_domain']={k:receipt[k] for k in ['arm','quality','complete_command_seconds','sampled_tree_PSS_peak_kib','sampled_tree_PSS_peak_GiB','missing_memory_observations','observer_CPU_seconds','resource_commits','timing_commits','coarse_same_role_CPD_and_resources_equal','exact_same_role_trajectory_requests_native_work_and_graph_payload_equivalence','own_root_endpoint_summary','paired_domain_over_native_ratio','measured_identities_rechecked','completion_timestamps']}
    status['BNN_timing03_first_complete_domain']['scope']='Historical second-arm snapshot; original full verifier passed, current owner table is authoritative for active case. Four-role equivalence/matching and descriptive paired costs remain pending.'
    status['evidence']['BNN_timing03_first_complete_domain']='BNN_timing03_domain0_receipt_01/completion.json'
    status['outstanding'].append('BNN03 domain_0 independently verified:13.228145690ns,2061417wire/43SB/5060CB,9146.351492s,PSS11.063066GiB,28missing samples;174measured identities rechecked dead. Original queue advanced to domain_1. Two of four known-input measurement roles complete; no new independent input, CP1r3result, optimized paired ratio or statistical speedup. Reuse original verifier. Exact same-role trajectory/request/native-work/sixgraph and full own-root/paired endpoint comparisons remain original four-role finish gates; original22.95percent overhead and paper17 claims remain unchanged.')
if (D/'BNN_timing03_domain1_receipt_01/completion.json').exists():
    receipt=read(D/'BNN_timing03_domain1_receipt_01/completion.json')
    status['BNN_timing03_second_complete_domain']=receipt
    status['BNN_timing03_second_complete_domain']['scope']='Historical third-arm snapshot; original full verifier passed. Current owner table identifies the last native arm. Four-role trajectories, requests, graph bytes, roots and endpoints must match before paired ratios.'
    status['evidence']['BNN_timing03_second_complete_domain']='BNN_timing03_domain1_receipt_01/completion.json'
    status['evidence']['BNN_timing03_second_domain_claim_scope']='BNN_timing03_domain1_claim_binding_01.json'

if (D/'sharing_prior_art_paper_binding_18.json').exists():
    paper=read(D/'sharing_prior_art_paper_binding_18.json');status['paper_pdf']=paper['pdf'];status['paper_pages']=6
    status['evidence'].update(current_paper='sharing_prior_art_paper_binding_18.json',sharing_prior_art='sharing_prior_art_paper_evidence_18/sources.json',contribution_and_attribution_map='sharing_prior_art_paper_evidence_18/contribution_comparison.md')
    status['paper_sharing_prior_art_scope']=dict(pages=6,quantitative_rows_unchanged=43,references_unchanged=9,new_independent_inputs=0,new_native_calls=0,external_router_reproduced=False,cross_paper_numeric_rank=False,new_benefit_claims=0)
if (D/'BNN_timing03_balanced_receipt_01/completion.json').exists():
    balanced=read(D/'BNN_timing03_balanced_receipt_01/completion.json')
    status['BNN_timing03_balanced_complete']={k:balanced[k] for k in [
        'paired_cost_observation_available','registered_order','rows','pairs',
        'pair_domain_over_native_ratios','native_mean_seconds','domain_mean_seconds',
        'ratio_of_arm_means','mean_of_pair_ratios','independent_new_inputs','goal_status']}
    status['evidence'].update(BNN_timing03_balanced_complete='BNN_timing03_balanced_receipt_01/completion.json',
                              BNN_timing03_balanced_claim_scope='BNN_timing03_balanced_claim_binding_01.json')
    for key in ['BNN_timing03_first_complete_arm','BNN_timing03_first_complete_domain','BNN_timing03_second_complete_domain']:
        if key in status:
            status[key]['scope']='Historical intermediate receipt; superseded for batch matching by BNN_timing03_balanced_complete. Original measurement remains unchanged.'
    status['outstanding']=[s for s in status['outstanding'] if not s.startswith((
        'Preserve active BNN03','BNN03 native_0','BNN03 domain_0','Priority02: after the current balanced BNN batch'))]
    status['outstanding'].insert(0,'BNN03 all four whole commands and original byte/trajectory/request/native-work/environment/root/full-endpoint matching passed. Reuse comparison and paired costs; no more BNN local repeats. Proceed with the actual Priority02 CP1r3 three-input/six-role owner, then the four-arm readonly admission and registered recoveries. Keep paper18 prior-art/contribution scope and all prior failures; same input repeats add zero independent evidence.')
    package=D/'confirmation_release_cp1r3_01/completion.json'
    if package.exists():
        status['actual_CP1r3_precision_package']=read(package)
        status['evidence']['actual_CP1r3_precision_package']='confirmation_release_cp1r3_01/completion.json'
    cohort=D/'cp1r3_distinct_input_cohort_01'
    if (cohort/'preflight.json').exists():
        status['actual_CP1r3_activation_preflight']=read(cohort/'preflight.json')
        status['evidence']['actual_CP1r3_activation_preflight']='cp1r3_distinct_input_cohort_01/preflight.json'
        status['actual_CP1r3_preparation_costs']={p.name:read(p) for p in [cohort/'activation_cost.json',*cohort.glob('*_provisioning_cost.json')] if p.exists()}
    phase_path=cohort/'queue_priority_02/status.json'
    phase=read(phase_path)
    if phase.get('case') and phase.get('status')=='running_confirmation_arm':
        case=Path(phase['case']);initial=case/'flow/resource_flow/initial'
        proof=initial/'completion.json';audit=initial/'physical_audit.json'
        if proof.exists() and audit.exists():
            verified=read(proof);physical=read(audit)
            if verified['passed'] and physical['passed']:
                physical_row=physical['legal'][0]
                manifest=initial/'runs/state/manifest.json'
                graph=case/'flow/resource_flow/joint_graph_indexes/completion.json'
                status['actual_CP1r3_live_initial_state']=dict(
                    input=phase['input'],arm=phase['arm'],case=str(case),
                    status=verified['status'],initial_route_imported=verified['initial_route_imported'],
                    CPD_ns=verified['full_precision_cpd_s']*1e9,
                    wirelength=physical_row['physical_metrics']['planar_wirelength_excluding_sb_half_nodes'],
                    SB_pairs=physical_row['physical_metrics']['sb_pairs_used'],
                    CB_sources=physical_row['physical_metrics']['cb_crossing_output_sources_used'],
                    route_body_sha256=verified['route_body_sha256'],
                    initial_native_command_seconds=read(manifest)['wall_seconds'],
                    graph_build_seconds=read(graph)['shared_complete_build_seconds'],
                    measured_whole_algorithm_seconds=None,complete_confirmation_passed=False,
                    source_sha256={str(p):sha(p) for p in [proof,audit,manifest,graph]},
                    qualification='Original fresh initial-state gate only; not terminal method quality, paired confirmation or an application-SDC claim. Component times are not summed into a complete cost.')
        repair=case/'flow/resource_flow/repair';checkpoint=repair/'current_state.json'
        if checkpoint.exists() and (repair/'steps.json').exists():
            before=read(checkpoint);steps=read(repair/'steps.json');after=read(checkpoint)
            if before==after and steps and after['accepted_steps']==len(steps):
                step=steps[-1]
                if step['committed_evaluation']==after['state']:
                    tx=Path(step['transaction']);role=step['accepted_role']
                    completed=tx/'completion.json';decisions=tx/(role+'_decisions.json')
                    evaluation=Path(after['state'])/'completion.json'
                    done=read(completed);decision=read(decisions);checked=read(evaluation)
                    evaluation_evidence=evaluation_receipt_evidence(evaluation.parent)
                    if done['passed'] and evaluation_evidence['passed'] and decision['resources_under_timing']['accepted']:
                        status['actual_CP1r3_live_resource_checkpoint']=dict(
                            input=phase['input'],arm=phase['arm'],accepted_steps=len(steps),
                            round=step['round'],state=after['state'],accepted_role=role,
                            mechanism=step.get('mechanism','current_resource_rank_window'),
                            CPD_ns=checked['full_precision_cpd_s']*1e9,
                            resources=step['roles'][role]['resources'],
                            latest_endpoint_comparison={k:v for k,v in decision['strict']['comparison'].items() if k!='changes'},
                            latest_complete_transaction_seconds=done['complete_orchestrator_seconds'],
                            evaluation_evidence=evaluation_evidence,
                            complete_algorithm_cost=None,complete_confirmation_passed=False,
                            source_sha256={str(p):sha(p) for p in [completed,decisions,evaluation]},
                            qualification='Consistent original accepted resource checkpoint with original FULL/STA/physical checks. Not terminal method quality or a paired confirmation. Latest transaction cost is nested, not assembled into a whole.')
        attempts_path=repair/'attempts.json'
        if attempts_path.exists():
            attempts=read(attempts_path)
            if attempts:
                latest=attempts[-1];tx=Path(latest['transaction']);completion=tx/'completion.json'
                if completion.exists():
                    done=read(completion);roles={};receipts=[completion]
                    for role,observed in done.get('roles',{}).items():
                        entry={k:observed.get(k) for k in ['status','scope','resources','cpd_s','native_core_seconds',
                            'native_calls_new','native_reused','reused_FULL_STA','evaluation']}
                        entry['policies']=observed.get('policies',{})
                        if observed.get('evaluation'):
                            prior_or_new_evaluation=Path(observed['evaluation'])/'completion.json'
                            if prior_or_new_evaluation.exists():
                                receipts.append(prior_or_new_evaluation)
                                entry['evaluation_evidence']=evaluation_receipt_evidence(prior_or_new_evaluation.parent)
                        decisions=tx/(role+'_decisions.json')
                        if decisions.exists():
                            decision=read(decisions);receipts.append(decisions)
                            comparison=decision.get('strict',{}).get('comparison')
                            if comparison is not None:entry['endpoint_comparison']={k:v for k,v in comparison.items() if k!='changes'}
                        roles[role]=entry
                    status['actual_CP1r3_latest_completed_resource_attempt']=dict(
                        input=phase['input'],arm=phase['arm'],round=latest['round'],
                        candidate_rank=latest['candidate_rank'],transaction=str(tx),
                        mechanism=latest.get('mechanism','current_resource_rank_window'),
                        transaction_workflow_passed=done.get('passed'),
                        accepted=latest.get('accepted_role') is not None,accepted_role=latest.get('accepted_role'),
                        complete_transaction_seconds=done.get('complete_orchestrator_seconds'),
                        roles=roles,error=done.get('error'),complete_algorithm_cost=None,
                        source_sha256={str(p):sha(p) for p in receipts},
                        qualification='Latest completed original attempt, including policy rejection or execution failure; separate from last accepted checkpoint. No missing quality or cost is invented. Transaction/core costs are not whole algorithm time.')
if (D/'balanced_cost_paper_binding_19.json').exists():
    paper=read(D/'balanced_cost_paper_binding_19.json');status['paper_pdf']=paper['pdf'];status['paper_pages']=6
    status['evidence'].update(current_paper='balanced_cost_paper_binding_19.json',
        balanced_complete_cost_paper='balanced_cost_paper_evidence_19/completion.json')
    status['paper_balanced_cost_update']=dict(pages=6,table_rows=42,terminal_display_rows=35,
        represented_terminal_attempts=37,balanced_measurements=4,moved_historical_engineering_rows=3,
        references_unchanged=9,prior_art_and_contribution_boundaries_unchanged=True,
        new_independent_inputs=0,new_CP1r3_results=0)
    status['paper_sharing_prior_art_scope']['scope']='Historical paper18, retained unchanged; current paper19 updates only matched costs, display counts and historical plot qualification.'
if (D/'CP1r3_lstm_native_progress_01/completion.json').exists():
    prefix=read(D/'CP1r3_lstm_native_progress_01/completion.json')
    status['CP1r3_lstm_native_historical_resource_prefix']={k:prefix[k] for k in [
        'observed_at','summarized_prefix_steps','rows','whole_algorithm_cost','complete_confirmation_passed','qualification']}
    status['evidence']['CP1r3_lstm_native_historical_resource_prefix']='CP1r3_lstm_native_progress_01/completion.json'
if (D/'CP1r3_lstm_native_resource_phase_01/completion.json').exists():
    closed_phase=read(D/'CP1r3_lstm_native_resource_phase_01/completion.json')
    status['CP1r3_lstm_native_closed_resource_phase']={k:closed_phase[k] for k in [
        'observed_at','accepted_resource_steps','attempted_scopes','ordinary_scopes','owner_scopes','owner_commits',
        'resource_final_CPD_ns','resource_final_resources','resource_complete_driver_seconds','nested_repair_seconds',
        'initial_to_resource_endpoint_delta','terminal_mode','terminal_same_source_candidates','terminal_eligible_candidates',
        'terminal_changed','timing_handoff_passed','absolute_timing_limits','whole_method_cost','complete_confirmation_passed']}
    status['evidence']['CP1r3_lstm_native_closed_resource_phase']='CP1r3_lstm_native_resource_phase_01/completion.json'
if (D/'CP1r3_lstm_native_binding_failure_audit_01/completion.json').exists():
    audit_path=D/'CP1r3_lstm_native_binding_failure_audit_01/completion.json'
    binding_audit=read(audit_path)
    result_path=D/'cp1r3_distinct_input_cohort_01/lstm_results.json'
    original_native=read(result_path)['native']
    assert binding_audit['passed'] and binding_audit['kind']=='metadata_audit_only'
    assert not binding_audit['is_experiment_completion'] and not binding_audit['complete_confirmation_passed']
    assert original_native['status']=='execution_or_verification_failed' and original_native['quality'] is None
    assert all(sha(p)==h for p,h in binding_audit['source_sha256'].items())
    status['CP1r3_lstm_native_whole_verification_failure']=dict(
        original_status=original_native['status'],quality=None,
        command_returncode=original_native['command_returncode'],
        complete_command_seconds=original_native['complete_seconds'],
        independent_failed_verification_seconds=original_native['independent_research_verification_seconds'],
        sampled_tree_PSS_peak_kib=original_native['sampled_PSS_kib'],
        missing_memory_observations=original_native['missing_memory_observations'],
        observer_CPU_seconds=binding_audit['observer_CPU_seconds'],
        metadata_diagnosis_passed=True,diagnosed_owner_registration_transitions=len(binding_audit['rows']),
        original_frozen_verifier_passed=False,complete_confirmation_passed=False,
        remaining_full_reverification_performed=False,paper_benefit_claims_authorized=False,
        new_native_or_STA_calls=0,original_history_unchanged=True,
        source_sha256={str(p):sha(p) for p in [audit_path,result_path]},
        qualification='The original command completed, but its frozen whole verifier failed at the owner preparation registration seal. A separate metadata audit proves exactly two documented pre-execution runtime-binding additions and the actual execution seal for all three owners. It does not replace remaining byte/request/FULL/STA/vector/physical verification or admit quality. Preserve original failed role; do not repeat native work. Original resource-phase receipts remain intermediate evidence only.')
    status['evidence']['CP1r3_lstm_native_whole_failure']='CP1r3_lstm_native_binding_failure_audit_01/completion.json'
    status['outstanding'].append('LSTM/native original command completed in7615.074177s but frozen whole verification failed in74.441375s at the pre-runtime versus execution registration seal. Separate readonly metadata audit reconstructs all3preparation hashes by removing only documented runtime path/hash additions and checks actual execution seals. Original failed result/quality null preserved; remaining full verification is outstanding under serial lock. No native replay, pair ratio, quality admission or paper benefit.')
if (D/'CP1r3_supplemental_verifier_01/plan.json').exists():
    supplemental=read(D/'CP1r3_supplemental_verifier_01/plan.json')
    status['CP1r3_supplemental_verifier']=dict(
        registered=True,queued=False,new_owner=False,actual_full_reverification_performed=False,
        original_frozen_runtime_unchanged=True,registered_targets=len(supplemental['targets']),
        preserved_original_assertions=supplemental['transformation']['assertions_retained'],
        metadata_and_transform_negative_guards=read(D/'CP1r3_supplemental_verifier_validation_01/validation.json')['negative_guards'],
        execution_requires_original_cohort_terminal=True,execution_requires_nonblocking_shared_lock=True,
        complete_confirmation_passed=False,paper_benefit_claims_authorized=False)
    status['evidence']['CP1r3_supplemental_verifier']='CP1r3_supplemental_verifier_01/plan.json'
if (D/'LSTM_first_scope_mechanism_audit_01/completion.json').exists():
    first_scope=read(D/'LSTM_first_scope_mechanism_audit_01/completion.json')
    status['LSTM_first_scope_mechanism_audit']={k:first_scope[k] for k in [
        'kind','actual_request_and_domain_bytes_equal','declared_initial_route_body_and_vector_hashes_equal',
        'raw_large_source_bytes_reverified','original_endpoint_change_records_equal','raw_full_vectors_reverified',
        'local_domain_minus_native','no_release_event_or_owner_coordination_in_this_scope',
        'whole_method_quality_admitted','paper_benefit_claims_authorized','qualification']}
    status['evidence']['LSTM_first_scope_mechanism_audit']='LSTM_first_scope_mechanism_audit_01/completion.json'
if (D/'LSTM_domain_release_scope_01/completion.json').exists():
    release_scope=read(D/'LSTM_domain_release_scope_01/completion.json')
    status['LSTM_domain_release_scope']={k:release_scope[k] for k in [
        'observed_at','round','accepted','released_net','trigger_pin','failed_restricted_attempts',
        'post_release_attempts','CPD_ns','resources','source_to_candidate_resource_delta',
        'endpoint_delta_summary','complete_transaction_seconds','nested_native_core_seconds',
        'matched_no_release_counterfactual_available','is_complete_algorithm_result',
        'paper_benefit_claims_authorized','qualification']}
    status['evidence']['LSTM_domain_release_scope']='LSTM_domain_release_scope_01/completion.json'
if (D/'confirmation_priority_handoff_03/completion.json').exists():
    handoff03=read(D/'confirmation_priority_handoff_03/plan.json')
    status['active_schedule_order']=['cp1r3_distinct_input_cohort_01','CP1r3_supplemental_verifier_01',*[n['batch'] for n in handoff03['stages']]]
    pred03={n['batch']:n['predecessor'] for n in handoff03['stages']}
    pred03['CP1r3_supplemental_verifier_01']=str(D/'cp1r3_distinct_input_cohort_01/queue_priority_02')
    for owner in owners:
        if owner['batch'] in pred03 and owner['queue_generation']=='priority_03':
            owner['actual_predecessor_queue']=pred03[owner['batch']]
            if owner['phase_status'].startswith('waiting'):owner['effective_wait']='priority_dependency: '+str(Path(pred03[owner['batch']]).parent.name)
    status['evidence']['confirmation_supplemental_priority']='confirmation_priority_handoff_03/completion.json'
    status['CP1r3_supplemental_verifier'].update(queued=True,new_owner=True,queue='CP1r3_supplemental_verifier_01/queue_priority_03')
    status['submission_candidate']=dict(source='submission_candidate_01/main.tex',pdf='submission_candidate_01/build/main.pdf',independent_of_recovery_queue=True,evidence_scope='paper19 verified evidence only')
    status['outstanding'].insert(0,'Priority03: original CP1r3 confirmation continues unchanged; supplementary verifier is the immediate next actual owner before historical audit/recoveries. Submission candidate is independently closed from paper19 evidence. Only relevant experiment rows/applicability/abstract/conclusions change with new admitted confirmation; unfinished recovery is not a paper prerequisite.')
if (D/'confirmation_priority_handoff_04/completion.json').exists():
    handoff04=read(D/'confirmation_priority_handoff_04/plan.json')
    status['active_schedule_order']=['cp1r3_distinct_input_cohort_01','CP1r3_supplemental_verifier_01','CP1r3_raw_admission_01',*[n['batch'] for n in handoff04['stages']]]
    pred04={n['batch']:n['predecessor'] for n in handoff04['stages']}
    pred04['CP1r3_raw_admission_01']=str(D/'CP1r3_supplemental_verifier_01/queue_priority_03')
    for owner in owners:
        if owner['batch'] in pred04 and owner['queue_generation']=='priority_04':
            owner['actual_predecessor_queue']=pred04[owner['batch']]
            if owner['phase_status'].startswith('waiting'):owner['effective_wait']='priority_dependency: '+str(Path(pred04[owner['batch']]).parent.name)
    status['CP1r3_raw_admission']=dict(queued=True,queue='CP1r3_raw_admission_01/queue_priority_04',plan='CP1r3_raw_admission_01/plan.json',original_owners_preserved=True,actual_full_raw_admission_executed=(D/'CP1r3_raw_admission_01/execution/completion.json').exists(),new_native_or_STA_calls=0,ETA_calibrated=False)
    status['evidence']['confirmation_raw_admission_priority']='confirmation_priority_handoff_04/post_handoff_identity_check.json'
    status['outstanding'].insert(0,'Priority04: preserve original CP1r3 and supplemental owners; additional complete-request/raw-STA/actual-byte/physical-proof/paired-root admission follows the supplemental replay, before historical recovery. No native requery. Original failures and separate audit costs retained; unsupported schemas fail closed. Actual audit duration remains uncalibrated.')
if (D/'LSTM_budget_cost_progress_01/completion.json').exists():
    budget_progress=read(D/'LSTM_budget_cost_progress_01/completion.json')
    status['LSTM_budget_and_conditional_ETA']={k:budget_progress[k] for k in ['observed_at','accepted_prefix_steps','remaining_resource_budget','ordinary_transaction_observed_range_seconds','conditional_scheduling_scenarios','additional_raw_admission_ETA','whole_domain_quality_admitted','complete_domain_seconds','paired_cost_ratio','qualification']}
    status['evidence']['LSTM_budget_and_conditional_ETA']='LSTM_budget_cost_progress_01/completion.json'
if (D/'LSTM_transaction_costs_01/completion.json').exists():
    transaction_costs=read(D/'LSTM_transaction_costs_01/completion.json')
    status['LSTM_transaction_cost_diagnostic']={k:transaction_costs[k] for k in ['observed_at','completed_transactions','groups','engineering_direction','whole_pair_quality_admitted','formal_pair_cost_ratio','qualification']}
    status['evidence']['LSTM_transaction_cost_diagnostic']='LSTM_transaction_costs_01/completion.json'
if (D/'submission_narrative_02/verification.json').exists():
    status['submission_narrative_candidate']=dict(source='submission_narrative_02/main.tex',pdf='submission_narrative_02/build/main.pdf',verification='submission_narrative_02/verification.json',passed=True,pages=6,original_candidate_preserved=True,matching_rows=28,relocated_rows=14,new_experiment_results=0)
    status['research_priority_after_narrative_request']=read(D/'submission_narrative_02/research_priority.json')
    status['simple_vertical_cost_baseline']=dict(plan='vertical_cost_baseline_dev_01/plan.json',source_patch_prepared=True,built=False,queued=False,weights=[0,0.5,1,2],new_native_calls=0)
    status['outstanding'].insert(0,'Current user priority: finish unchanged CP1r3 then registered supplementary/raw admission; next implement/build/validate and queue the preregistered same-scope vertical-cost baseline before optional historical recovery. New six-page problem-insight-design-validation draft is independently verified; original candidate preserved. No uncompleted checkpoints or future baseline benefit in paper.')
if (D/'owner_registration_development_fix_02/completion.json').exists():
    status['prospective_owner_registration_fix']=read(D/'owner_registration_development_fix_02/completion.json')
    status['evidence']['prospective_owner_registration_fix']='owner_registration_development_fix_02/completion.json'
if (D/'LSTM_observation_cost_layers_01/completion.json').exists():
    layers=read(D/'LSTM_observation_cost_layers_01/completion.json')
    status['LSTM_observation_cost_layers']={k:layers[k] for k in ['observed_at','closed_ordinary_transactions','observation_workers','groups','whole_pair_quality_admitted','formal_pair_cost_ratio','qualification']}
    status['evidence']['LSTM_observation_cost_layers']='LSTM_observation_cost_layers_01/completion.json'
if (D/'submission_candidate_followup_02/role_status_and_eta.json').exists():
    status['submission_candidate_latest_conditional_ETA']=read(D/'submission_candidate_followup_02/role_status_and_eta.json')
    status['evidence']['submission_candidate_latest_conditional_ETA']='submission_candidate_followup_02/role_status_and_eta.json'
if (D/'LSTM_native_fallback_progress_01/progress_and_eta.json').exists():
    status['submission_candidate_latest_conditional_ETA']=read(D/'LSTM_native_fallback_progress_01/progress_and_eta.json')
    status['evidence']['submission_candidate_latest_conditional_ETA']='LSTM_native_fallback_progress_01/progress_and_eta.json'
    status['simple_vertical_cost_baseline']['worker_preparation']='vertical_cost_baseline_dev_01/worker_preparation.json'
if (D/'vertical_cost_baseline_dev_01/development_status.json').exists():
    status['simple_vertical_cost_baseline_development']=read(D/'vertical_cost_baseline_dev_01/development_status.json')
    status['evidence']['simple_vertical_cost_baseline_development']='vertical_cost_baseline_dev_01/development_status.json'
if (D/'LSTM_round012_rejection_01/summary.json').exists():
    status['latest_closed_LSTM_rejection']=read(D/'LSTM_round012_rejection_01/summary.json')
if (D/'confirmation_priority_handoff_05/completion.json').exists():
    status['active_schedule']='confirmation_priority_handoff_05/plan.json'
    handoff05=read(D/'confirmation_priority_handoff_05/plan.json')
    status['active_schedule_order']=['cp1r3_distinct_input_cohort_01','CP1r3_supplemental_verifier_01','CP1r3_raw_admission_01','vertical_cost_baseline_dev_01',*[n['batch'] for n in handoff05['stages']]]
    pred05={n['batch']:n['predecessor'] for n in handoff05['stages']}
    pred05['vertical_cost_baseline_dev_01']=str(D/'CP1r3_raw_admission_01/queue_priority_04')
    for owner in owners:
        if owner['batch'] in pred05 and owner['queue_generation']=='priority_05':
            owner['actual_predecessor_queue']=pred05[owner['batch']]
            if owner['phase_status'].startswith('waiting'):owner['effective_wait']='priority_dependency: '+str(Path(pred05[owner['batch']]).parent.name)

    status['simple_vertical_cost_baseline'].update(queued=True,execution_plan='vertical_cost_baseline_dev_01/execution_plan.json',checks=32)
    status['evidence']['simple_cost_queue_handoff']='confirmation_priority_handoff_05/completion.json'
    status['outstanding']=[x for x in status['outstanding'] if not x.startswith(('Priority04:','Current user priority:'))]
    status['outstanding'].insert(0,'Priority05 applied: original CP1r3, supplemental and raw-admission owners preserved. Preregistered same-source simple crossing-cost0/.5/1/2 control is now queued after raw admission and before historical audit/recovery. Actual source-control proof, private build and zero equivalence remain execution gates. Thirty-two small parser/controller checks passed; no actual baseline result yet.')
if (D/'independent_input_candidates_03/completion.json').exists():
    status['next_input_provenance']=read(D/'independent_input_candidates_03/completion.json')
    status['evidence']['next_input_provenance']='independent_input_candidates_03/INPUT_SCOPE.md'
if (D/'LSTM_closing_menu_ETA_01/progress_and_eta.json').exists():
    status['submission_candidate_latest_conditional_ETA']=read(D/'LSTM_closing_menu_ETA_01/progress_and_eta.json')
    status['evidence']['submission_candidate_latest_conditional_ETA']='LSTM_closing_menu_ETA_01/progress_and_eta.json'
if (D/'submission_narrative_export_01/completion.json').exists():
    status['submission_narrative_minimal_export']=read(D/'submission_narrative_export_01/completion.json')
    status['evidence']['submission_narrative_minimal_export']='submission_narrative_export_01/completion.json'
if (D/'LSTM_existing_tradeoffs_02/completion.json').exists():
    status['LSTM_existing_candidate_tradeoffs']=read(D/'LSTM_existing_tradeoffs_02/completion.json')
    status['LSTM_focused_419_SB_candidate']=read(D/'LSTM_existing_tradeoffs_02/focused_419_SB_candidate.json')
    status['evidence']['LSTM_existing_candidate_tradeoffs']='LSTM_existing_tradeoffs_02/TRADEOFFS.md'
if (D/'LSTM_retention_metadata_incident_01/incident.json').exists():
    status['LSTM_retention_metadata_incident']='LSTM_retention_metadata_incident_01/incident.json'
    status['evidence']['LSTM_retention_metadata_incident']='../../docs/GitHub_LSTM_retention_incident_20261117.md'
    status['outstanding'].insert(0,'Preserve round013/candidate00 guided FULL_STA_failed caused by archival hardlink ctime interference. No synthetic completion or replay; existing supplemental/raw admission must retain infrastructure classification. Do not link/unlink/chmod/touch/replace live upstream inputs. Full LSTM pair and clean timing remain unadmitted.')
if (D/'LSTM_retention_metadata_incident_01/registered_admission_scope_review.json').exists():
    status['evidence']['LSTM_registered_admission_scope']='LSTM_retention_metadata_incident_01/registered_admission_scope_review.json'
    status['LSTM_registered_admission_scope']='Original frozen verifier and raw v1 require every transaction passed. Actual round013/candidate00 is false and contains a vector without final completion. Existing queue termination is not sufficient for quality admission; preserve first actual verifier failure and reconcile existing evidence separately if needed. Baseline dependency is raw queue termination, not all roles admitted.'
if (D/'LSTM_native_fallback_progress_02/progress_and_eta.json').exists():
    status['submission_candidate_latest_conditional_ETA']=read(D/'LSTM_native_fallback_progress_02/progress_and_eta.json')
    status['evidence']['submission_candidate_latest_conditional_ETA']='LSTM_native_fallback_progress_02/progress_and_eta.json'
if (D/'submission_narrative_03/verification.json').exists():
    status['submission_narrative_clarification']=dict(verification='submission_narrative_03/verification.json',pages=6,abstract_and_numerical_table_unchanged=True,original_02_preserved=True)
    status['evidence']['submission_narrative_clarification']='submission_narrative_03/verification.json'
if (D/'LSTM_round013_candidate01_receipt_01/summary.json').exists():
    status['latest_closed_LSTM_resource_transaction']=read(D/'LSTM_round013_candidate01_receipt_01/summary.json')
    status['evidence']['latest_closed_LSTM_resource_transaction']='LSTM_round013_candidate01_receipt_01/summary.json'
if (D/'LSTM_native_fallback_progress_03/progress_and_eta.json').exists():
    status['submission_candidate_latest_conditional_ETA']=read(D/'LSTM_native_fallback_progress_03/progress_and_eta.json')
    status['evidence']['submission_candidate_latest_conditional_ETA']='LSTM_native_fallback_progress_03/progress_and_eta.json'
    status['latest_closed_LSTM_resource_transaction']=status['submission_candidate_latest_conditional_ETA']
    status['evidence']['latest_closed_LSTM_resource_transaction']='LSTM_native_fallback_progress_03/progress_and_eta.json'
if (D/'LSTM_native_fallback_progress_04/progress_and_eta.json').exists():
    status['submission_candidate_latest_conditional_ETA']=read(D/'LSTM_native_fallback_progress_04/progress_and_eta.json')
    status['evidence']['submission_candidate_latest_conditional_ETA']='LSTM_native_fallback_progress_04/progress_and_eta.json'
    status['latest_closed_LSTM_resource_transaction']=status['submission_candidate_latest_conditional_ETA']
    status['evidence']['latest_closed_LSTM_resource_transaction']='LSTM_native_fallback_progress_04/progress_and_eta.json'
if (D/'LSTM_retention_metadata_incident_01/development_guard_validation.json').exists():
    status['evidence']['LSTM_failed_evaluation_independent_audit_development']='LSTM_retention_metadata_incident_01/development_guard_validation.json'
wait_pointer=Path('/tmp/dac_resource_phase_pidfd_wait_01.json')
if wait_pointer.exists():
    pointer=read(wait_pointer)
    # This pointer locates supervision only. Actual owner/child liveness above
    # remains independently queried; no running experiment is inferred here.
    status['resource_phase_wait']=pointer
    status['resource_phase_wait_qualification']='Supervision handoff pointer only; original process identity and terminal receipts determine actual state.'
if (D/'LSTM_retention_metadata_incident_01/actual_metadata_guard_validation.json').exists():
    status['evidence']['LSTM_incident_actual_metadata_guard']='LSTM_retention_metadata_incident_01/actual_metadata_guard_validation.json'
if (D/'LSTM_complete_execution_01/verification_result.json').exists():
    latest=read(D/'LSTM_complete_execution_01/verification_result.json')
    status['LSTM_complete_execution_verification']=latest
    status['evidence']['LSTM_complete_execution_verification']='LSTM_complete_execution_01/verification_result.json'
    status['evidence']['LSTM_resource_phase_terminal']='LSTM_resource_phase_terminal_01/checkpoint.json'
    status['submission_candidate_latest_conditional_ETA']=latest['conditional_ETA']
    status['evidence']['submission_candidate_latest_conditional_ETA']='LSTM_complete_execution_01/verification_result.json'
    status['outstanding'].insert(0,'LSTM N/D commands are complete but both original verifiers failed; quality and formal paired ratio remain unavailable. Preserve native owner-registration failure and domain round013/candidate00 false completion. Original cohort continues DLA-small/native; no LSTM native/STA replay or historical completion rewrite. TableI LSTM claim awaits separate actual evidence admission.')
if (D/'DLA_small_initial_failure_01/checkpoint.json').exists():
    latest_dla=read(D/'DLA_small_initial_failure_01/checkpoint.json')
    status['DLA_small_initial_failure']=latest_dla
    status['evidence']['DLA_small_initial_failure']='DLA_small_initial_failure_01/checkpoint.json'
    status['submission_candidate_latest_conditional_ETA']=latest_dla['conditional_ETA']
    status['evidence']['submission_candidate_latest_conditional_ETA']='DLA_small_initial_failure_01/checkpoint.json'
    if latest_dla['status']=='both_original_arms_initial_route_failed_no_legal_root':
        status['outstanding'].insert(0,'DLA-small N/D both failed initial routing under frozen W100/200-iteration settings with525 overused nodes; actual whole command costs709.742677/702.413717s retained, no legal quality or method-cost ratio. Original cohort continues eltwise-SB; no DLA retry or budget change.')
    else:
        status['outstanding'].insert(0,'DLA-small/native initial routing failed under frozen W100/200-iteration settings, with525 overused nodes; retain709.742677s actual cost and no quality CPD. Original domain arm continues; keep original budget and classify its own terminal outcome before paired applicability claims.')
if (D/'eltwise_SB_native_execution_failure_01/checkpoint.json').exists():
    latest_eltwise=read(D/'eltwise_SB_native_execution_failure_01/checkpoint.json')
    status['eltwise_SB_native_execution_failure']=latest_eltwise
    status['evidence']['eltwise_SB_native_execution_failure']='eltwise_SB_native_execution_failure_01/checkpoint.json'
    status['submission_candidate_latest_conditional_ETA']=latest_eltwise['conditional_ETA']
    status['evidence']['submission_candidate_latest_conditional_ETA']='eltwise_SB_native_execution_failure_01/checkpoint.json'
    status['outstanding'].insert(0,'eltwise-SB/native ended with timing-planner str/float TypeError after resource-prefix success; complete command903.226738s retained, no whole-method quality admission or paired ratio. Original domain arm continues with frozen rules. Isolated expression-level development checks do not repair historical failure or admit actual evidence.')
if (D/'planner_numeric_slack_dev_01/validation.json').exists():
    status['prospective_planner_numeric_slack_validation']=read(D/'planner_numeric_slack_dev_01/validation.json')
    status['evidence']['prospective_planner_numeric_slack_validation']='planner_numeric_slack_dev_01/validation.json'
if (D/'CP1r3_complete_execution_01/admission_terminal.json').exists():
    status['CP1r3_complete_execution']=read(D/'CP1r3_complete_execution_01/checkpoint.json')
    status['CP1r3_registered_admission_terminal']=read(D/'CP1r3_complete_execution_01/admission_terminal.json')
    status['evidence']['CP1r3_complete_execution']='CP1r3_complete_execution_01/checkpoint.json'
    status['evidence']['CP1r3_registered_admission_terminal']='CP1r3_complete_execution_01/admission_terminal.json'
    status['submission_candidate_latest_conditional_ETA']=dict(confirmation_remaining_roles=0,supplement_remaining_roles=0,raw_queue_terminal=True,quality_admitted_pairs=0,baseline_phase='See actual original owner and execution stage; no completed baseline timing yet',baseline_time_uncalibrated=True,qualification='Previous confirmation ETA scenarios have ended. Frozen build/link guards are stage limits, not measured ETA or Goal stopping conditions.')
    status['evidence']['submission_candidate_latest_conditional_ETA']='CP1r3_complete_execution_01/admission_terminal.json'
    status['outstanding']=[x for x in status['outstanding'] if not x.startswith(('eltwise-SB/native ended','DLA-small N/D both','DLA-small/native initial','LSTM N/D commands are complete'))]
    status['outstanding'].insert(0,'CP1r3 six executions, original supplement and raw queue are terminal; zero admitted pairs. Raw failed prerequisites before large-byte audit. Native supplemental main payload exists but subsequent output-directory failure remains an unsuccessful audit command. Reconcile saved actual evidence separately without repeating native calls or rewriting historical completion. Original crossing-cost baseline now executes with frozen rules before historical recovery.')
if (D/'submission_narrative_04/verification.json').exists():
    status['submission_narrative_terminal_coverage']=dict(verification='submission_narrative_04/verification.json',pdf='submission_narrative_04/build/main.pdf',pages=6,added_unadmitted_attempt_rows=6,BNN_method_prior_art_and_mechanisms_unchanged=True,new_admitted_benefits=0)
    status['evidence']['submission_narrative_terminal_coverage']='submission_narrative_04/verification.json'
if (D/'vertical_cost_baseline_terminal_01/checkpoint.json').exists():
    baseline_terminal=read(D/'vertical_cost_baseline_terminal_01/checkpoint.json')
    status['simple_vertical_cost_baseline_terminal']=baseline_terminal
    status['evidence']['simple_vertical_cost_baseline_terminal']='vertical_cost_baseline_terminal_01/checkpoint.json'
    status['simple_vertical_cost_baseline'].update(built=True,execution_terminal=True,zero_equivalence_passed=True,positive_weights_original_admitted=0)
    status['submission_candidate_latest_conditional_ETA']=baseline_terminal['conditional_ETA']
    status['evidence']['submission_candidate_latest_conditional_ETA']='vertical_cost_baseline_terminal_01/checkpoint.json'
    status['outstanding'].insert(0,'Original four-strength crossing-cost execution terminal353.244486s; zero equivalence passed. All three positive-weight independent admissions failed on the mutable progress file bound by zero proof. Exact old progress preimage reconstructed,19 bounded guards passed; original failures retained. New independent readonly owner waits for serial slot and reuses existing candidates, no native/STA queries. No positive baseline superiority or complete-method cost claim.')
    audit_queue=D/'vertical_cost_admission_reconciliation_01/execution'
    if (audit_queue/'registration.json').exists():
        registration=read(audit_queue/'registration.json');actual=process_identity(registration['pid'])
        status['weighted_admission_readonly_owner']=dict(registration=registration,actual_process=actual,verified_live=bool(actual and actual['state']!='Z' and actual['start_ticks']==registration['start_ticks']),phase=read(audit_queue/'status.json'),completion=read(audit_queue/'completion.json') if (audit_queue/'completion.json').exists() else None)
empty_audit=D/'CLSTM_domain_empty_supervision_audit_02'
if (empty_audit/'queue/registration.json').exists():
    registration=read(empty_audit/'queue/registration.json');actual=process_identity(registration['pid'])
    status['CLSTM_empty_supervision_readonly_owner']=dict(registration=registration,actual_process=actual,verified_live=bool(actual and actual['state']!='Z' and actual['start_ticks']==registration['start_ticks']),phase=read(empty_audit/'queue/status.json'),completion=read(empty_audit/'queue/completion.json') if (empty_audit/'queue/completion.json').exists() else None)
    status['evidence']['CLSTM_empty_supervision_readonly_audit']='CLSTM_domain_empty_supervision_audit_02/execution_plan.json'
    status['evidence']['CLSTM_empty_supervision_identity_guards']='CLSTM_domain_empty_supervision_audit_02/identity_validation.json'
    status['evidence']['legacy_recovered_development_outcomes']='legacy_recovery_progress_02/checkpoint.json'
if (D/'reduction_native_complete_recovery_01/checkpoint.json').exists():
    recovered_native=read(D/'reduction_native_complete_recovery_01/checkpoint.json')
    status['reduction_native_complete_recovery']=recovered_native
    status['evidence']['reduction_native_complete_recovery']='reduction_native_complete_recovery_01/checkpoint.json'
    status['evidence']['reduction_native_closed_resource']='reduction_native_resource_phase_terminal_01/checkpoint.json'
    status['submission_candidate_latest_conditional_ETA']=recovered_native['conditional_ETA']
    status['evidence']['submission_candidate_latest_conditional_ETA']='reduction_native_complete_recovery_01/checkpoint.json'
    status['outstanding'].insert(0,'reduction/native recovered development full method is terminal at12.606378164ns,1241199wire/72SB/3058CB; own-root setup1746better286worse,hold0. New suffix5161.457547s and old failed6147.846396s stay separate; original269-query native work reused without rewriting running manifest. Original reduction/domain suffix now runs. No frozen confirmation, independent input, fresh whole cost or full N/D ratio; main paper benefits unchanged.')
if (D/'reduction_domain_complete_recovery_01/checkpoint.json').exists():
    recovered_domain=read(D/'reduction_domain_complete_recovery_01/checkpoint.json')
    status['reduction_domain_complete_recovery']=recovered_domain
    status['evidence']['reduction_domain_complete_recovery']='reduction_domain_complete_recovery_01/checkpoint.json'
    status['evidence']['reduction_domain_closed_resource']='reduction_domain_resource_phase_terminal_01/checkpoint.json'
    status['outstanding']=[x for x in status['outstanding'] if not x.startswith('reduction/native recovered development full method')]
if (D/'vertical_cost_confirmed_controls_01/checkpoint.json').exists():
    confirmed_cost=read(D/'vertical_cost_confirmed_controls_01/checkpoint.json')
    status['simple_vertical_cost_confirmed_controls']=confirmed_cost
    status['evidence']['simple_vertical_cost_confirmed_controls']='vertical_cost_confirmed_controls_01/checkpoint.json'
    status['simple_vertical_cost_baseline'].update(positive_weights_independently_admitted=3,all_four_candidates_legal=True,resource_policy_accepted_weights=0)
    status['outstanding']=[x.replace('Original crossing-cost baseline now executes with frozen rules before historical recovery.','Original four-strength baseline and its three positive readonly admissions are terminal; all four legal candidates exceed the original CB cap.') for x in status['outstanding'] if not x.startswith('Original four-strength crossing-cost execution terminal')]
if (empty_audit/'queue/completion.json').exists():
    empty_terminal=read(empty_audit/'queue/completion.json')
    status['CLSTM_empty_supervision_source_stage_terminal']=dict(queue_completion=empty_terminal,audit=read(empty_audit/'audit.json'))
    status['evidence']['CLSTM_empty_supervision_source_stage_terminal']='CLSTM_domain_empty_supervision_audit_02/audit.json'
if (D/'submission_narrative_05/verification.json').exists():
    status['submission_candidate_latest']=dict(verification='submission_narrative_05/verification.json',pdf='submission_narrative_05/build/main.pdf',impact='submission_narrative_05/EXPERIMENT_IMPACT.md',pages=6,matched_fixed_scope_cost_controls=4,new_complete_method_pairs=0,new_independent_inputs=0)
    status['evidence']['submission_candidate_latest']='submission_narrative_05/verification.json'
    status['paper_pdf']=str(D/'submission_narrative_05/build/main.pdf')
    status['submission_candidate_latest_conditional_ETA']=dict(original_recovery_remaining_roles=0,baseline_execution_remaining_roles=0,baseline_readonly_remaining_roles=0,CLSTM_source_stage_audit_remaining_roles=0,CLSTM_candidate_and_full_recovery_complete=False,CP1r3_admitted_pairs=0,qualification='Registered recovery and necessary readonly stages are terminal. New independent-input admission and separately registered remaining candidate recovery have no measured ETA yet; no queue or date/count Goal stopping condition.')
    status['evidence']['submission_candidate_latest_conditional_ETA']='submission_narrative_05/EXPERIMENT_IMPACT.md'
    status['outstanding'].insert(0,'Submission05 is independently verified at six pages. Four matched crossing-cost controls are admitted but all exceed CB653; update only TableIII/SectionV-A and related scope claims. Reduction N/D development suffixes ended with unequal historical prefixes, no fresh complete-time ratio. CLSTM23-query source stage passed, candidate physical/domain/STA and full recovery remain separately chargeable. Prioritize true independent input/actual physical-start evidence; do not repeat BNN local queries or rewrite original failures.')
if (D/'empty_query_patch_validation_01/completion.json').exists():
    status['empty_query_development_replay_terminal']=read(D/'empty_query_patch_validation_01/completion.json')
    status['evidence']['empty_query_development_replay_terminal']='empty_query_patch_validation_01/completion.json'
active_arm_pointer=Path('/tmp/dac_cp1r3_active_arm_pidfd_wait_01.json')
if (D/'GEMM_input_preflight_01/completion.json').exists():
    status['GEMM_input_byte_coordinate_preflight']=dict(result=read(D/'GEMM_input_preflight_01/completion.json'),measurement=read(D/'GEMM_input_preflight_01/measurement/completion.json'))
    status['evidence']['GEMM_input_byte_coordinate_preflight']='GEMM_input_preflight_01/completion.json'
if (D/'planner_numeric_slack_replay_02/completion.json').exists():
    status['numeric_slack_actual_replay']=read(D/'planner_numeric_slack_replay_02/completion.json')
    status['evidence']['numeric_slack_actual_replay']='planner_numeric_slack_replay_02/completion.json'
if (D/'confirmation_release_cp1r4_01/completion.json').exists():
    status['CP1r4_numeric_only_release']=dict(freeze=read(D/'confirmation_release_cp1r4_01/completion.json'),reconstruction=read(D/'confirmation_release_cp1r4_01/public_source_reconstruction.json'))
    status['evidence']['CP1r4_numeric_only_release']='confirmation_release_cp1r4_01/completion.json'
if (D/'cp1r4_gemm_pair_01/plan.json').exists():
    gemm_root=D/'cp1r4_gemm_pair_01'
    status['CP1r4_GEMM_registered_pair']=dict(preflight=read(gemm_root/'preflight.json'),registered_inputs=1,registered_roles=2,phase=read(gemm_root/'queue/status.json'),provisioning=read(gemm_root/'gemm_provisioning_cost.json') if (gemm_root/'gemm_provisioning_cost.json').exists() else None)
    gemm_results=read(gemm_root/'gemm_results.json') if (gemm_root/'gemm_results.json').exists() else {}
    status['CP1r4_GEMM_registered_pair']['terminal_role_results']=gemm_results
    status['CP1r4_GEMM_registered_pair']['remaining_execution_roles']=2-len(gemm_results)
    gemm_plan=read(gemm_root/'plan.json')
    gemm_work=Path(gemm_plan['inputs'][0]['workspace'])
    status['CP1r4_GEMM_registered_pair']['initial_gate_receipts']={arm:read(gemm_work/arm/'flow/resource_flow/initial/completion.json') for arm in ['native','domain'] if (gemm_work/arm/'flow/resource_flow/initial/completion.json').exists()}
    status['CP1r4_GEMM_registered_pair']['closed_joint_index_components']={arm:read(gemm_work/arm/'flow/resource_flow/joint_graph_indexes/completion.json') for arm in ['native','domain'] if (gemm_work/arm/'flow/resource_flow/joint_graph_indexes/completion.json').exists()}
    status['evidence']['CP1r4_GEMM_registered_pair']='cp1r4_gemm_pair_01/plan.json'
    status['active_schedule_order']=['cp1r4_gemm_pair_01',*status.get('active_schedule_order',[])]
    status['submission_candidate_latest_conditional_ETA']=dict(registered_current_roles=2,remaining_execution_roles=2-len(gemm_results),active_input='GEMM',current_phase=status['CP1r4_GEMM_registered_pair']['phase'],source_activation_observed_seconds=5.261965245008469,input_provisioning_observed_seconds=56.26370170339942,whole_new_input_duration_uncalibrated=True,qualification='Current actual case/stages and measured closure drive the next estimate. Per-child guards are not ETA or Goal stopping conditions. No complete GEMM sample or final paired QoR yet; no borrowed BNN duration.')
    status['evidence']['submission_candidate_latest_conditional_ETA']='cp1r4_gemm_pair_01/STATUS.md'
    status['submission_candidate_latest_conditional_ETA']['observed_same_input_joint_index_seconds']={arm:r['shared_complete_build_seconds'] for arm,r in status['CP1r4_GEMM_registered_pair']['closed_joint_index_components'].items()}
    status['submission_candidate_latest_conditional_ETA']['component_reference_qualification']='Same-input domain index may refer to the observed native component, not the whole remaining suffix or a complete time assembled from components.'
    if (D/'GEMM_native_initial_timeout_01/checkpoint.json').exists():
        status['GEMM_native_initial_timeout']=read(D/'GEMM_native_initial_timeout_01/checkpoint.json')
        status['evidence']['GEMM_native_initial_timeout']='GEMM_native_initial_timeout_01/checkpoint.json'
        status['submission_candidate_latest_conditional_ETA'].update(status['GEMM_native_initial_timeout']['conditional_ETA'])
        eta=status['submission_candidate_latest_conditional_ETA']
        eta['remaining_execution_roles']=2-len(gemm_results)
        current=status['CP1r4_GEMM_registered_pair']['phase']
        if current.get('arm')=='domain' and 'domain' not in gemm_results:
            current_identity=process_identity(current['pid'])
            if current_identity and current_identity['start_ticks']==current['start_ticks']:
                elapsed=float(Path('/proc/uptime').read_text().split()[0])-int(current['start_ticks'])/100
                eta.update(observed_at=status['observed_at'],observed_domain_command_elapsed_seconds_approx=elapsed,
                           conditional_remaining_seconds_approx=max(0,eta['domain_complete_command_reference_seconds']-elapsed),
                           domain_initial_start_utc=read(gemm_work/'domain/flow/resource_flow/initial/runs/state/manifest.json')['start_utc'] if (gemm_work/'domain/flow/resource_flow/initial/runs/state/manifest.json').exists() else None)
        elif 'domain' in gemm_results:
            eta.update(conditional_remaining_seconds_approx=None,condition='Original GEMM roles terminal; historical timeout-path ETA superseded by actual receipts.')
    if (D/'CLSTM_domain_recovery_02/queue/registration.json').exists():
        recovery_root=D/'CLSTM_domain_recovery_02'
        status['CLSTM_domain_registered_recovery_02']=dict(validation=read(recovery_root/'validation.json'),phase=read(recovery_root/'queue/status.json'),plan='CLSTM_domain_recovery_02/arm/plan.json',candidate_or_full_method_admitted=False)
        status['active_schedule_order'].append('CLSTM_domain_recovery_02')
        status['evidence']['CLSTM_domain_registered_recovery_02']='CLSTM_domain_recovery_02/execution_plan.json'
    if (D/'LSTM_necessary_readonly_02/queue/registration.json').exists():
        lstm_readonly=D/'LSTM_necessary_readonly_02'
        status['LSTM_necessary_readonly_02']=dict(phase=read(lstm_readonly/'queue/status.json'),
            metadata_fix_validation=read(lstm_readonly/'metadata_fix_validation.json'),
            stages=read(lstm_readonly/'stages.json') if (lstm_readonly/'stages.json').exists() else [],
            terminal=read(lstm_readonly/'queue/completion.json') if (lstm_readonly/'queue/completion.json').exists() else None,
            full_native_domain_pair_admitted=False,new_native_or_STA_calls=0)
        status['active_schedule_order'].append('LSTM_necessary_readonly_02')
        status['evidence']['LSTM_necessary_readonly_02']='LSTM_necessary_readonly_02/execution_plan.json'
    status['outstanding'].insert(0,'CP1r4 GEMM one-input/two-role confirmation now runs with fixed configs after actual +inf two-arm planner replay, independent freeze and source+wheel reconstruction. Native/domain order fixed; retain every result and independently admit source/bytes/requests/FULL/STA/full endpoints/physical gates before paper claims. Do not modify active source or budgets; original CP1r3 failures and first diagnostic observer failure/cost remain.')
if (D/'submission_narrative_06/verification.json').exists():
    paper06=read(D/'submission_narrative_06/verification.json')
    assert paper06['passed'] and paper06['pages']==6
    status['submission_candidate_latest']=paper06
    status['paper_pdf']=str(D/'submission_narrative_06/build/main.pdf')
    status['evidence']['submission_candidate_latest']='submission_narrative_06/verification.json'
    status['GEMM_complete_execution']=read(D/'GEMM_complete_execution_01/checkpoint.json')
    status['evidence']['GEMM_complete_execution']='GEMM_complete_execution_01/checkpoint.json'
    status['LSTM_native_supplementary_full_admission']=read(D/'LSTM_necessary_readonly_02/native_raw/completion.json')
    status['LSTM_domain_failed_candidate_raw_evidence']=read(D/'LSTM_necessary_readonly_02/domain_failed_evaluation/audit.json')
    status['evidence']['LSTM_native_supplementary_full_admission']='LSTM_necessary_readonly_02/native_raw/completion.json'
    status['evidence']['LSTM_domain_failed_candidate_raw_evidence']='LSTM_necessary_readonly_02/domain_failed_evaluation/audit.json'
    status['CLSTM_recovery02_actual_failure']=read(D/'CLSTM_domain_recovery_failure_02/checkpoint.json')
    status['evidence']['CLSTM_recovery02_actual_failure']='CLSTM_domain_recovery_failure_02/checkpoint.json'
    status['submission_candidate_latest_conditional_ETA']=dict(original_GEMM_remaining_roles=0,
        LSTM_necessary_readonly_remaining_stages=0,CLSTM_recovery02_remaining_stages=0,
        newly_admitted_complete_native_domain_pairs=0,old_GEMM_timeout_path_ETA_superseded=True,
        qualification='Use actual successor phase/receipts below. GEMM original roles and three LSTM readonly stages terminal; LSTM native full supplementary admission is one arm, domain source candidate audit is not whole-role admission. No full future suffix ETA calibrated, no date/count/matrix Goal stop.')
    status['evidence']['submission_candidate_latest_conditional_ETA']='submission_narrative_06/EXPERIMENT_IMPACT.md'
    status['outstanding']=[x for x in status['outstanding'] if not x.startswith('CP1r4 GEMM one-input/two-role confirmation now runs')]
    status['outstanding'].insert(0,'Submission06 verified at six pages/36 main rows; method/prior-art/BNN and mechanism/cost controls unchanged. LSTM native passed full supplementary raw admission, domain whole role still unadmitted, no new pair. GEMM both initial-timeout records retained. CLSTM02 source closure failed before consuming old native; retain old failure and only use a separately completed manifest-complete source audit for any new adapter.')
if (D/'CLSTM_domain_manifest_audit_03/audit.json').exists():
    status['CLSTM_manifest_source_audit03']=read(D/'CLSTM_domain_manifest_audit_03/audit.json')
    status['evidence']['CLSTM_manifest_source_audit03']='CLSTM_domain_manifest_audit_03/audit.json'
if (D/'CLSTM_domain_recovery_03/queue/registration.json').exists():
    recovery03=D/'CLSTM_domain_recovery_03'
    status['CLSTM_domain_registered_recovery03']=dict(phase=read(recovery03/'queue/status.json'),
        validation=read(recovery03/'validation.json'),
        result=read(recovery03/'result.json') if (recovery03/'result.json').exists() else None,
        byte_revalidation=read(recovery03/'byte_revalidation.json') if (recovery03/'byte_revalidation.json').exists() else None)
    status['active_schedule_order']=['CLSTM_domain_recovery_03',*status.get('active_schedule_order',[])]
    status['evidence']['CLSTM_domain_registered_recovery03']='CLSTM_domain_recovery_03/execution_plan.json'
    status['submission_candidate_latest_conditional_ETA']['current_CLSTM_recovery03_phase']=status['CLSTM_domain_registered_recovery03']['phase']
    status['submission_candidate_latest_conditional_ETA']['whole_suffix_reference_unavailable']=True
if (D/'CLSTM_domain_complete_recovery_03/checkpoint.json').exists():
    status['CLSTM_domain_complete_recovery03']=read(D/'CLSTM_domain_complete_recovery_03/checkpoint.json')
    status['evidence']['CLSTM_domain_complete_recovery03']='CLSTM_domain_complete_recovery_03/checkpoint.json'
    status['submission_candidate_latest_conditional_ETA']=dict(all_registered_current_stages_terminal=True,
        GEMM_remaining_roles=0,LSTM_necessary_readonly_remaining_stages=0,CLSTM_recovery03_remaining_stages=0,
        next_required_gate='LSTM/domain whole-role failed-scope/rollback/frozen-check and raw admission, not yet registered/executed',
        next_required_gate_duration_uncalibrated=True,new_complete_native_domain_pairs=0,
        qualification='Actual latest terminal receipts supersede all earlier role/suffix ETAs. Next full-domain readonly scope depends on exact failed-scope handling and actual raw coverage, not a borrowed duration or stop date. Goal active.')
if active_arm_pointer.exists():
    status['active_CP1r3_arm_wait']=read(active_arm_pointer)
    status['active_CP1r3_arm_wait_qualification']='Handoff locator only; actual queue and process identities above determine liveness.'
whole_lstm=D/'LSTM_domain_whole_admission_03'
if (whole_lstm/'queue/registration.json').exists():
    status['LSTM_domain_whole_admission_03']=dict(phase=read(whole_lstm/'queue/status.json'),
        terminal=read(whole_lstm/'queue/completion.json') if (whole_lstm/'queue/completion.json').exists() else None,
        decision=read(whole_lstm/'admission_decision.json') if (whole_lstm/'admission_decision.json').exists() else None)
    status['evidence']['LSTM_domain_whole_admission_03']='LSTM_domain_whole_admission_03/execution_plan.json'
    status['submission_candidate_latest_conditional_ETA']=dict(
        all_registered_current_stages_terminal=(whole_lstm/'queue/completion.json').exists(),
        phase=read(whole_lstm/'queue/status.json'),
        qualification='Three necessary readonly gates, no route/STA reruns. On closure explicit domain admission and matched quality decision supersede old pending labels; original ctime failure preserved. No clean-time extrapolation.')
if (D/'submission_narrative_07/verification.json').exists():
    proof07=read(D/'submission_narrative_07/verification.json')
    assert proof07['passed'] and proof07['pages']==6
    status['submission_candidate_latest']=proof07
    status['paper_pdf']=str(D/'submission_narrative_07/build/main.pdf')
    status['evidence']['submission_candidate_latest']='submission_narrative_07/verification.json'
if (D/'LSTM_admitted_mechanism_synthesis_01/completion.json').exists():
    status['LSTM_admitted_mechanism_synthesis']=read(D/'LSTM_admitted_mechanism_synthesis_01/completion.json')
    status['evidence']['LSTM_admitted_mechanism_synthesis']='LSTM_admitted_mechanism_synthesis_01/MECHANISM_RESULT.md'
if (D/'TPU_OS_input_preflight_01/completion.json').exists():
    status['TPU_OS_input_preflight']=read(D/'TPU_OS_input_preflight_01/completion.json')
    status['evidence']['TPU_OS_input_preflight']='TPU_OS_input_preflight_01/STATUS.md'
    status['next_independent_input']=dict(id='tpu_os_p0',actual_bytes_and_coordinates_passed=status['TPU_OS_input_preflight']['passed'],
        full_pair_registered=False,full_pair_started=False,new_native_or_STA_calls=0,
        known_distinct_dataflow_netlist_same_TPU_family=True,new_architecture=False,
        next='Use existing verified owner preparation/runtime identity logic in a frozen confirmation checker before registering the pair. Reuse completed CP1r4 algorithm/source evidence, no failed expensive-batch rerun.',
        ETA='No current complete-run timer or queue. Input preflight measured2.261795s; new legal-root/full-role time unknown, not borrowed from LSTM or BNN.',
        submission07_not_blocked=True)
tpu_pair=D/'cp1r5_tpu_os_pair_01'
if (tpu_pair/'plan.json').exists():
    tpu_results=read(tpu_pair/'tpu_os_results.json') if (tpu_pair/'tpu_os_results.json').exists() else {}
    tpu_live=next((o for o in owners if o['batch']=='cp1r5_tpu_os_pair_01'),None)
    status['CP1r5_TPU_OS_registered_pair']=dict(preflight=read(tpu_pair/'preflight.json'),
        phase=read(tpu_pair/'queue/status.json'),actual_owner=tpu_live,terminal_role_results=tpu_results,
        remaining_execution_roles=2-len(tpu_results),
        checkpoint=read(tpu_pair/'current_checkpoint.json') if (tpu_pair/'current_checkpoint.json').exists() else None,
        post_queue_admission=read(tpu_pair/'post_queue_admission_plan.json') if (tpu_pair/'post_queue_admission_plan.json').exists() else None)
    status['next_independent_input']=dict(id='tpu_os_p0',full_pair_registered=True,
        full_pair_started=(tpu_pair/'queue/registration.json').exists(),
        known_distinct_dataflow_netlist_same_TPU_family=True,new_architecture=False,
        quality_requires_full_raw_and_paired_admission=True,submission07_not_blocked=True)
    status['submission_candidate_latest_conditional_ETA']=dict(remaining_execution_roles=2-len(tpu_results),
        current_phase=status['CP1r5_TPU_OS_registered_pair']['phase'],
        actual_checkpoint=status['CP1r5_TPU_OS_registered_pair']['checkpoint'],
        qualification='Use actual current phase and same-input completed-stage costs. Guards are not completion predictions. Full repair/menu duration remains uncalibrated until observed.')
    status['evidence']['CP1r5_TPU_OS_registered_pair']='cp1r5_tpu_os_pair_01/STATUS.md'
    status['active_schedule_order']=['cp1r5_tpu_os_pair_01','cp1r5_tpu_os_pair_01/post_queue_admission_plan.json']
    status['outstanding']=['Complete fixed TPU-OS native/domain arms, then priority readonly actual request/FULL/raw-STA/vector/physical and six-payload paired admission before any paper claim. Retain every original failure and measured fee; no repeated completed native query. Submission07 remains independently reviewable.']
write(D/'CURRENT_STATUS.json',status)
rows=[]
for o in owners:
    if not o['verified_live']:continue
    rows.append(f"- `{o['batch']}`: {o['phase_status']}; owner PID {o['pid']}, verified live={o['verified_live']}.")
from render_current_status_md_v1 import render
text=render(status,D)

(D/'CURRENT_STATUS.md').write_text(text)
history=D/'continuation_history'/('current_status_'+str(time.time_ns()));history.mkdir()
active=[o for o in owners if o['verified_live']]
for n in ['CONTINUATION.json','live_handoff.json']:
    p=D/n;shutil.copy2(p,history/n);v=read(p)
    v.update(updated_at=now,observed_at=now,research_state='ongoing',current_goal_state='active',
        platform_automatic_continuation_limited=False,latest_current_status='CURRENT_STATUS.json',
        active_jobs=active,active_owners=active,supervisors=active,runners=active,
        running_jobs=[o for o in active if not o['phase_status'].startswith('waiting')],
        queued_jobs=[o for o in active if o['phase_status'].startswith('waiting')],
        latest_owner_verification={o['batch']:o for o in owners},latest_paper=paper,
        latest_publication=status['latest_incremental_publication'],
        latest_multiobjective=dict(archive='multiobjective_closed_stream_quality_01',points=671,complete_configurations=34,complete_observer_measured_configurations=33,qualified_GNU_only_configurations=1,complete_cold_configuration_seconds=None),
        pending_interrupted_resource_cases=(read(D/'interrupted_stage_reconciliation_01/inventory.json')['rows'] if (D/'interrupted_stage_reconciliation_01/inventory.json').exists() else []),next_actions=status['outstanding'],research_blockers=[])
    v['multiobjective_policy']['archive']='multiobjective_closed_stream_quality_01'
    write(p,v)
print(dict(observed_at=now,live_owners=[o['batch'] for o in active],summary=str(D/'CURRENT_STATUS.md')),flush=True)
