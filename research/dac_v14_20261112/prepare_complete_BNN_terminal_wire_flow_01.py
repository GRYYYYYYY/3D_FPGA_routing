"""Freeze an actual fresh full-flow test of terminal wire retention before timing."""
import copy
import subprocess
import sys
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

root = D/'complete_BNN_terminal_wire_flow_01'
assert not root.exists()
baseline_config = D/'complete_BNN_closed_stream_flow_01/configs/bnn_native_closed_stream.json'
original = read(baseline_config)
proof = D/'terminal_resource_handoff_validation_01/completion.json'
validated = read(proof)
assert validated['passed'] and validated['foreign_flow_rejected']
assert all(sha(f) == h for f, h in validated['source_sha256'].items())
assert all(sha(f) == h for f, h in original['input_sha256'].items())
files = [Path(__file__).resolve(), baseline_config, proof] + [D/name for name in [
    'queue_complete_BNN_terminal_wire_flow_01.py',
    'run_complete_resource_terminal_wire_timing_v1.py',
    'verify_complete_resource_terminal_wire_timing_v1.py',
    'compare_BNN_terminal_wire_full_flow_v1.py',
    'complete_resource_prefix_equivalence_v1.py',
    'terminal_resource_handoff_v1.py',
    'select_terminal_resource_alternative_v2.py',
    'state_resource_assurance.py',
    'endpoint_timing_policy_streaming_v2.py']]
for script in files:
    if script.suffix == '.py': compile(script.read_text(), str(script), 'exec')
for name in ['run_complete_resource_terminal_wire_timing_v1.py',
             'verify_complete_resource_terminal_wire_timing_v1.py',
             'select_terminal_resource_alternative_v2.py']:
    subprocess.run([sys.executable, str(D/name), '--help'], check=True, stdout=subprocess.DEVNULL)
config = copy.deepcopy(original)
config['terminal_resource_policy'] = 'endpoint_wire_before_timing'
config['input_sha256'].update({str(f): sha(f) for f in files})
assert all(config[k] == v for k, v in original.items() if k != 'input_sha256')
assert all(config['input_sha256'].get(k) == v for k, v in original['input_sha256'].items())
root.mkdir(); (root/'configs').mkdir()
path = root/'configs/bnn_native_terminal_wire.json'; write(path, config)
qualification = ('One development full-flow configuration on the same BNN inputs, seed11, count8, '
    'phase binaries, original resource policy and current-STA timing portfolio as closed-stream control. '
    'After its own resource search closes, select the lowest-wire already evaluated same-source legal '
    'candidate with equal SB/CB, unchanged endpoint identity, nonregressing CPD/setup/hold violations '
    'and original caps; tie by original attempt index then role; retain original terminal if none. '
    'Reevaluate the actual selected state with FULL/STA and physical audit, then reselect timing targets '
    'from that state to convergence. All selection, checks, loading, rejection and rollback costs are '
    'inside one new measured command. No external candidate, predicted timing or old quality/time is '
    'injected. Compare common actual resource prefix independently against completed closed-stream '
    'control; retain differing trajectories and failures, denominator1. Existing 24-wire local '
    'candidate motivates this development test but does not predict final gain or independent '
    'confirmation. Report actual whole wall/PSS/RSS and sampling gaps; one shared-host observation '
    'does not establish statistical speedup. Run after robot release ablation using existing serial lock.')
write(root/'plan.json', dict(fixed_order=['bnn_native_terminal_wire'], config=str(path),
    predecessor=str(D/'robot_domain_release_ablation_01/queue'),
    baseline_completion=str(D/'complete_BNN_closed_stream_flow_01/bnn_native_closed_stream/completion.json'),
    prepared_files=list(map(str, files)), qualification=qualification))
write(root/'preflight.json', dict(passed=True, native_calls=0, registered_roles=1,
    actual_full_flow_validated=False, prior_positive_and_two_zero_candidate_handoffs_verified=True,
    foreign_flow_rejected=True, three_CLI_smoke_passed=True,
    original_config_and_source_bindings_preserved=True,
    source_sha256={str(f): sha(f) for f in [path, root/'plan.json', *files]}))
print(dict(prepared=True, root=str(root), native_calls=0), flush=True)
