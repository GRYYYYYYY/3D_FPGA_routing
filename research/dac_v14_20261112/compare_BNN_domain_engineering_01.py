"""Same-role engineering equivalence; never fabricate an optimized paired cost."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from complete_resource_timing_equivalence_v1 import compare
from endpoint_timing_policy_streaming_v2 import compare as compare_endpoints

root = D/'complete_BNN_domain_engineering_01'; plan = read(root/'plan.json')
case = root/'bnn_domain_closed_stream'; reference = Path(plan['historical_domain_reference'])
observed = read(root/'queue/results.json')[case.name]
assert not (root/'comparison.json').exists()
files = [Path(__file__).resolve(), root/'queue/results.json', root/'plan.json',
         D/'complete_resource_timing_equivalence_v1.py', D/'endpoint_timing_policy_streaming_v2.py']
payload = dict(passed=True, registered_new_roles=1, successful_new_roles=int(observed['passed']),
    postprocessing_native_calls=0, optimized_pair_cost_ratio_established=False,
    stable_interleaved_timing_complete=False, statistical_speedup_established=False)
if not observed['passed']:
    measured = case/'measurement/completion.json'
    payload.update(failure_stage=observed['failure_stage'], actual_quality=None,
        command_passed=observed['command_passed'], verification_passed=observed['verification_passed'],
        actual_complete_seconds=read(measured)['complete_command_wall_seconds'] if measured.exists() else None,
        comparable_engineering_cost_observation=False)
    if measured.exists(): files.append(measured)
else:
    actual, old = [read(p/'completion.json') for p in [case, reference]]
    assert actual['passed'] and old['passed'] and read(case/'metadata_consumers.json')['all_within_measured_flow']
    configs = [read(p/'config.json') for p in [case, reference]]
    ignored = {'input_sha256', 'cache_mode', 'preprocessing_strategy', 'endpoint_loader_strategy', 'metadata_cache_strategy'}
    assert {k:v for k,v in configs[0].items() if k not in ignored} == {k:v for k,v in configs[1].items() if k not in ignored}
    assert all(configs[0]['input_sha256'].get(k) == v for k,v in configs[1]['input_sha256'].items())
    equivalent = compare(case, reference)
    receipt = root/'domain_downstream_equivalence.json'; write(receipt, equivalent)
    payloads = []
    for component, names in [('resource_flow/graph_audit_cache', ['nodes.npy','edges.npy','switches.npy']),
                             ('resource_flow/full_graph_cache', ['extra.npy','metadata.json']),
                             ('physical_query_graph', ['graph.bin'])]:
        for name in names:
            paths = [p/'flow'/component/name for p in [case, reference]]
            payloads.append(dict(component=component, file=name, byte_exact=sha(paths[0]) == sha(paths[1])))
            files.extend(paths)
    exact = bool(all(r['byte_exact'] for r in payloads) and equivalent['downstream_actual_states_requests_and_native_work_exact'])
    endpoint_rows = {}
    for label, other in [('historical_domain', reference), ('historical_native', D/'complete_resource_timing_full_flow_01/bnn_native')]:
        other_done = read(other/'completion.json'); assert other_done['passed']
        paths = [Path(c['final_state'])/'endpoint_vector.json' for c in [other_done, actual]]
        comparison = compare_endpoints(*[read(p) for p in paths])
        detail = root/(label+'_final_endpoints.json'); write(detail, comparison)
        endpoint_rows[label] = {k:v for k,v in comparison.items() if k != 'changes'}
        endpoint_rows[label]['full_changes_receipt'] = str(detail)
        files.extend([other/'completion.json', *paths, detail])
    payload.update(actual_CPD_ns=actual['CPD_ns'], actual_resources=actual['resources'],
        actual_complete_seconds=actual['complete_wall_seconds'],
        actual_sampled_tree_PSS_peak_kib=actual['sampled_tree_PSS_peak_kib'],
        actual_sampled_tree_RSS_peak_kib=actual['sampled_tree_RSS_peak_kib'],
        actual_missing_memory_observations=actual['missing_memory_observations'],
        complete_endpoint_comparisons=endpoint_rows, graph_payloads=payloads,
        same_role_execution_exact=exact, comparable_engineering_cost_observation=exact,
        historical_domain_complete_seconds=old['complete_wall_seconds'],
        descriptive_same_role_seconds_difference=actual['complete_wall_seconds']-old['complete_wall_seconds'] if exact else None,
        descriptive_same_role_percent_difference=100*(actual['complete_wall_seconds']/old['complete_wall_seconds']-1) if exact else None,
        actual_metadata_consumers_within_measured_flow=True)
    files.extend([case/'completion.json', reference/'completion.json', case/'config.json', reference/'config.json',
        case/'metadata_consumers.json', receipt, *map(Path, equivalent['compared_files'])])
payload.update(source_sha256={str(f):sha(f) for f in dict.fromkeys(files)},
    qualification='One new domain engineering execution with the same optimization set already applied to native. '
    'Full original-domain state/request/native-work and graph equality gate same-behavior historical cost descriptions. '
    'Divergence/failure is retained rather than rerun. Earlier native observer loss, PSS gap and overlap remain; '
    'no optimized domain/native ratio, causal timing attribution or interleaved speedup is claimed. '
    'The original matched +22.95 percent remains historical evidence. No new independent input or integrated-method claim.')
write(root/'comparison.json', payload)
print({k:payload[k] for k in ['passed','registered_new_roles','successful_new_roles','actual_complete_seconds']}, flush=True)
