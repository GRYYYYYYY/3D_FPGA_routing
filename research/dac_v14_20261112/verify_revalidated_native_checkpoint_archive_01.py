"""Read-only checks for the four partial native observations and their seals."""
from pathlib import Path
from retained_prefix_workflow import D, read, sha
from run_native_scope_policy_v4 import run_dir
from state_resource_assurance import require_publication_proof

root = D/'multiobjective_revalidated_native_checkpoints_01'
receipt = read(root/'completion.json')
assert receipt['passed'] and receipt['records'] == 541 and len(receipt['added']) == 4
assert all(sha(root/n) == h for n, h in receipt['artifact_sha256'].items())
assert all(sha(p) == h for p, h in receipt['source_sha256'].items())
points = read(root/'points.json')
selected = [p for p in points if p['id'] in receipt['added']]
assert len(selected) == 4
for p in selected:
    assert not p['actor_final_selected'] and not p['actor_terminal_claim'] and not p['transition_committed']
    assert p['complete_single_configuration_seconds'] is None and p['timing_cohort'] is None
    assert p['new_native_calls_for_archival'] == 0 and p['quality_status'] == 'dominated'
    state = Path(p['state'])
    c = read(state/'completion.json')
    assert c['passed'] and all(c['checks'].values())
    proof = require_publication_proof(state)
    assert proof['passed']
    seal = read(p['actual_revalidation_context_seal'])
    assert seal['passed'] and sha(seal['pool_completion']) == seal['pool_completion_sha256']
    assert Path(seal['pool_completion']) == Path(p['batch_full_path'])/'pool/completion.json'
    assert read(seal['pool_completion'])['passed']
    assert p['independent_physical_audit_reused_for_exact_route'] == c['physical_audit_reused']
    assert p['new_independent_physical_audit_executed'] is not c['physical_audit_reused']
    assert read(run_dir(state)/'manifest.json')['metrics']['native_full_check_passed']
assert next(p for p in selected if p['arm'] == 'bnn_R1_native_revalidated_pending_candidate')['policy_accepted_if_resumed'] is False
assert next(p for p in selected if p['arm'] == 'bnn_Tf_native_revalidated_pending_candidate')['policy_accepted_if_resumed'] is True
print(dict(passed=True, sealed_partial_observations=4, native_actor_menus_closed=0,
           pending_candidates_committed=0, native_calls_new=0), flush=True)
