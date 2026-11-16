"""Register the missing domain engineering arm without repeating native work."""
import copy
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

root = D/'complete_BNN_domain_engineering_01'
assert not root.exists()
native_path = D/'complete_BNN_closed_stream_flow_01/configs/bnn_native_closed_stream.json'
reference = D/'complete_resource_timing_full_flow_01/bnn_domain'
native, original = read(native_path), read(reference/'config.json')
assert read(reference/'completion.json')['passed']
assert read(D/'orphaned_BNN_engineering_comparison_01/completion.json')['all_actual_work_comparisons_exact']
config = copy.deepcopy(native)
config.update(domain_mode=original['domain_mode'], domain_feedback=original['domain_feedback'])
ignored = {'input_sha256', 'cache_mode', 'preprocessing_strategy',
           'endpoint_loader_strategy', 'metadata_cache_strategy'}
assert {k:v for k,v in config.items() if k not in ignored} == {k:v for k,v in original.items() if k not in ignored}
assert all(config['input_sha256'].get(k) == v for k,v in original['input_sha256'].items())
assert [k for k in config if config[k] != native[k]] == ['domain_mode', 'domain_feedback']
assert 'terminal_resource_policy' not in config
files = [Path(__file__).resolve(), native_path, reference/'config.json', reference/'completion.json',
         D/'orphaned_BNN_engineering_comparison_01/completion.json',
         D/'queue_BNN_domain_engineering_01.py', D/'compare_BNN_domain_engineering_01.py',
         D/'complete_resource_timing_equivalence_v1.py', D/'endpoint_timing_policy_streaming_v2.py',
         D/'measure_process_tree_v1.py', D/'run_complete_resource_timing_joint_stream_v1.py',
         D/'verify_complete_resource_timing_joint_stream_v1.py']
for path in files:
    if path.suffix == '.py': compile(path.read_text(), str(path), 'exec')
# Avoid reading large RRG/binaries during the currently measured flow. The
# existing digests are preserved and checked under the serial lock before run.
config['input_sha256'].update({str(p):sha(p) for p in files})
root.mkdir(); (root/'configs').mkdir()
path = root/'configs/bnn_domain_closed_stream.json'; write(path, config)
qualification = ('One previously unexecuted complete domain engineering arm. Reuse the completed '
    'native closed-stream implementation: one-pass graph generation, explicit same-command caches '
    'and streaming-v2 observations. Only domain_mode/domain_feedback differ from that native '
    'configuration. Preserve the historical full-domain policy, binaries, physical inputs, seed11, '
    'count8/1.01 convergence, current-STA selection, acceptance and stopping rules. No new '
    'terminal-wire selection, owner escalation or grouping heuristic. Rebuild indexes and fresh '
    'initial route inside one measured command; no historical candidates/routes/query history. '
    'Run after all existing cross-input and mechanism queues, under the existing serial lock. '
    'Retain failures and divergence; require complete endpoint/state/request/native-work and graph '
    'payload equivalence against the original domain arm before a same-behavior cost comparison. '
    'Native is not rerun. Its earlier observer loss/PSS gap/overlap remain qualifications; this '
    'single observation does not revise the original matched 22.95 percent overhead or establish '
    'a clean optimized-pair ratio. Stable interleaved timing remains separate future work. '
    'No overall research date/call/matrix stopping condition.')
plan = dict(fixed_order=['bnn_domain_closed_stream'], config=str(path),
    predecessor=str(D/'portable_robot_p1_pair_01/queue'),
    historical_domain_reference=str(reference), native_engineering_reference=str(native_path.parent.parent/'bnn_native_closed_stream'),
    qualification=qualification, source_sha256={str(p):sha(p) for p in [path, *files]})
write(root/'plan.json', plan)
write(root/'preflight.json', dict(passed=True, native_calls=0, registered_roles=1,
    only_algorithmic_difference_from_native=['domain_mode', 'domain_feedback'],
    original_domain_algorithm_rules_exact=True, original_domain_input_bindings_preserved=True,
    terminal_wire_or_owner_algorithm_change=False,
    large_input_rehash_deferred_to_serial_admission=True, actual_full_flow_validated=False,
    source_sha256={str(root/'plan.json'):sha(root/'plan.json'), **plan['source_sha256']}))
print(dict(prepared=True, root=str(root), native_calls=0), flush=True)
