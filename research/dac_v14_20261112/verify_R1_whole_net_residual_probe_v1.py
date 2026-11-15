"""Verify actual whole-net candidates without changing the registered SB/CB policy."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha, route_body
from run_native_scope_policy_v4 import run_dir
from fixed_anchor_acceptance import decisions
from multiobjective_acceptance_v2 import decide
from endpoint_timing_policy_streaming_v2 import compare
from resource_opportunity_census import stream_trace

root = D / 'R1_whole_net_residual_probe_01'
tx = root / 'transaction'
q = root / 'queue'
closed = read(q / 'completion.json')
assert closed['passed'] and read(tx / 'completion.json')['passed']
out = root / 'verification.json'
assert not out.exists()
files = [Path(__file__).resolve(), q / 'completion.json', q / 'registration.json',
         root / 'plan.json', tx / 'completion.json', tx / 'registration.json',
         tx / 'progress.json', tx / 'process_costs.json',
         root / 'actual_old_pin1_control.json', D / 'multiobjective_acceptance_v2.py']
hashed = {}
def checked(p):
    p = str(Path(p).resolve())
    if p not in hashed:
        hashed[p] = sha(p)
    return hashed[p]
def bound(receipt):
    for p, h in receipt.get('source_sha256', {}).items():
        assert checked(p) == h, p
for p in [q / 'registration.json', q / 'completion.json', tx / 'completion.json']:
    bound(read(p))

def axes(state):
    audit = read(run_dir(state) / 'independent_audit.json')
    assert audit['audit']['passed']
    m = audit['physical_metrics']
    return dict(wirelength=m['planar_wirelength_excluding_sb_half_nodes'],
                SB_pairs=m['sb_pairs_used'], CB_sources=m['cb_crossing_output_sources_used'])

def net_tree(state):
    rec = next(r for r in stream_trace(run_dir(state) / 'routed.route') if r['net'] == 31767)
    trace = rec['trace']
    cross = []
    for a, b in zip(trace, trace[1:]):
        if a.switch != -1 and a.low[2] != b.low[2]:
            cross.append(dict(kind='CB' if a.kind == 'OPIN' else 'SB',
                              nodes=[a.inode, b.inode], layers=[a.low[2], b.low[2]]))
    return dict(source_layer=trace[0].low[2],
                sinks=sorted((n.pin, n.low[2]) for n in trace if n.kind == 'SINK'),
                crossings=cross)

roles = read(tx / 'registration.json')['roles']
progress = read(tx / 'progress.json')
source = Path(read(root / 'plan.json')['source_state'])
bv = read(source / 'endpoint_vector.json')
br = axes(source)
assert br == dict(wirelength=2070629, SB_pairs=33, CB_sources=5071)
original = read(D / 'stable_seed_transfer_recovery_01/bnn_R1_paired/registration.json')['anchor']
files += [source / 'endpoint_vector.json', run_dir(source) / 'routed.route',
          D / 'stable_seed_transfer_recovery_01/bnn_R1_paired/registration.json']
results = {}
for name, role in roles.items():
    assert role['state'] == str(source)
    assert not role['crossing_reuse_enabled'] and not role['domain_failure_release']
    assert role['fixed_resource_limits'] == original['resource_limits']
    assert role['original_budget']['CPD_s'] == original['CPD_s']
    worker = tx / name
    wc = read(worker / 'completion.json')
    assert wc['passed'] and all(wc['checks'].values())
    restored = read(worker / 'endpoint_vector.json')
    assert all(restored[k] == bv[k] for k in ['cpd_s', 'setup', 'hold', 'endpoint_ids', 'constraints_sha256'])
    assert route_body(run_dir(worker) / 'routed.route') == route_body(run_dir(source) / 'routed.route')
    audit = read(tx / (name + '_audit/analysis.json'))
    assert audit['passed'] and audit['scope'] == [dict(net=31767, retained_nodes=1, other_branch_edges_unchanged=True, terminal_set_unchanged=True)]
    assert {r['net'] for r in audit['queries']} == {31767}
    assert sorted(r['pin'] for r in audit['queries']) == [1, 2, 3, 4]
    expected_order = [3, 1, 4, 2] if name == 'whole_net_current_criticality' else [1, 2, 3, 4]
    assert [r['pin'] for r in audit['queries']] == expected_order
    domain = read(tx / (name + '_domain_audit.json'))
    assert domain['passed'] and domain['enabled'] is False
    bound(domain)
    row = progress[name]
    assert row['status'] == 'legal_evaluated' and not row['native_reused']
    state = Path(row['evaluation'])
    rd = run_dir(state)
    c = read(state / 'completion.json')
    assert c['passed']
    m = read(rd / 'manifest.json')
    assert m['metrics']['native_full_check_passed']
    assert all(checked(rd / n) == m['outputs'][n]['sha256'] for n in ['packed.net', 'placed.place', 'routed.route'])
    assert route_body(rd / 'routed.route') == route_body(Path(audit['candidate_route']))
    assert checked(audit['candidate_route']) == audit['candidate_sha256']
    av, ar = read(state / 'endpoint_vector.json'), axes(state)
    assert ar == row['resources'] and av['cpd_s'] == row['cpd_s']
    expected = decisions(bv, av, br, ar, role['original_budget'])
    for mode in ['timing_under_resources', 'resources_under_timing']:
        expected[mode] = decide(mode, bv, av, br, ar, cpd_limit_s=role['original_budget']['CPD_s'],
                                resource_limits=role['fixed_resource_limits'], native_valid=True,
                                transaction_complete=True, resource_objectives=('SB_pairs', 'CB_sources'))
    assert expected == read(tx / (name + '_decisions.json'))
    delta = compare(bv, av)
    assert delta['compatible']
    results[name] = dict(status='legal_evaluated', state=str(state), CPD_ns=av['cpd_s'] * 1e9,
                         resources=ar, wire_delta=ar['wirelength'] - br['wirelength'],
                         vector_exact=all(bv[k] == av[k] for k in ['cpd_s', 'setup', 'hold', 'endpoint_ids', 'constraints_sha256']),
                         decisions=row['policies'], query_order=expected_order, actual_queries=4,
                         actual_search_attempts=len(audit['attempts']), native_core_seconds=row['native_core_seconds'],
                         actual_net_tree=net_tree(state), endpoint_comparison=delta)
    files += [worker / 'completion.json', worker / 'endpoint_vector.json',
              run_dir(worker) / 'routed.route', tx / (name + '_audit/analysis.json'),
              tx / (name + '_domain_audit.json'), tx / (name + '_decisions.json'),
              state / 'completion.json', state / 'endpoint_vector.json', rd / 'manifest.json',
              rd / 'independent_audit.json', rd / 'routed.route']

ss = list(results.values())
write(out, dict(passed=True, source_state=str(source), source_resources=br, source_tree=net_tree(source),
                roles=results, final_candidates_same_full_vector=ss[0]['vector_exact'] and ss[1]['vector_exact'],
                final_candidates_same_ordered_route=route_body(run_dir(Path(ss[0]['state'])) / 'routed.route') == route_body(run_dir(Path(ss[1]['state'])) / 'routed.route'),
                complete_shared_imported_scope_seconds=read(tx / 'completion.json')['complete_orchestrator_seconds'],
                committed_to_original_actor=False, native_calls_new=0,
                source_sha256={str(f): checked(f) for f in files},
                qualification='Both actual whole-net candidates include source/candidate/restored FULL and fresh STA, independent physical/capacity/scope checks, fixed original R1 envelopes and recomputed unchanged SB/CB-only decisions. Wire improvements are retained even when the registered vertical-only policy rejects. Shared imported-scope cost includes the empty-source serialization control and both real roles; it is not cold standalone or whole pristine-native cost. A remaining terminal-cut excess does not prove a feasible one-crossing replacement. No original actor or old decision changed.'))
print(dict(passed=True, results={n: {k: r[k] for k in ['CPD_ns', 'resources', 'wire_delta', 'vector_exact']} for n, r in results.items()}), flush=True)
