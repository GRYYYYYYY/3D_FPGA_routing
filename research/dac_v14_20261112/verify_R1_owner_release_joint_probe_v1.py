"""Verify the matched two-net owner-release pair, including failed searches."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from run_native_scope_policy_v4 import run_dir
from fixed_anchor_acceptance import decisions
from multiobjective_acceptance_v2 import decide
from endpoint_timing_policy_streaming_v2 import compare

root = D / 'R1_owner_release_joint_probe_01'
q, tx = root / 'queue', root / 'transaction'
assert read(q / 'completion.json')['passed'] and read(tx / 'completion.json')['passed']
assert not (root / 'verification.json').exists()
reg, progress = read(tx / 'registration.json'), read(tx / 'progress.json')
roles = reg['roles']
assert list(roles) == ['joint_native', 'joint_target_CB_domain']
off, on = roles.values()
for key in ['state', 'source', 'request', 'queries', 'removed_pins', 'objective',
            'seed_order', 'original_budget', 'fixed_resource_limits']:
    assert off[key] == on[key], key
assert off['removed_pins'] == {'31767': [1, 2, 3, 4], '62707': [1]}
assert len(off['queries']) == 5 and off['objective'] == 'weighted_soft'
assert not off['crossing_reuse_enabled'] and on['crossing_reuse_enabled']
assert not off['explicit_crossings'] and on['explicit_crossings']
files = [Path(__file__).resolve(), q / 'completion.json', q / 'registration.json',
         tx / 'completion.json', tx / 'registration.json', tx / 'progress.json',
         tx / 'process_costs.json', root / 'selection.json', root / 'plan.json',
         D / 'R1_local_escape_owner_diagnostic_01/completion.json']
hashed = {}
def checked(p):
    p = str(Path(p).resolve())
    if p not in hashed:
        hashed[p] = sha(p)
    return hashed[p]
def bound(proof):
    for p, h in proof.get('source_sha256', {}).items():
        assert checked(p) == h, p
for proof in [read(q / 'registration.json'), reg, read(tx / 'completion.json')]:
    bound(proof)
def axes(state):
    a = read(run_dir(state) / 'independent_audit.json')
    assert a['audit']['passed']
    m = a['physical_metrics']
    return dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'],
                SB_pairs=m['sb_pairs_used'], CB_sources=m['cb_crossing_output_sources_used'])
source = Path(off['state'])
before, current = read(source / 'endpoint_vector.json'), axes(source)
assert current == dict(wirelength=2070629, SB_pairs=33, CB_sources=5071)
selection = read(root / 'selection.json')
assert selection['selected']['owner_net'] == 62707 and selection['selected']['pins'] == [1]
assert selection['selected']['current_0p2ns_screen']['eligible']
results, binaries = {}, set()
for name, role in roles.items():
    worker = tx / name
    wc = read(worker / 'completion.json')
    assert wc['passed'] and all(wc['checks'].values())
    restored = read(worker / 'endpoint_vector.json')
    assert all(restored[k] == before[k] for k in ['cpd_s', 'setup', 'hold', 'endpoint_ids', 'constraints_sha256'])
    assert route_body(run_dir(worker) / 'routed.route') == route_body(Path(role['source']) / 'routed.route')
    manifest = read(run_dir(worker) / 'manifest.json')
    binaries.add(checked(manifest['command'][0]))
    assert manifest['environment']['VPR_JOINT_NATIVE_SEED_ORDER'] == role['seed_order']
    assert manifest['environment']['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE'] == '0'
    audit, domain = [read(tx / p) for p in [name + '_audit/analysis.json', name + '_domain_audit.json']]
    assert audit['passed'] and domain['passed']
    bound(audit)
    bound(domain)
    assert domain['enabled'] == role['crossing_reuse_enabled']
    if domain['enabled']:
        assert domain['explicit_whole_net_source_restriction'] and not domain['retained_crossing_reuse']
        assert domain['allowed_sources'] == [265308]
    expected_order = [(p['net'], p['pin']) for p in role['queries']]
    observed_order = [(p['net'], p['pin']) for p in audit['queries']]
    assert observed_order == expected_order[:len(observed_order)]
    row = progress[name]
    result = dict(status=row['status'], actual_queries=len(audit['queries']),
                  actual_search_attempts=len(audit['attempts']), target_CB_domain=role['crossing_reuse_enabled'])
    if row['status'] == 'transaction_failed_rolled_back':
        assert not audit.get('candidate_route')
        result.update(quality=None, accepted=False)
    else:
        assert row['status'] == 'legal_evaluated' and observed_order == expected_order
        assert {r['net'] for r in audit['scope']} == {31767, 62707}
        assert all(r['terminal_set_unchanged'] and r['other_branch_edges_unchanged'] for r in audit['scope'])
        state = Path(row['evaluation'])
        rd = run_dir(state)
        m = read(rd / 'manifest.json')
        assert read(state / 'completion.json')['passed'] and m['metrics']['native_full_check_passed']
        assert all(checked(rd / n) == m['outputs'][n]['sha256'] for n in ['packed.net', 'placed.place', 'routed.route'])
        assert route_body(rd / 'routed.route') == route_body(Path(audit['candidate_route']))
        after, resource = read(state / 'endpoint_vector.json'), axes(state)
        assert resource == row['resources'] and after['cpd_s'] == row['cpd_s']
        expected = decisions(before, after, current, resource, role['original_budget'])
        for mode in ['timing_under_resources', 'resources_under_timing']:
            expected[mode] = decide(mode, before, after, current, resource,
                cpd_limit_s=role['original_budget']['CPD_s'], resource_limits=role['fixed_resource_limits'],
                native_valid=True, transaction_complete=True, resource_objectives=('SB_pairs', 'CB_sources'))
        assert expected == read(tx / (name + '_decisions.json'))
        result.update(evaluation=str(state), CPD_ns=after['cpd_s'] * 1e9, resources=resource,
                      accepted=expected['resources_under_timing']['accepted'], policies=row['policies'],
                      endpoint_comparison=compare(before, after), native_core_seconds=row['native_core_seconds'])
        files += [state / 'completion.json', state / 'endpoint_vector.json', rd / 'manifest.json',
                  rd / 'independent_audit.json', rd / 'routed.route', tx / (name + '_decisions.json')]
    results[name] = result
    files += [worker / 'completion.json', worker / 'endpoint_vector.json', run_dir(worker) / 'manifest.json',
              tx / (name + '_audit/analysis.json'), tx / (name + '_domain_audit.json')]
assert binaries == {read(D / 'crossing_source_stage_01/binding.json')['binary_sha256']}
write(root / 'verification.json', dict(passed=True, roles=results, native_calls_new=0,
      matched_source_scope_order_weights_and_binary=True, only_target_crossing_domain_differs=True,
      complete_shared_imported_scope_seconds=read(tx / 'completion.json')['complete_orchestrator_seconds'],
      committed_to_original_actor=False, source_sha256={str(f): checked(f) for f in files},
      qualification='Prospectively selected owner-release group, with actual same-source/new-binary unrestricted native control. Preserve all failures, legal rejects and tradeoffs. Source/candidate/restored FULL/STA, physical/capacity/scope/domain and exact original-envelope decisions checked. Shared imported scope includes real source serialization/control and both roles, not cold or per-arm standalone time. Original R1 actor remains unchanged.'))
print(dict(passed=True, roles=results), flush=True)
