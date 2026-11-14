#!/usr/bin/env python3
"""Discriminate branch serialization from actual mechanism changes on the first divergent net."""
import fcntl
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from actual_route_tree_identity import tree_identity
from endpoint_timing_policy_streaming_v2 import load, compare
from run_native_scope_policy_v4 import run_dir

b = D / 'serialization_order_diagnostic_02'
b.mkdir(exist_ok=False)
lock = (b / 'owner.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
started = time.monotonic()
old = D / 'uniform_feedback_resource_dev_01/eltwise_A0_feedback_K8'
new = D / 'fused_resource_development_01/eltwise_A0_feedback_K8'
assert read(old / 'completion.json')['passed'] and read(new / 'completion.json')['passed']
old_source = old / 'round_000/candidate_00/reuse_on_evaluation'
new_source = new / 'round_000/candidate_00/reuse_on_evaluation'
old_route, new_route = (run_dir(state) / 'routed.route' for state in [old_source, new_source])
old_tree, new_tree = tree_identity(old_route), tree_identity(new_route)
assert old_tree == new_tree
ov, nv = (read(state / 'endpoint_vector.json') for state in [old_source, new_source])
assert all(ov[key] == nv[key] for key in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256'])
old_tx = old / 'round_001/candidate_00'
new_tx = new / 'round_001/candidate_00'
request, domain = old_tx / 'request.txt', old_tx / 'domain.txt'
assert sha(request) == sha(new_tx / 'request.txt') and sha(domain) == sha(new_tx / 'domain.txt')
pattern = r'^Net 6719 \(.*?\)\n.*?(?=^Net |\Z)'
ot, nt = old_route.read_text(), new_route.read_text()
old_block, new_block = (re.search(pattern, text, re.M | re.S) for text in [ot, nt])
assert old_block and new_block
swapped = b / 'native_source_with_only_6719_canonical_order.route'
swapped.write_text(nt[:new_block.start()] + old_block.group() + nt[new_block.end():])
assert tree_identity(swapped) == new_tree
files = [Path(__file__).resolve(), D / 'run_serialized_order_native_analysis_v2.py', D / 'actual_route_tree_identity.py',
    D / 'export_policy_native_binding_01.json', old / 'completion.json', new / 'completion.json',
    old_route, new_route, swapped, request, domain, old_source / 'endpoint_vector.json', new_source / 'endpoint_vector.json']
bound = {str(path): sha(path) for path in files}
write(b / 'registration.json', dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],
    source_sha256=bound, prior_harness_failure='serialization_order_diagnostic_01: callback output directories absent, native print_route target parent missing; source checker/search ran but callback could not complete. Original signal11, logs and cost retained. Version02 creates dedicated candidate/restored directories before launching, as the validated queue already does. Not a legal-candidate failure or research stop.',question='Only the second guided eltwise restoration differs: same scope, request, domain, source topology and full endpoint vector. Does serialized branch order change native tie choices, and can changing only net6719 order recover the old candidate?',
    cases=['old_canonical_source','native_serialized_source','native_source_only6719_canonical'],
    limits=dict(this_chain_native_VPR_maximum=1, combined_with_registered_BNN_parent_child_maximum=3,
        child_seconds=1800, memory_bytes=64*1024**3, disk_reserve_bytes=80*1024**3),
    qualification='New local three-arm intervention, not repeated whole experiments for reporting. Same current binary, inputs, physical topology, criticalities, domain and query order. Native standalone processes avoid adding a second loaded parent alongside the registered BNN actor. Existing cohorts remain unmodified.'))
references = {name: Path(read(actor / 'completion.json')['final_state']) for name, actor in [('old',old),('new',new)]}
reference_trees = {name: tree_identity(run_dir(state) / 'routed.route') for name, state in references.items()}
reference_vectors = {name: read(state / 'endpoint_vector.json') for name, state in references.items()}
results = []
for name, state, route in [('old_canonical_source',old_source,None),
    ('native_serialized_source',new_source,None),('native_source_only6719_canonical',new_source,swapped)]:
    assert all(sha(path) == digest for path, digest in bound.items())
    output = b / name
    command = [sys.executable, str(D / 'run_serialized_order_native_analysis_v2.py'), '--source', str(run_dir(state)),
        '--batch', str(output), '--native-cases', str(request), '--crossing-domain', str(domain), '--objective', 'weighted_soft']
    if route:
        command += ['--candidate-route', str(route)]
    t = time.monotonic()
    with (b / (name + '.log')).open('w') as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        write(b / 'status.json', dict(case=name,pid=child.pid,start_ticks=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19]))
        code = child.wait()
    receipt = read(output / 'completion.json')
    assert code == 0 and receipt['passed']
    native = run_dir(output)
    assert (native / 'candidate/native_state_gate.txt').read_text() == 'candidate FULL fresh_STA actual_installed_trees\n'
    assert (native / 'candidate_restored/native_state_gate.txt').read_text() == 'restored_source FULL fresh_STA actual_installed_trees\n'
    for suffix in ['native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo']:
        assert sha(native / suffix) == sha(native / 'candidate_restored' / suffix)
    actual_tree = tree_identity(native / 'candidate/routed.route')
    actual_vector = load(native / 'candidate/native_sta_frontier.jsonl')
    matches = [label for label, tree in reference_trees.items() if tree == actual_tree]
    for label in matches:
        assert all(actual_vector[key] == reference_vectors[label][key] for key in ['cpd_s','setup','hold','constraints_sha256'])
    lines = (native / 'joint_native.log').read_text().splitlines()
    assert lines[-1].startswith('COMPLETE 1 ') and lines[-1].endswith('occupancy_restored')
    results.append(dict(case=name, actual_candidate_reference_matches=matches, actual_candidate_CPD_ns=actual_vector['cpd_s']*1e9,
        known_reference_resources={label:read(run_dir(references[label])/'independent_audit.json')['physical_metrics'] for label in matches},
        complete_diagnostic_arm_seconds=time.monotonic()-t, source_native_receipt=str(output/'completion.json'),
        query_rows=[line for line in lines if line.startswith('QUERY ')], native_log=str(native/'joint_native.log')))
    write(b / 'results.json', results)
classification = ('net6719_serialization_order_causally_changes_native_tie_choice' if
    results[0]['actual_candidate_reference_matches']==['old'] and results[1]['actual_candidate_reference_matches']==['new'] and results[2]['actual_candidate_reference_matches']==['old'] else
    'serialization_hypothesis_not_resolved_by_this_intervention')
write(b / 'completion.json', dict(passed=True, classification=classification, results=results,
    source_sha256=bound, complete_local_diagnostic_seconds=time.monotonic()-started,
    new_standalone_native_processes=3, complete_single_configuration_algorithm_seconds=None,
    qualification='All3actual installed candidates pass native FULL/newSTA and restored-source equality. Exact topology/vector matches bind candidate resource metrics to their already independently audited reference, without borrowing creation time. A positive isolated6719 swap distinguishes serialization/seed tie handling from target selection, query coverage, domain release or new mathematical routing quality. Branch order can affect future decisions even when the current physical state and full timing vector agree. Research continues; no global stop or end-to-end speed claim.'))
print(dict(passed=True, classification=classification, matches=[row['actual_candidate_reference_matches'] for row in results]), flush=True)
