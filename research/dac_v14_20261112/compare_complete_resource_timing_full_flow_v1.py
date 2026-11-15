"""Read-only paired report for the actual fresh BNN complete configurations."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from complete_flow_equivalence_v1 import equal_state
from endpoint_timing_policy import compare as compare_endpoints
from run_native_scope_policy_v4 import run_dir


def compare_configs(native, domain):
    differing = {key: [native.get(key), domain.get(key)]
                 for key in native.keys() | domain.keys() if native.get(key) != domain.get(key)}
    assert differing == dict(domain_mode=['unrestricted', 'paired'], domain_feedback=[False, True]), differing
    assert native['external_history_allowed'] is domain['external_history_allowed'] is False
    assert native['initial_route_imported'] is domain['initial_route_imported'] is False
    assert native['cache_mode'] == domain['cache_mode'] == 'build_inside_flow'
    return differing


def summarize(root):
    root = Path(root)
    assert not (root/'comparison.json').exists(), 'Do not replace a previous scientific report'
    plan, closed, results = [read(root/name) for name in ['plan.json', 'queue/completion.json', 'queue/results.json']]
    assert plan['fixed_order'] == ['bnn_native', 'bnn_domain'] and set(results) == set(plan['fixed_order'])
    registered = read(root/'queue/registration.json')
    assert all(sha(path) == digest for path, digest in registered['source_sha256'].items())
    configs = {name: read(plan['cases'][name]) for name in plan['fixed_order']}
    config_differences = compare_configs(configs['bnn_native'], configs['bnn_domain'])
    files = [Path(__file__).resolve(), D/'complete_flow_equivalence_v1.py', D/'endpoint_timing_policy.py',
             root/'plan.json', root/'queue/registration.json', root/'queue/completion.json', root/'queue/results.json']
    outcomes = {}
    for name in plan['fixed_order']:
        case = root/name
        config = read(case/'config.json')
        assert config == configs[name]
        files += [case/'config.json', Path(plan['cases'][name])]
        measured = case/'measurement/completion.json'
        measure = read(measured) if measured.exists() else None
        if measure:
            files.append(measured)
        if not results[name]['passed']:
            outcomes[name] = dict(status='configuration_failed', quality=None,
                actual_failed_seconds=None if measure is None else measure['complete_command_wall_seconds'],
                failed_returncode=results[name]['returncode'],
                qualification='Failed actual role retained in denominator; missing cost is unknown, not zero.')
            continue
        proof = read(case/'completion.json')
        assert proof['passed'] and proof['complete_configuration_verified'] and measure and measure['passed']
        assert all(sha(path) == digest for path, digest in proof['source_sha256'].items())
        assert proof['complete_wall_seconds'] == measure['complete_command_wall_seconds']
        assert proof['phase_binary_sha256'] == config['phase_binary_sha256']
        files.append(case/'completion.json')
        outcomes[name] = dict(status='complete_legal_configuration', **{key: proof[key] for key in [
            'initial_state', 'resource_final_state', 'final_state', 'CPD_ns', 'resources',
            'complete_wall_seconds', 'resource_actual_work', 'resource_accepted_steps',
            'timing_accepted_steps', 'timing_attempted_proposals', 'phase_binary_sha256',
            'waited_process_RSS_high_water_kib', 'sampled_tree_RSS_peak_kib',
            'sampled_tree_PSS_peak_kib', 'missing_memory_observations', 'observer_CPU_seconds']})
        outcomes[name]['fixed_absolute_timing_limits'] = read(case/'flow/absolute_timing_limits.json')
        files.append(case/'flow/absolute_timing_limits.json')
        for state in [proof['initial_state'], proof['resource_final_state'], proof['final_state']]:
            state = Path(state)
            files += [state/'completion.json', state/'endpoint_vector.json', run_dir(state)/'manifest.json', run_dir(state)/'routed.route']
    native, domain = [outcomes[name] for name in plan['fixed_order']]
    pair = dict(quality_comparison_available=False, reason='One or both complete roles failed')
    if all(outcome['status'] == 'complete_legal_configuration' for outcome in [native, domain]):
        initial = equal_state(native['initial_state'], domain['initial_state'])
        endpoints = compare_endpoints(read(Path(native['final_state'])/'endpoint_vector.json'),
                                      read(Path(domain['final_state'])/'endpoint_vector.json'))
        comparable = all(initial.values()) and endpoints['compatible']
        pair = dict(quality_comparison_available=comparable, initial_state_comparison=initial,
            final_endpoint_comparison=endpoints, config_differences=config_differences,
            final_output_comparison=equal_state(native['final_state'], domain['final_state']),
            descriptive_domain_minus_native_seconds=domain['complete_wall_seconds']-native['complete_wall_seconds'],
            same_compute_opportunity_claim=False,
            timing_caps_are_each_actual_resource_final=True)
        if comparable:
            delta = {key: domain['resources'][key]-native['resources'][key] for key in native['resources']}
            cpd_delta = domain['CPD_ns']-native['CPD_ns']
            axes = [cpd_delta, *delta.values()]
            pair.update(domain_minus_native_CPD_ns=cpd_delta, domain_minus_native_resources=delta,
                four_axis_quality_relation=('domain_dominates_native' if all(v <= 0 for v in axes) and any(v < 0 for v in axes)
                    else 'native_dominates_domain' if all(v >= 0 for v in axes) and any(v > 0 for v in axes)
                    else 'equal' if all(v == 0 for v in axes) else 'tradeoff'))
        else:
            pair['reason'] = 'Actual fresh root or final endpoint identity differs; paired quality delta withheld'
    payload = dict(passed=True, execution_cohort_all_legal=closed['passed'], registered_roles=2,
        successful_legal_roles=sum(x['status'] == 'complete_legal_configuration' for x in outcomes.values()),
        results=outcomes, pair=pair, source_sha256={str(path): sha(path) for path in files}, native_calls_new=0,
        qualification='Actual fresh count8/1.01/seed11 BNN whole-command pair. Each quality/time/memory tuple and actual work belongs to that configuration; failures retain denominator/cost without invented quality. Same explicit physical inputs, phase binaries, initial routing and base policies; treatment changes resource domain plus timing feedback, so this is a combined algorithm comparison, not one-factor attribution or equal compute. Quality deltas require actual exact initial route/full vector and compatible final endpoint identities. Each timing resource cap follows its own actual resource final. Graph/index/query construction, actual candidates/checks/rejections/rollback/seals remain within whole measured commands. Upstream RR/pack/place generation separate; uncontrolled OS cache/shared host, descriptive observations not statistical speedups. Historical imported BNN quality/costs are not substituted, and native/paired convergence remains a registered menu property, not global optimality.')
    write(root/'comparison.json', payload)
    print(dict(passed=True, registered_roles=2, successful_legal_roles=payload['successful_legal_roles'], pair=pair), flush=True)
    return payload

if __name__ == '__main__':
    summarize(D/'complete_resource_timing_full_flow_01')
