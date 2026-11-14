#!/usr/bin/env python3
"""Distinguish a serialization-sensitive legal gain from graph-export and guide claims."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from endpoint_timing_policy_streaming_v2 import compare
from actual_route_tree_identity import tree_identity
from run_native_scope_policy_v4 import run_dir

out = D / 'fused_eltwise_order_mechanism_01.json'
assert not out.exists()
diagnostic = D / 'serialization_order_diagnostic_02/completion.json'
proof = read(diagnostic)
assert proof['passed']
assert [row['actual_candidate_reference_matches'] for row in proof['results']] == [['old'],['new'],['old']]
old = D / 'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8'
new = D / 'fused_resource_development_01/eltwise_A0_feedback_K8'
native = D / 'fused_resource_development_01/eltwise_A0_native_only_K8'
files = [Path(__file__).resolve(), diagnostic, D / 'serialization_order_diagnostic_01/failure.json',
    D / 'actual_route_tree_identity.py', D / 'multiobjective_archive_52/completion.json']
for actor in [old, new, native]:
    assert read(actor / 'completion.json')['passed']
    files += [actor / 'registration.json', actor / 'completion.json', actor / 'attempts.json']
rows = []
for index in [0, 1]:
    otx, ntx = (actor / f'round_{index:03d}/candidate_00' for actor in [old,new])
    assert sha(otx / 'request.txt') == sha(ntx / 'request.txt')
    assert sha(otx / 'domain.txt') == sha(ntx / 'domain.txt')
    for name in ['reuse_off','reuse_on']:
        os, ns = (tx / (name + '_evaluation') for tx in [otx,ntx])
        ot, nt = (tree_identity(run_dir(state) / 'routed.route') for state in [os,ns])
        changed = [net for net in ot if ot[net] != nt[net]]
        comparison = compare(read(os / 'endpoint_vector.json'), read(ns / 'endpoint_vector.json'))
        old_log, new_log = (run_dir(tx / name) / 'joint_native.log' for tx in [otx,ntx])
        old_lines, new_lines = old_log.read_text().splitlines(), new_log.read_text().splitlines()
        seed_rows = lambda lines: [line.split()[2:] for line in lines if line.startswith('KEEP 6719 ')]
        ok, nk = seed_rows(old_lines), seed_rows(new_lines)
        rows.append(dict(round=index, arm=name, changed_physical_tree_nets=changed,
            full_vector_comparison=comparison,
            net6719_retained_seed_rows_same_multiset=sorted(ok)==sorted(nk),
            net6719_retained_seed_row_order_same=ok==nk,
            released_domain_queries=[line for line in new_lines if line.startswith('DOMAIN_RELEASE ')],
            old_query_rows=[line for line in old_lines if line.startswith('QUERY ')],
            new_query_rows=[line for line in new_lines if line.startswith('QUERY ')]))
        files += [otx/'request.txt',ntx/'request.txt',otx/'domain.txt',ntx/'domain.txt',old_log,new_log,
            os/'completion.json',ns/'completion.json',os/'endpoint_vector.json',ns/'endpoint_vector.json']
assert [row['changed_physical_tree_nets'] for row in rows] == [[],[],[],[6719]]
assert all(not row['released_domain_queries'] for row in rows)
nc, gc = read(native / 'completion.json'), read(new / 'completion.json')
state = Path(gc['final_state'])
oldstate = Path(read(old / 'completion.json')['final_state'])
quality = read(run_dir(state) / 'independent_audit.json')['physical_metrics']
write(out, dict(passed=True, rows=rows, isolated_serialization_swap_recovers_old_candidate=True,
    native=dict(state=nc['final_state'], CPD_ns=nc['final_CPD_s']*1e9, resources=nc['final_resources'],
        complete_imported_workflow_seconds=nc['complete_imported_algorithm_workflow_seconds'],native_children=nc['native_analysis_children']),
    guided=dict(state=gc['final_state'], CPD_ns=gc['final_CPD_s']*1e9, resources=gc['final_resources'],
        complete_imported_workflow_seconds=gc['complete_imported_algorithm_workflow_seconds'],native_children=gc['native_analysis_children']),
    old_guided_resources=read(old/'completion.json')['final_resources'],
    native_to_guided_tradeoff=dict(wire=gc['final_resources']['wirelength']-nc['final_resources']['wirelength'],
        SB_pairs=gc['final_resources']['SB_pairs']-nc['final_resources']['SB_pairs'],
        CB_sources=gc['final_resources']['CB_sources']-nc['final_resources']['CB_sources']),
    new_vs_old_guided_setup_comparison=compare(read(oldstate/'endpoint_vector.json'),read(state/'endpoint_vector.json')),
    complete_single_configuration_algorithm_seconds=None,
    source_sha256={str(path):sha(path) for path in files}, native_calls_for_this_binding=0,
    qualification='New24SB/965CB point uses23lesswire than the older217214 point at equal CPD, but the three-arm same-binary intervention attributes this difference to serialized retained-tree order, not an improved guide score or reduced graph text. Causal evidence concerns search-choice sensitivity; equal complete weighted path costs or a specific heap-tie mechanism are not proved. Same seed rows in a different order may affect tie resolution and heuristic termination. Exact ordered route bytes stay in query/cache identity; topology/full-vector equivalence alone is insufficient for future search-state equivalence. Two own-current strategies use the same native search/scope/selector/budgets/menu and their own states after divergence. Imported actor times include their actual failures/checks/seals and are not cold full routing or formal repeat timing. Fewer native child processes do not imply fewer STA evaluations: fused workers also reobserve restored source. The first standalone adapter omitted required output folders and failed; fixed adapter02 supplies them and all3native candidates pass, with original failed cost/logs retained.'))
print(dict(passed=True,native_to_guided=(gc['final_resources']['wirelength']-nc['final_resources']['wirelength'],
    gc['final_resources']['SB_pairs']-nc['final_resources']['SB_pairs'],gc['final_resources']['CB_sources']-nc['final_resources']['CB_sources']),
    seed_order=[(row['round'],row['arm'],row['net6719_retained_seed_rows_same_multiset'],row['net6719_retained_seed_row_order_same'])for row in rows]),flush=True)
