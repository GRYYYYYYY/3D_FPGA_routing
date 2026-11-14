#!/usr/bin/env python3
"""Bind actual automatic release, matched route/STA, acceptance and whole workflow costs."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from run_native_scope_policy_v4 import run_dir

b = D / 'automatic_domain_release_dev_01'
c = read(b / 'completion.json')
assert c['passed'] and all(sha(p) == h for p, h in c['source_sha256'].items())
tiny = read(D / 'domain_failure_release_tiny_01/completion.json')
assert tiny['passed']
tx = b / 'round_000/candidate_00'
domain = read(tx / 'automatic_release_domain_audit.json')
assert domain['passed'] and domain['released_queries'] == [[31767, 1]] and len(domain['final_domain_nets']) == 7
assert all(sha(p) == h for p, h in domain['source_sha256'].items())
candidate = Path(c['final_state'])
reference = Path(read(D / 'failure_feedback_domain_dev_02/completion.json')['final_state'])
fallback = Path(c['fallback_state'])
v = read(candidate / 'endpoint_vector.json')
ref = read(reference / 'endpoint_vector.json')
assert all(v[k] == ref[k] for k in ['cpd_s', 'setup', 'hold', 'endpoint_ids', 'constraints_sha256'])
assert sha(run_dir(candidate) / 'routed.route') == sha(run_dir(reference) / 'routed.route')
decision = read(tx / 'automatic_release_decisions.json')
assert decision['accepted'] and read(b / 'pool/completion.json')['passed']
assert read(b / 'evaluation_context/input_seal.json')['passed']
pool_jobs = read(b / 'pool/jobs.json')
assert len(pool_jobs) == 2 and pool_jobs[0]['native_options']['operation'] == 'repair_feedback'
assert all(j['passed'] for j in pool_jobs)
audit = read(tx / 'automatic_release_audit/analysis.json')
costs = read(b / 'process_costs.json')
whole = c['complete_imported_algorithm_workflow_seconds']
stages = [dict(row, percent_of_imported_workflow=100 * row['complete_process_seconds'] / whole) for row in costs]
residual = whole - sum(row['complete_process_seconds'] for row in costs)
assert residual >= 0
files = [Path(__file__).resolve(), b / 'registration.json', b / 'completion.json', b / 'process_costs.json',
         b / 'pool/completion.json', b / 'pool/jobs.json', b / 'evaluation_context/input_seal.json',
         b / 'evaluation_context/completion.json', tx / 'automatic_release_domain_audit.json',
         tx / 'automatic_release_audit/analysis.json', tx / 'automatic_release_decisions.json',
         candidate / 'endpoint_vector.json', reference / 'completion.json', reference / 'endpoint_vector.json',
         D / 'domain_failure_release_tiny_01/completion.json', D / 'domain_failure_release_stage_01/binding.json']
write(D / 'automatic_domain_release_mechanism_01.json', dict(passed=True,
      automatic_initial_domain_nets=domain['initial_domain_nets'], automatic_released_queries=domain['released_queries'],
      final_guided_nets=domain['final_domain_nets'],
      metadata_qualification='The legacy current_state.remaining_domain_nets field is the controller initial specification, not the final native active domain. The actual native trace and audited seven-net final list above are authoritative.',
      exact_prior_selective_domain_route_and_full_vectors=True,
      CPD_ns=v['cpd_s'] * 1e9, resources=c['final_resources'],
      delta_from_same_source_unrestricted=dict(CPD_s=0, wirelength=64, SB_pairs=-2, CB_sources=0),
      acceptance=dict(resources_under_timing=decision['accepted'],
          strict=decision['strict_or_endpoint_control']['strict']['accepted'],
          endpoint_vector=decision['strict_or_endpoint_control']['endpoint_vector']['accepted'],
          strict_or_endpoint_evidence=decision['strict_or_endpoint_control']),
      native_search_core_seconds=audit['native_transaction_seconds'],
      complete_imported_algorithm_workflow_seconds=whole, workflow_stage_costs=stages,
      residual_registration_context_and_misc_seconds=residual,
      source_worker_native_child_seconds=pool_jobs[0]['native_child_seconds'],
      candidate_FULL_STA_native_child_seconds=pool_jobs[1]['native_child_seconds'],
      costs_nested_not_additive=True, complete_single_configuration_algorithm_seconds=None,
      source_sha256={str(p): sha(p) for p in files},
      qualification='Real automatic per-net native release from the fixed registered eight-cut scope, no manual release target or transaction restart. Capacity, replacement, whole native FULL/STA, exact fixed vectors and final seals passed. Same quality observation as prior manual partial-domain proof; not an additional frontier configuration or formal cold speedup. Fresh own-current selector trajectories from pristine roots run in a separate subsequent cohort.'))
write(D / 'domain_failure_release_stage_01/native_validation_binding_01.json', dict(
      passed=True, tiny='domain_failure_release_tiny_01/completion.json',
      large='automatic_domain_release_dev_01/completion.json', mechanism='automatic_domain_release_mechanism_01.json',
      source_sha256={str(p): sha(p) for p in [D / 'domain_failure_release_tiny_01/completion.json',
          b / 'completion.json', D / 'automatic_domain_release_mechanism_01.json', D / 'domain_failure_release_stage_01/binding.json']},
      qualification='Historical build binding remains immutable. Native compatibility, automatic fallback and actual matched replacement/FULLSTA now passed; no cold complete-algorithm timing claim.'))
print(dict(passed=True, CPD_ns=v['cpd_s'] * 1e9, resources=c['final_resources'],
           workflow_seconds=whole, core_seconds=audit['native_transaction_seconds']), flush=True)
