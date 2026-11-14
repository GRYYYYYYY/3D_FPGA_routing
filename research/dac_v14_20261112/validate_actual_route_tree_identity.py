#!/usr/bin/env python3
"""Actual fused candidate/reconstruction equality plus meaningful trace mutations."""
import re
import time
from retained_prefix_workflow import D, read, write, sha
from actual_route_tree_identity import same_actual_trees

b = D / 'actual_route_tree_identity_validation_01'
b.mkdir(exist_ok=False)
started = time.monotonic()
tiny = D / 'export_policy_tiny_01/pool/job_0007/native/candidate/routed.route'
text = tiny.read_text()
blocks = re.split(r'(?=^Net \d+ )', text, flags=re.M)
reordered = b / 'reordered.route'
reordered.write_text(blocks[0] + ''.join(reversed(blocks[1:])))
assert same_actual_trees(tiny, reordered)
checks = {}
for name, modified in [
    ('switch_changed', text.replace('Switch: 0', 'Switch: 1', 1)),
    ('endpoint_pin_changed', text.replace('Net_pin_index: 1', 'Net_pin_index: 987', 1)),
    ('whole_net_missing', blocks[0] + ''.join(blocks[2:])),
    ('duplicate_net', text + blocks[1]),
]:
    target = b / (name + '.route')
    target.write_text(modified)
    try:
        equal = same_actual_trees(tiny, target)
    except AssertionError:
        equal = False
    assert not equal, name
    checks[name] = True
sealed = D / 'candidate_full_sta_bnn_03/completion.json'
assert read(sealed)['passed']
actual = D / 'candidate_full_sta_bnn_01/pool/job_0000/native/candidate/routed.route'
reconstructed = D / 'candidate_full_sta_bnn_03/transaction/fused_audit/candidate.route'
assert same_actual_trees(actual, reconstructed)
files = [__file__, D / 'actual_route_tree_identity.py', tiny, actual, reconstructed, sealed]
write(D / 'actual_route_tree_identity_validation_01.json', dict(passed=True,
    actual_large_candidate_and_independently_reconstructed_trees_exact=True,
    net_serialization_order_irrelevant=True, meaningful_negative_cases=checks,
    source_sha256={str(path): sha(path) for path in files}, native_calls=0,
    complete_component_validation_seconds=time.monotonic() - started,
    qualification='Checks actual root, every parent/child/switch edge and all terminal pin mappings per net. Physical node metadata, capacities, legality and timing still require separate native/independent gates; digest equivalence is not itself a physical proof.'))
print(dict(passed=True, negative_cases=len(checks)), flush=True)
