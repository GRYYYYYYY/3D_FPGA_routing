"""Compare actual full costs only after actual downstream equivalence checks."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from complete_resource_timing_equivalence_v1 import compare

root=D/'complete_BNN_closed_stream_flow_01'
case=root/'bnn_native_closed_stream'
observed=read(root/'queue/results.json')[case.name]
assert not (root/'comparison.json').exists()
files=[Path(__file__).resolve(),root/'queue/results.json',root/'plan.json',D/'complete_resource_timing_equivalence_v1.py']
payload=dict(passed=True,registered_new_roles=1,successful_new_roles=int(observed['passed']),native_calls_new=0)
if not observed['passed']:
    measured=case/'measurement/completion.json'
    payload.update(failure_stage=observed.get('failure_stage'),
                   command_passed=observed.get('command_passed'),verification_passed=observed.get('verification_passed'),
                   actual_command_seconds=read(measured)['complete_command_wall_seconds'] if measured.exists() else None,
                   comparable_engineering_cost_observation=False)
    if measured.exists():files.append(measured)
else:
    actual=read(case/'completion.json')
    assert actual['passed'] and read(case/'metadata_consumers.json')['all_within_measured_flow']
    comparisons=[]
    for label, reference in [('three_pass_legacy_metadata',D/'complete_resource_timing_full_flow_01/bnn_native'),
                             ('one_pass_legacy_metadata',D/'complete_BNN_joint_index_flow_01/bnn_native_joint_indexes')]:
        if not (reference/'completion.json').exists() or not read(reference/'completion.json')['passed']:
            comparisons.append(dict(reference=label,actual_reference_available=False,comparable=False))
            continue
        old=read(reference/'completion.json')
        configs=[read(p/'config.json') for p in [case,reference]]
        ignored={'input_sha256','cache_mode','preprocessing_strategy','endpoint_loader_strategy','metadata_cache_strategy'}
        assert {k:v for k,v in configs[0].items() if k not in ignored}=={k:v for k,v in configs[1].items() if k not in ignored}
        assert all(configs[0]['input_sha256'].get(k)==v for k,v in configs[1]['input_sha256'].items())
        equivalent=compare(case,reference)
        receipt=root/('downstream_'+label+'.json');write(receipt,equivalent)
        payloads=[]
        for component,names in [('resource_flow/graph_audit_cache',['nodes.npy','edges.npy','switches.npy']),
                                ('resource_flow/full_graph_cache',['extra.npy','metadata.json']),('physical_query_graph',['graph.bin'])]:
            for name in names:
                paths=[p/'flow'/component/name for p in [case,reference]]
                exact=sha(paths[0])==sha(paths[1]);payloads.append(dict(component=component,file=name,byte_exact=exact));files.extend(paths)
        exact=all(r['byte_exact'] for r in payloads) and equivalent['downstream_actual_states_requests_and_native_work_exact']
        comparisons.append(dict(reference=label,actual_reference_available=True,comparable=exact,
            graph_payloads=payloads,reference_actual_seconds=old['complete_wall_seconds'],
            descriptive_seconds_difference=actual['complete_wall_seconds']-old['complete_wall_seconds'],
            reference_actual_PSS_kib=old['sampled_tree_PSS_peak_kib']))
        files += [reference/'completion.json',reference/'config.json',case/'config.json',receipt,*map(Path,equivalent['compared_files'])]
    payload.update(actual_CPD_ns=actual['CPD_ns'],actual_resources=actual['resources'],
        actual_complete_seconds=actual['complete_wall_seconds'],
        actual_sampled_tree_PSS_peak_kib=actual['sampled_tree_PSS_peak_kib'],
        actual_missing_memory_observations=actual['missing_memory_observations'],comparisons=comparisons,
        actual_metadata_consumers_within_measured_flow=True)
    files += [case/'completion.json',case/'metadata_consumers.json']
payload.update(source_sha256={str(f):sha(f) for f in files},qualification='One actual complete native configuration combining explicit same-command metadata cache paths and existing streaming-v2 parsing at previously legacy native observation sites, atop one-pass graph generation. No new native binary, request/search/acceptance rule or assurance gate. Exact actual full states/requests/native work and all six payloads must match each available actual reference before descriptive full-cost comparison. Two implementation changes versus one-pass legacy-path control, not a one-factor parser effect. Parser component RSS/time is never spliced into complete cost. Failures/divergences/missing reference remain explicit. Single shared-host observation, uncontrolled OS cache/chronology; no statistical speedup or independent benchmark claim.')
write(root/'comparison.json',payload)
print({k:v for k,v in payload.items() if k not in ['source_sha256','qualification','comparisons']},flush=True)
