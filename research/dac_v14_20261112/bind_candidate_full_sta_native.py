#!/usr/bin/env python3
"""Bind successful real candidate/source integration, failed checks and correct cost semantics."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

large = D / 'candidate_full_sta_bnn_03'
c = read(large / 'completion.json')
assert c['passed'] and all(sha(p) == h for p, h in c['source_sha256'].items())
assert read(D / 'candidate_full_sta_tiny_01/completion.json')['passed']
assert read(large / 'evaluation_context/input_seal.json')['passed']
assert read(large / 'validation_only_pool/completion.json')['passed']
candidate = Path(c['candidate_state'])
gate = read(candidate / 'runs/state/analysis_gate.json')
assert gate['passed'] and all(gate['checks'].values())
assert read(candidate / 'runs/state/manifest.json')['observed_state_kind'] == 'installed_candidate'
assert read(candidate / 'runs/state/independent_audit.json')['audit']['passed']
files = [Path(__file__).resolve(), large / 'completion.json', large / 'decisions.json',
         large / 'evaluation_context/input_seal.json', large / 'validation_only_pool/completion.json',
         candidate / 'completion.json', candidate / 'runs/state/analysis_gate.json', candidate / 'runs/state/independent_audit.json',
         large / 'transaction/exact_audit_reuse.json', D / 'candidate_full_sta_tiny_01/completion.json',
         D / 'candidate_observation_view_validation_01/completion.json', D / 'candidate_full_sta_cost_semantics_01.json',
         D / 'candidate_full_sta_bnn_01/pool/completion.json', D / 'candidate_full_sta_bnn_02/evaluation_context/input_seal.json',
         D / 'pool_state_evaluator_v5.py', D / 'sealed_native_pool_replay.py', D / 'candidate_full_sta_stage_01/binding.json']
binding = dict(passed=True, stage='candidate_full_sta_stage_01',
      native_tiny='candidate_full_sta_tiny_01/completion.json',
      actual_large='candidate_full_sta_bnn_03/completion.json',
      real_candidate_observed=True, candidate_independent_same_binary_full_exports_exact=True,
      source_restored_and_following_independent_exports_exact=True, full_physical_scope_and_actual_resource_checks=True,
      CPD_ns=c['CPD_s'] * 1e9, resources=c['resources'],
      native_kernel_including_candidate_observation_seconds=c['native_kernel_including_candidate_observation_seconds'],
      native_connection_query_seconds=c['native_connection_queries_seconds'],
      original_new_worker_request_seconds=read(D / 'candidate_full_sta_bnn_01/process_costs.json')[0]['complete_process_seconds'],
      recovery_segment_seconds=c['complete_recovery_segment_engineering_validation_seconds'],
      new_repair_searches_in_recovery=0, new_independent_validation_LOAD_jobs=2,
      complete_cold_single_configuration_algorithm_seconds=None,
      failures_preserved=dict(version01='endpoint tuple/list comparison, numerical values and source exports actually equal; empty-state cleanup then masked the original assertion',
          version02='six-digit printed-source CPD consistency check was incorrectly applied to an explicit full-precision candidate metric; no numerical change or new native query',
          recovery='Normalize endpoint ID containers, initialize empty evaluator states and distinguish source printed-metric consistency from candidate native-vector identity. Reuse sealed worker and passed physical transaction/domain audits; do not manufacture a candidate gate.'),
      validated_scope='Default compatibility and actual resource-repair candidate on the existing tiny fixture and one BNN eight-network feedback transaction. The BNN candidate has flatCPD and nine improved setup components. CPD-changing/forced-path timing transactions and broad fixed-policy cold runtime are not validated by this binding.',
      source_sha256={str(p): sha(p) for p in files},
      qualification='Actual integrated candidate FULL/freshSTA validated, not a new search primitive or an additional quality-frontier point. Fused COMPLETE clock includes its candidate observer, so it is not the earlier callback-free core. Original failed segments, native creation and new validation-only controls remain separate, not a synthetic cold timing point. Original quality cohort versions remain unchanged; resource-first timing uses its separately registered stable backend.')
write(D / 'candidate_full_sta_native_binding_01.json', binding)
write(D / 'candidate_full_sta_stage_01/native_validation_binding_01.json', dict(passed=True,
      evidence='candidate_full_sta_native_binding_01.json',
      source_sha256={str(D / 'candidate_full_sta_native_binding_01.json'): sha(D / 'candidate_full_sta_native_binding_01.json')},
      qualification='Historical build-only binding remains immutable; this file records completed scope-specific native validation, without a performance claim.'))
print(dict(passed=True, CPD_ns=binding['CPD_ns'], resources=binding['resources']), flush=True)
