"""Report complete prospective circuit-pair outcomes, including failed roles."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from complete_flow_equivalence_v1 import equal_state

root = D/'complete_serial_additional_circuits_01'
closed, observed = read(root/'queue/completion.json'), read(root/'queue/results.json')
plan = read(root/'plan.json')
assert set(observed) == set(plan['fixed_order'])
files = [Path(__file__).resolve(), D/'complete_flow_equivalence_v1.py', root/'queue/completion.json',
         root/'queue/results.json', root/'plan.json']
results, pairs = {}, {}
for name in plan['fixed_order']:
    case = root/name
    config = read(case/'config.json')
    assert all(sha(f) == h for f, h in config['input_sha256'].items())
    assert sha(config['source_manifest']) == config['source_manifest_sha256']
    measure = read(case/'measurement/completion.json')
    files += [case/'config.json', case/'measurement/completion.json', Path(config['source_manifest'])]
    if not observed[name]['passed']:
        results[name] = dict(status='configuration_failed', quality=None,
            actual_failed_seconds=measure['complete_command_wall_seconds'],
            failed_returncode=observed[name]['returncode'])
        continue
    proof = read(case/'explicit_policy_verification.json')
    assert proof['passed'] and all(sha(f) == h for f, h in proof['source_sha256'].items())
    results[name] = dict(status='complete_legal_configuration', CPD_ns=proof['CPD_ns'],
        resources=proof['resources'], complete_wall_seconds=proof['complete_wall_seconds'],
        sampled_tree_PSS_peak_kib=proof['sampled_tree_PSS_peak_kib'],
        missing_memory_observations=proof['missing_memory_observations'],
        accepted_steps=proof['accepted_steps'], attempted_scopes=proof['attempted_scopes'],
        actual_native_work=proof['actual_native_work'], initial_state=proof['initial_state'], final_state=proof['final_state'])
    files.append(case/'explicit_policy_verification.json')
for circuit in ['conv_layer', 'robot_rl']:
    n, d = [results[circuit+'_'+role] for role in ['native', 'domain']]
    configs = [read(root/(circuit+'_'+role)/'config.json') for role in ['native', 'domain']]
    assert configs[0]['route_command'] == configs[1]['route_command']
    if not all(x['status'] == 'complete_legal_configuration' for x in [n, d]):
        pairs[circuit] = dict(quality_comparison_available=False, reason='One or both actual complete roles failed')
        continue
    initial = equal_state(n['initial_state'], d['initial_state'])
    matched = all(initial.values())
    pairs[circuit] = dict(quality_comparison_available=matched, initial_state_comparison=initial,
        domain_minus_native_resources={k: d['resources'][k]-n['resources'][k] for k in n['resources']} if matched else None,
        domain_minus_native_CPD_ns=d['CPD_ns']-n['CPD_ns'] if matched else None,
        descriptive_domain_minus_native_seconds=d['complete_wall_seconds']-n['complete_wall_seconds'],
        input_selection='Frozen additional known circuit, historical heldout directory name is not a new held-out designation')
write(root/'comparison.json', dict(passed=True, execution_cohort_all_legal=closed['passed'], registered_roles=4,
    successful_legal_roles=sum(r['status'] == 'complete_legal_configuration' for r in results.values()),
    results=results, pairs=pairs, source_sha256={str(f): sha(f) for f in files}, native_calls_new=0,
    qualification='Four prospective fixed-policy full measurements on two additional known circuits; each successful quality/time/memory tuple belongs to its actual command. Failed-role costs/denominators remain without invented quality. Only actual identical fresh roots support the paired quality delta. Same policy/input options and full own-current menus, not matched compute or statistical speedups. New identities relative to prior3complete-measurement circuits do not retroactively create an unseen benchmark split.'))
print(dict(passed=True, results=results, pairs=pairs), flush=True)
