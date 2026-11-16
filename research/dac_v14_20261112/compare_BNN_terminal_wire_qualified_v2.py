"""Reconcile the real recovery result with qualified original quality and GNU time."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from complete_resource_prefix_quality_equivalence_v2 import compare
from endpoint_timing_policy_streaming_v2 import compare as compare_vectors
from orphaned_flow_time_evidence_v2 import parse_gnu_time


def check_config_pair(actual, baseline):
    assert actual['terminal_resource_policy'] == 'endpoint_wire_before_timing'
    assert 'terminal_resource_policy' not in baseline
    excluded = {'input_sha256', 'terminal_resource_policy'}
    assert {k:v for k,v in actual.items() if k not in excluded} == {k:v for k,v in baseline.items() if k not in excluded}
    assert all(actual['input_sha256'].get(k) == v for k,v in baseline['input_sha256'].items())


def observed_gnu(case):
    case = Path(case)
    parsed = parse_gnu_time((case/'measurement/gnu_time.txt').read_text())
    reg = read(case/'measurement/registration.json')
    assert parsed['exit_status'] == 0
    assert parsed['command_text'] == ' '.join(reg['command'])
    cmd = reg['command']
    assert Path(cmd[cmd.index('--output')+1]).resolve() == (case/'flow').resolve()
    assert sha(cmd[cmd.index('--config')+1]) == sha(case/'config.json')
    return parsed


def cost_comparison(actual, baseline, baseline_time, prefix_exact):
    # Clock scopes are explicit: never subtract GNU wall from observer wall.
    new_gnu, old_gnu = observed_gnu(actual), observed_gnu(baseline)
    for key in ['elapsed_seconds', 'display_resolution_seconds', 'command_text', 'exit_status']:
        assert old_gnu[key] == baseline_time[key]
    assert baseline_time['original_observer_receipt_available'] is False
    assert baseline_time['complete_observer_wall_seconds'] is None
    assert baseline_time['sampled_tree_PSS_peak_kib'] is None
    assert baseline_time['undisturbed_timing'] is False
    return dict(actual_GNU_time=new_gnu, baseline_GNU_time=old_gnu,
        descriptive_GNU_seconds_difference=new_gnu['elapsed_seconds']-old_gnu['elapsed_seconds'] if prefix_exact else None,
        baseline_observer_wall_seconds=None, baseline_sampled_tree_PSS_peak_kib=None,
        baseline_original_observer_lost=True, baseline_overlap_qualification_retained=True,
        matched_clock_scope='GNU-time of each complete algorithm command',
        statistical_or_undisturbed_speedup_established=False)


def main():
    root = D/'BNN_terminal_wire_qualified_comparison_02'; plan = read(root/'plan.json')
    assert not (root/'completion.json').exists()
    recovery = Path(plan['recovery_queue']); terminal = read(recovery/'completion.json')
    assert terminal['status'] == 'registered_never_executed_tasks_terminal'
    observed = terminal['results']['terminal_wire']
    actual, baseline = Path(plan['actual']), Path(plan['baseline'])
    verified = bool(observed['returncode'] == 0 and observed.get('verification') and observed['verification']['returncode'] == 0)
    files = [Path(__file__).resolve(), root/'plan.json', recovery/'completion.json',
        D/'complete_resource_prefix_quality_equivalence_v2.py', D/'endpoint_timing_policy_streaming_v2.py',
        D/'orphaned_flow_time_evidence_v2.py']
    result = dict(passed=True, registered_roles=1, verified_complete_roles=int(verified),
        native_calls_new=0, new_independent_inputs=0, actual_execution_receipt=observed)
    if not verified:
        measure_path = actual/'measurement/completion.json'
        measurement = read(measure_path) if measure_path.exists() else None
        result.update(status='failed_or_unverified_configuration_retained', actual_quality=None,
            quality_comparison_available=False, single_change_attribution_available=False,
            actual_observer_wall_seconds=measurement.get('complete_command_wall_seconds') if measurement else None)
        if measurement: files.append(measure_path)
    else:
        a = read(actual/'completion.json'); quality_path = Path(plan['baseline_quality_receipt'])
        b = read(quality_path); time_path = quality_path.parent/'original_time_evidence.json'; old_time = read(time_path)
        assert a['passed'] and a['complete_configuration_verified']
        assert b['passed'] and b['complete_configuration_quality_verified']
        assert not (baseline/'completion.json').exists(), 'Do not substitute or manufacture a complete observer receipt'
        assert all(sha(p) == h for p,h in b['source_sha256'].items())
        assert all(sha(p) == h for p,h in old_time['source_sha256'].items())
        check_config_pair(read(actual/'config.json'), read(baseline/'config.json'))
        shared = compare(actual, baseline, quality_path)
        write(root/'resource_prefix.json', shared)
        exact = shared['resource_prefix_actual_states_requests_and_native_work_exact']
        va_path, vb_path = [Path(p['final_state'])/'endpoint_vector.json' for p in [b,a]]
        endpoints = compare_vectors(read(va_path), read(vb_path)); write(root/'final_endpoints.json', endpoints)
        assert endpoints['compatible'], 'Different endpoint/constraint identities cannot support the paired comparison'
        costs = cost_comparison(actual, baseline, old_time, exact)
        result.update(status='qualified_complete_comparison', quality_comparison_available=True,
            resource_prefix_exact=exact, single_change_attribution_available=exact,
            actual={k:a[k] for k in ['final_state','CPD_ns','resources','complete_wall_seconds','terminal_wire_commits',
                'sampled_tree_PSS_peak_kib','sampled_tree_RSS_peak_kib','waited_process_RSS_high_water_kib','missing_memory_observations']},
            baseline_quality={k:b[k] for k in ['final_state','CPD_ns','resources']},
            terminal_minus_baseline_resources={k:a['resources'][k]-b['resources'][k] for k in a['resources']},
            terminal_minus_baseline_CPD_ns=a['CPD_ns']-b['CPD_ns'],
            endpoint_summary={k:v for k,v in endpoints.items() if k != 'changes'},
            full_endpoint_changes=str(root/'final_endpoints.json'), complete_cost_comparison=costs)
        files += [actual/'completion.json', actual/'config.json', baseline/'config.json', quality_path, time_path,
            root/'resource_prefix.json', root/'final_endpoints.json', va_path, vb_path,
            *map(Path, shared['compared_files'])]
        for case in [actual,baseline]:
            files += [case/'measurement/registration.json',case/'measurement/gnu_time.txt']
    result.update(source_sha256={str(p):sha(p) for p in dict.fromkeys(files)}, qualification=plan['qualification'])
    write(root/'completion.json', result)
    print({k:result[k] for k in ['passed','status','verified_complete_roles','native_calls_new']}, flush=True)


if __name__ == '__main__': main()
