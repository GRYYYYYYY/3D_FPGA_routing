"""Bind failure, spent whole cost and supplementary scope without quality admission."""
from pathlib import Path
from datetime import datetime,timezone
from retained_prefix_workflow import D,read,write,sha

out=D/'CP1r3_lstm_native_failure_claim_binding_01.json';assert not out.exists()
audit_path=D/'CP1r3_lstm_native_binding_failure_audit_01/completion.json';audit=read(audit_path)
result_path=D/'CP1r3_lstm_native_binding_failure_audit_01/original_native_result.json';result=read(result_path)
assert audit['passed'] and audit['kind']=='metadata_audit_only' and not audit['is_experiment_completion']
assert all(sha(p)==h for p,h in audit['source_sha256'].items())
assert result['status']=='execution_or_verification_failed' and result['quality'] is None and result['command_returncode']==0
assert read(D/'cp1r3_distinct_input_cohort_01/lstm_results.json')['native']==result
supplemental=D/'CP1r3_supplemental_verifier_01/plan.json';plan=read(supplemental)
assert len(plan['targets'])==6 and all(sha(p)==h for p,h in plan['source_sha256'].items())
assert not (supplemental.parent/'cases').exists()
validation=D/'CP1r3_supplemental_verifier_validation_01/validation.json';checks=read(validation)
assert checks['passed'] and checks['negative_guards']==30 and checks['all_original_assertions_retained']==88
assert not checks['actual_full_reverification_performed']
assert all(sha(p)==h for p,h in read(D/'confirmation_priority_handoff_02/plan.json')['protected_source_sha256'].items())
paper_path=D/'balanced_cost_paper_binding_19.json';paper=read(paper_path)
assert paper['passed'] and paper['prior_art_and_contribution_boundaries_unchanged']
assert all(sha(p)==h for p,h in paper['source_sha256'].items())
sources=[Path(__file__).resolve(),audit_path,result_path,supplemental,validation,paper_path,
         D/'CP1r3_lstm_native_resource_phase_01/completion.json',
         D/'CP1r3_supplemental_verifier_validation_01/preflight_failure_01/failure.json']
write(out,dict(passed=True,kind='failure_and_scope_binding_only',observed_at=datetime.now(timezone.utc).isoformat(),
    original_result_status=result['status'],quality=None,original_whole_verifier_passed=False,
    original_native_command_returncode=0,complete_command_seconds=result['complete_seconds'],
    independent_failed_verification_seconds=result['independent_research_verification_seconds'],
    sampled_tree_PSS_peak_kib=result['sampled_PSS_kib'],missing_memory_observations=result['missing_memory_observations'],
    observer_CPU_seconds=audit['observer_CPU_seconds'],metadata_diagnosis_seconds=audit['complete_metadata_audit_seconds'],
    metadata_only_diagnosis_passed=True,original_measured_identities_repolled=audit['original_measured_identities_repolled'],
    documented_owner_registration_transitions=len(audit['rows']),
    complete_confirmation_passed=False,new_complete_verified_pairs=0,new_independent_inputs=0,
    paired_cost_ratio=None,new_native_or_STA_calls=0,
    supplementary_verifier_registered=True,supplementary_verifier_queued=False,
    supplementary_verifier_executed=False,supplementary_guards=30,original_assertions_retained=88,
    frozen_algorithm_and_current_queue_unchanged=True,original_failures_preserved=True,
    original_history_rewritten=False,resource_phase_receipt_is_not_whole_confirmation=True,
    paper19_unchanged=True,paper18_prior_art_and_contribution_boundaries_unchanged=True,
    paper_benefit_claims_authorized=False,adoption_authorized=False,
    source_sha256={str(p):sha(p) for p in sources},
    qualification='Command wall time is actual spent cost even though independent quality admission failed. No component times are stitched; observer CPU is not subtracted. The separate metadata diagnosis explains the exact documented runtime-binding transition and does not replace remaining full checks or relabel the frozen verifier. A new separately registered replay preserves all other checks and outputs elsewhere, but has not executed. Keep the original six-role cohort and four-arm audit/recovery chain; no automatic retry, new BNN role, quality admission or broader manuscript benefit.'))
print(dict(passed=True,quality_admitted=False,original_failure_preserved=True,
           supplemental_executed=False,complete_command_seconds=result['complete_seconds']))
