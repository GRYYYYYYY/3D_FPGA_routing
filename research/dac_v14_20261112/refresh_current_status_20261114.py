"""Small authoritative entry point; preserve historical receipts and old handoffs."""
from datetime import datetime,timezone
from pathlib import Path
import shutil
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

now=datetime.now(timezone.utc).isoformat()
owners=[]
for name in ['stable_seed_transfer_recovery_02','direct_scope_resource_equivalence_recovery_02',
             'native_census_resource_equivalence_recovery_02','native_checkpoint_recovery_01',
             'rejection_feedback_controller_dev_01','complete_route_resource_measurements_01',
             'vector_then_strict_comparison_01','connection_budget_resource_dev_01',
             'complete_serial_resource_measurement_dev_01','complete_serial_resource_measurement_paired_dev_01',
             'complete_serial_reusable_graph_dev_01','complete_serial_seed_policy_dev_01','serial_fused_candidate_validation_01','serial_fused_candidate_validation_02','complete_serial_fused_dev_01','complete_serial_transfer_dev_01','complete_serial_fused_dev_03','complete_serial_lazy_dev_01','connection_budget_scope_probe_01','complete_serial_lazy_transfer_dev_01','complete_serial_architecture_transfer_01','budget47_current_timing_composition_01','complete_serial_seed_transfer_01','complete_serial_source_snapshot_01','complete_serial_timing_budget_01','complete_resource_timing_full_flow_01','R1_whole_net_residual_probe_01','R1_crossing_source_probe_01','native_checkpoint_recovery_02','complete_route_resource_measurements_02','vector_then_strict_comparison_02','connection_budget_resource_dev_02','R1_owner_release_joint_probe_01','complete_serial_additional_circuits_01','complete_serial_lazy_source_snapshot_01','partial_escape_owner_intervention_01','complete_BNN_joint_index_flow_01','complete_BNN_closed_stream_flow_01','BNN_wire_timing_native_validation_01','native_checkpoint_recovery_03','complete_route_resource_measurements_03','vector_then_strict_comparison_04','robot_domain_release_ablation_01','complete_BNN_terminal_wire_flow_01','query_reduction_resource_dev_01','unexecuted_recovery_20261115_01','unified_input_integration_01','standalone_native_observation_equivalence_01','standalone_transaction_native_check_01','standalone_whole_method_check_01','portable_clstm_pair_01','robot_owner_scope_pair_01','portable_robot_p1_pair_01','complete_BNN_domain_engineering_01','portable_reduction_pair_01','clstm_input_contract_pair_02','robot_p1_input_contract_pair_02','cp1_cross_circuit_cohort_01','robot_union_mechanism_01','BNN_interleaved_timing_01','cp1r1_cross_circuit_cohort_01','cp1r2_cross_circuit_cohort_01','robot_union_mechanism_02','robot_union_verification_recovery_01','BNN_interleaved_timing_02','BNN_interleaved_timing_03','robot_owner_reentry_audit_01','robot_owner_reentry_audit_02','empty_query_patch_validation_01','confirmation_release_cp1r3_01','robot_p1_prefix_recovery_01']:
    q=D/name/('' if name.startswith('serial_fused_candidate_validation_') else 'queue');reg=read(q/'registration.json')
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
        flow=D/name/phase['case']/'flow'
        if (flow/'active_child.json').exists():
            stage=read(flow/'active_child.json');actual=process_identity(stage['pid'])
            if actual and actual['state']!='Z' and actual['start_ticks']==stage['start_ticks']:
                flow_stage=dict(phase=stage['phase'],pid=stage['pid'],start_ticks=stage['start_ticks'],verified_live=True,actual_process=actual)
        if (flow/'stages.json').exists():
            completed_flow_stages=[{k:v for k,v in row.items() if k in ['phase','status','returncode','complete_process_seconds']} for row in read(flow/'stages.json')]
    if name=='robot_p1_prefix_recovery_01':
        recovery_flow=D/name/'flow'
        if (recovery_flow/'active_child.json').exists():
            stage=read(recovery_flow/'active_child.json');actual=process_identity(stage['pid'])
            if actual and actual['state']!='Z' and actual['start_ticks']==stage['start_ticks']:
                flow_stage=dict(phase=stage.get('tag',stage.get('phase')),pid=stage['pid'],start_ticks=stage['start_ticks'],verified_live=True,actual_process=actual)
    owners.append(dict(flow_active_stage=flow_stage,completed_flow_stages=completed_flow_stages,batch=name,wait_channel=wait_channel,effective_wait='shared_serial_slot' if wait_channel and wait_channel.startswith('locks_lock') and phase['status'].startswith('waiting') else None,registration=str(q/'registration.json'),pid=reg['pid'],start_ticks=reg['start_ticks'],
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
        pending_interrupted_resource_cases=[],next_actions=status['outstanding'],research_blockers=[])
    v['multiobjective_policy']['archive']='multiobjective_closed_stream_quality_01'
    write(p,v)
print(dict(observed_at=now,live_owners=[o['batch'] for o in active],summary=str(D/'CURRENT_STATUS.md')),flush=True)
