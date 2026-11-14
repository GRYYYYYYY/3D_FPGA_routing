#!/usr/bin/env python3
"""Bind actual tested native export scope; historical build receipt remains unchanged."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

output = D / 'export_policy_native_binding_01.json'
assert not output.exists()
proofs = ['export_policy_tiny_01/completion.json', 'export_policy_timing_01/completion.json',
    'export_policy_resource_01/completion.json', 'export_policy_large_queue_01/completion.json',
    'actual_route_tree_identity_validation_01.json']
for name in proofs:
    receipt = read(D / name)
    assert receipt['passed']
    assert all(sha(path) == digest for path, digest in receipt['source_sha256'].items())
stage = D / 'export_policy_stage_01'
binding = read(stage / 'binding.json')
assert sha(stage / 'bin/vpr') == binding['binary_sha256']
source = D / 'export_policy_workspace_01'
assert all(sha(source / name) == digest for name, digest in binding['source_sha256'].items())
files = [Path(__file__).resolve(), stage / 'binding.json', stage / 'build_result.json',
    D / 'export_policy_analysis_pool.py', D / 'pool_state_evaluator_v7.py', D / 'endpoint_timing_policy_streaming_v2.py'] + [D / name for name in proofs]
result = dict(passed=True, status='actual_native_export_policy_scope_validated', binary_sha256=binding['binary_sha256'],
    source_sha256={str(path): sha(path) for path in files},
    actual_scope=['tiny full/compact source/candidate/restored and infeasible rollback/release/default recovery',
        'BNN free-path4network CPD-changing transaction', 'BNN8network automatic selective domain-release resource transaction',
        'explicit full/compact candidate-view binding rejects forged flag',
        'independent candidate LOAD/FULL/freshSTA frontier/constraints/fullgraph equality; following source exact'],
    compact_retains=['native FULL', 'fresh setup/hold STA', 'all JSON per-pin rows', 'all endpoint/domain identities',
        'full numeric precision', 'constraints', 'actual candidate and restored-source gates', 'physical/resource/scope audits'],
    compact_omits_only='unused full timing graph text; cannot feed a timing-cone selector without a requested full export',
    not_validated=['forced-target-path timing operator', 'general nonzero-RC/multilayer/flat routing', 'cold whole-configuration speedup'],
    new_native_calls=0, qualification='Proof binding only. Original built_not_native_validated receipt retained as historical build fact. Individual actual candidate/worker/time identities stay separate; export and decoder engineering gains do not prove quality improvement or formal end-to-end speedup.')
write(output, result)
write(stage / 'native_validation_binding_01.json', dict(result, binding=str(output), binding_sha256=sha(output)))
print(dict(passed=True, binary_sha256=binding['binary_sha256']), flush=True)
