"""Verify all feasible or rolled-back explicit-domain whole-net transactions."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from run_native_scope_policy_v4 import run_dir
from fixed_anchor_acceptance import decisions
from multiobjective_acceptance_v2 import decide
from endpoint_timing_policy_streaming_v2 import compare

root = D / 'R1_crossing_source_probe_01'
q, tx = root / 'queue', root / 'transaction'
assert read(q / 'completion.json')['passed']
terminal = read(tx / 'completion.json')
assert terminal['passed']
reg, progress = read(tx / 'registration.json'), read(tx / 'progress.json')
assert not (root / 'verification.json').exists()
files = [Path(__file__).resolve(), q / 'completion.json', q / 'registration.json',
         tx / 'completion.json', tx / 'registration.json', tx / 'progress.json',
         tx / 'process_costs.json', root / 'plan.json',
         D / 'R1_whole_net_residual_probe_01/verification.json',
         D / 'crossing_source_stage_01/build_verification.json']
hashed = {}
def checked(p):
    p = str(Path(p).resolve())
    if p not in hashed:
        hashed[p] = sha(p)
    return hashed[p]
def bound(proof):
    for p, h in proof.get('source_sha256', {}).items():
        assert checked(p) == h, p
for proof in [read(q / 'registration.json'), terminal, reg]:
    bound(proof)

results = {}
for name, role in reg['roles'].items():
    source = Path(role['state'])
    before = read(source / 'endpoint_vector.json')
    worker = tx / name
    wc = read(worker / 'completion.json')
    assert wc['passed'] and all(wc['checks'].values())
    restored = read(worker / 'endpoint_vector.json')
    assert all(restored[k] == before[k] for k in ['cpd_s', 'setup', 'hold', 'endpoint_ids', 'constraints_sha256'])
    assert route_body(run_dir(worker) / 'routed.route') == route_body(Path(role['source']) / 'routed.route')
    assert checked(role['request']) == checked(D / 'R1_whole_net_residual_probe_01/whole_net_current_criticality_request.txt')
    domain = read(tx / (name + '_domain_audit.json'))
    audit = read(tx / (name + '_audit/analysis.json'))
    assert domain['passed'] and domain['explicit_whole_net_source_restriction']
    assert not domain['retained_crossing_reuse'] and audit['passed']
    bound(domain)
    bound(audit)
    row = progress[name]
    result = dict(status=row['status'], allowed_resource_kind=role['allowed_resource_kind'],
                  actual_queries=len(audit['queries']), actual_search_attempts=len(audit['attempts']))
    if row['status'] == 'transaction_failed_rolled_back':
        assert not audit.get('candidate_route') and not domain['transaction_completed']
        result.update(quality=None, accepted=False,
                      qualification='Native constrained search failed operationally; source restored. No mathematical infeasibility or global lower-bound attainability claim.')
    else:
        assert row['status'] == 'legal_evaluated' and domain['transaction_completed']
        state = Path(row['evaluation'])
        rd = run_dir(state)
        assert read(state / 'completion.json')['passed']
        manifest = read(rd / 'manifest.json')
        assert manifest['metrics']['native_full_check_passed']
        assert all(checked(rd / n) == manifest['outputs'][n]['sha256'] for n in ['packed.net', 'placed.place', 'routed.route'])
        physical = read(rd / 'independent_audit.json')
        assert physical['audit']['passed']
        m = physical['physical_metrics']
        resources = dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'], SB_pairs=m['sb_pairs_used'], CB_sources=m['cb_crossing_output_sources_used'])
        assert resources == row['resources'] and resources['SB_pairs'] + resources['CB_sources'] == 5103
        assert route_body(rd / 'routed.route') == route_body(Path(audit['candidate_route']))
        after = read(state / 'endpoint_vector.json')
        current = dict(wirelength=2070629, SB_pairs=33, CB_sources=5071)
        expected = decisions(before, after, current, resources, role['original_budget'])
        for mode in ['timing_under_resources', 'resources_under_timing']:
            expected[mode] = decide(mode, before, after, current, resources,
                cpd_limit_s=role['original_budget']['CPD_s'], resource_limits=role['fixed_resource_limits'],
                native_valid=True, transaction_complete=True, resource_objectives=('SB_pairs', 'CB_sources'))
        assert expected == read(tx / (name + '_decisions.json'))
        result.update(evaluation=str(state), CPD_ns=after['cpd_s'] * 1e9, resources=resources,
                      accepted=expected['resources_under_timing']['accepted'], policies=row['policies'],
                      endpoint_comparison=compare(before, after), native_core_seconds=row['native_core_seconds'])
        files += [state / 'completion.json', state / 'endpoint_vector.json', rd / 'manifest.json',
                  rd / 'independent_audit.json', rd / 'routed.route', tx / (name + '_decisions.json')]
    results[name] = result
    files += [source / 'endpoint_vector.json', worker / 'completion.json', worker / 'endpoint_vector.json',
              tx / (name + '_audit/analysis.json'), tx / (name + '_domain_audit.json')]
write(root / 'verification.json', dict(passed=True, roles=results, native_calls_new=0,
      complete_shared_imported_scope_seconds=terminal['complete_orchestrator_seconds'],
      committed_to_original_actor=False, source_sha256={str(f): checked(f) for f in files},
      qualification='Explicit one-original-crossing-resource whitelist, not retained-crossing reuse; all candidate and restored native FULL/fresh STA, physical/capacity/scope/domain gates remain. Same new binary/scope/order/weights across the CB-only/SB-only pair. Old unrestricted whole-net controls are a separately bound binary; no unmeasured default-search equivalence or isolated cross-version causal claim. All failures/rejections retained. Shared imported scope cost includes real source serialization and two roles, not cold or standalone algorithm time.'))
print(dict(passed=True, roles=results), flush=True)
