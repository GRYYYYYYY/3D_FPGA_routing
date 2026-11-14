#!/usr/bin/env python3
"""Validate real cross-observer anchor identity and reject actual problem mismatches."""
import copy
import shutil
import subprocess
import sys
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from native_problem_identity import problem_identity
from run_native_scope_policy_v4 import run_dir, input_identity

b = D / 'native_problem_identity_validation_01'
b.mkdir(exist_ok=False)
old = D / 'resource_first_timing_dev_01/timing'
reg = read(old / 'registration.json')
terminal = read(old / 'completion.json')
assert not terminal['passed'] and terminal['operator_stop'] == 'transaction_preparation_failed'
anchor = Path(reg['initial_state'])
current = Path(terminal['final_state'])
arun, crun = run_dir(anchor), run_dir(current)
assert read(anchor / 'completion.json')['passed'] and read(current / 'completion.json')['passed']
assert input_identity(arun) != input_identity(crun)
identity = problem_identity(arun)
assert identity == problem_identity(crun)
assert read(anchor / 'endpoint_vector.json')['constraints_sha256'] == read(current / 'endpoint_vector.json')['constraints_sha256']
test = b / 'metadata_test_copy'
test.mkdir()
for name in ['packed.net', 'placed.place']:
    shutil.copy2(crun / name, test / name)
manifest = read(crun / 'manifest.json')
write(test / 'manifest.json', manifest)
assert problem_identity(test) == identity
rejected = []
changed = copy.deepcopy(manifest)
changed['command'][changed['command'].index('--clock_modeling') + 1] = 'route'
write(test / 'manifest.json', changed)
assert problem_identity(test) != identity
rejected.append('clock_model_change')
changed = copy.deepcopy(manifest)
graph = changed['command'][changed['command'].index('--read_rr_graph') + 1]
changed['shared_inputs'][graph]['sha256'] = '0' * 64
write(test / 'manifest.json', changed)
try:
    problem_identity(test)
except AssertionError:
    rejected.append('graph_identity_mismatch')
else:
    raise AssertionError('Changed graph binding accepted')
write(test / 'manifest.json', manifest)
with (test / 'packed.net').open('ab') as stream:
    stream.write(b'\n')
try:
    problem_identity(test)
except AssertionError:
    rejected.append('packing_bytes_no_longer_match_seal')
else:
    raise AssertionError('Changed private input accepted')
plan = old / 'round_001/portfolio/portfolio.json'
menu = read(plan)
selected = menu['proposals'][0]
source_plan = Path(selected['plan'])
assert read(source_plan)['source_state'] == str(current)
result = subprocess.run([sys.executable, str(D / 'prepare_native_group_step_v2.py'), '--plan', str(source_plan),
                         '--anchor-state', str(anchor), '--output', str(b / 'prepared_step'), '--objective', 'weighted_soft'],
                        capture_output=True, text=True, timeout=1800)
assert result.returncode == 0, result.stderr
prepared = read(b / 'prepared_step/registration.json')
assert prepared['problem_identity'] == identity
assert prepared['roles']['current_group']['original_budget']['CPD_s'] == reg['anchor']['CPD_s']
files = [Path(__file__).resolve(), D / 'native_problem_identity.py', D / 'prepare_native_group_step_v2.py',
         old / 'registration.json', old / 'completion.json', source_plan, arun / 'manifest.json', crun / 'manifest.json',
         b / 'prepared_step/registration.json']
write(b / 'completion.json', dict(passed=True, same_real_problem_cross_backend_accepted=True,
      prior_false_failure='Old equality key included observers, runtime libraries and inherited historical shared inputs despite equal actual graph/packing/placement/circuit/architecture/effectiveoptions/constraints.',
      negative_cases=rejected, exact_failed_plan_now_prepared=True, actual_plan=str(source_plan),
      native_calls=0, route_calls=0, source_sha256={str(p): sha(p) for p in files},
      qualification='Only the anchor problem identity guard changed; all backend/runtime versions remain separately bound. No search, resource envelope, timing values, native FULL/STA or acceptance rule changed. Preserve the first accepted point and failed preparation; formal whole-configuration version/timing still explicit.'))
print(dict(passed=True, negatives=rejected, new_native_calls=0), flush=True)
