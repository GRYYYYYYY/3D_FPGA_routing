"""Measure the actual composition; never predict its cost by subtraction."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from complete_flow_equivalence_v1 import compare

root = D/'complete_serial_lazy_source_snapshot_01'
closed, observed = read(root/'queue/completion.json'), read(root/'queue/results.json')
plan = read(root/'plan.json')
assert set(observed) == set(plan['fixed_order'])
references = dict(eltwise_domain=D/'complete_serial_lazy_dev_01/delay_seed_paired',
                  softmax_domain=D/'complete_serial_lazy_transfer_dev_01/softmax_paired')
files = [Path(__file__).resolve(), D/'complete_flow_equivalence_v1.py', root/'plan.json',
         root/'queue/completion.json', root/'queue/results.json']
results = {}
for name in plan['fixed_order']:
    actual, prior = root/name, references[name]
    measure = read(actual/'measurement/completion.json')
    files += [actual/'measurement/completion.json', actual/'config.json', prior/'config.json']
    if not observed[name]['passed']:
        results[name] = dict(status='configuration_failed', quality=None,
            actual_failed_seconds=measure['complete_command_wall_seconds'], failed_returncode=observed[name]['returncode'])
        continue
    a, b = [read(p/'explicit_policy_verification.json') for p in [actual, prior]]
    for proof in [a, b]:
        assert proof['passed'] and all(sha(f) == h for f, h in proof['source_sha256'].items())
    ca, cb = [read(p/'config.json') for p in [actual, prior]]
    assert ca['route_command'][1:] == cb['route_command'][1:]
    assert all(ca[k] == cb[k] for k in ['domain_mode', 'domain_feedback', 'seed_order', 'cache_mode', 'execution_policy'])
    for config, binding in [(ca, D/'source_snapshot_stage_01/binding.json'), (cb, D/'native_resource_census_stage_01/binding.json')]:
        assert sha(config['route_command'][0]) == read(binding)['binary_sha256']
    equivalence = compare(actual, prior)
    assert a['actual_native_work']['source_serialization_controls'] == 0
    assert a['actual_native_work']['source_snapshot_exports'] == a['actual_native_work']['native_transactions']
    results[name] = dict(status='complete_legal_configuration', CPD_ns=a['CPD_ns'], resources=a['resources'],
        complete_wall_seconds=a['complete_wall_seconds'], reference_complete_wall_seconds=b['complete_wall_seconds'],
        observed_seconds_difference=a['complete_wall_seconds']-b['complete_wall_seconds'],
        sampled_tree_PSS_peak_kib=a['sampled_tree_PSS_peak_kib'], missing_memory_observations=a['missing_memory_observations'],
        actual_native_work=a['actual_native_work'], equivalence=equivalence,
        same_workload_backend_time_comparison_valid=equivalence['same_complete_execution_states_and_workload'])
    files += [actual/'explicit_policy_verification.json', prior/'explicit_policy_verification.json', *map(Path, equivalence['compared_files'])]
write(root/'comparison.json', dict(passed=True, execution_cohort_all_legal=closed['passed'], registered_roles=2,
    successful_legal_roles=sum(r['status'] == 'complete_legal_configuration' for r in results.values()),
    results=results, native_calls_new=0, source_sha256={str(f): sha(f) for f in files},
    qualification='Actual source-snapshot plus ON-first full configurations, compared with actual Census ON-first references. Exact source/candidate/final vectors/ordered routes, requests/domains, decisions, actual skips/rollbacks and common native workload are checked, not inferred from final quality. Any divergence and failed role remains explicit and bars a same-workload time claim. Distinct binaries bound separately; same remaining route options. No empty controls, borrowed costs or component-time subtraction. Single known-circuit shared-host measurements, no statistical speedups or independent test claim.'))
print(dict(passed=True, results=results), flush=True)
