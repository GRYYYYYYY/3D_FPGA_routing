"""Compare actual completed work and matching GNU-time scopes, retaining observer loss."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from complete_resource_timing_quality_equivalence_v1 import compare
from orphaned_flow_time_evidence_v2 import parse_gnu_time
root=D/'orphaned_BNN_engineering_comparison_01';root.mkdir(exist_ok=False)
case=D/'complete_BNN_closed_stream_flow_01/bnn_native_closed_stream'
quality=D/'orphaned_BNN_quality_analysis_02/completion.json';actual=read(quality)
assert actual['passed'] and actual['complete_configuration_quality_verified']
time=read(quality.parent/'original_time_evidence.json');assert time['exit_status']==0
files=[Path(__file__).resolve(),D/'complete_resource_timing_quality_equivalence_v1.py',D/'complete_resource_timing_equivalence_v1.py',
    D/'orphaned_flow_time_evidence_v2.py',quality,quality.parent/'original_time_evidence.json',case/'config.json']
rows=[]
for label,reference in [('three_pass_legacy_metadata',D/'complete_resource_timing_full_flow_01/bnn_native'),
                        ('one_pass_legacy_metadata',D/'complete_BNN_joint_index_flow_01/bnn_native_joint_indexes')]:
    old=read(reference/'completion.json');assert old['passed']
    configs=[read(p/'config.json') for p in [case,reference]]
    ignored={'input_sha256','cache_mode','preprocessing_strategy','endpoint_loader_strategy','metadata_cache_strategy'}
    assert {k:v for k,v in configs[0].items() if k not in ignored}=={k:v for k,v in configs[1].items() if k not in ignored}
    assert all(configs[0]['input_sha256'].get(k)==v for k,v in configs[1]['input_sha256'].items())
    equivalent=compare(case,reference,quality);path=root/(label+'_downstream.json');write(path,equivalent)
    payloads=[]
    for component,names in [('resource_flow/graph_audit_cache',['nodes.npy','edges.npy','switches.npy']),
                             ('resource_flow/full_graph_cache',['extra.npy','metadata.json']),('physical_query_graph',['graph.bin'])]:
        for name in names:
            paths=[p/'flow'/component/name for p in [case,reference]]
            payloads.append(dict(component=component,file=name,byte_exact=sha(paths[0])==sha(paths[1])));files.extend(paths)
    previous=parse_gnu_time((reference/'measurement/gnu_time.txt').read_text());assert previous['exit_status']==0
    registered=read(reference/'measurement/registration.json');assert previous['command_text']==' '.join(registered['command'])
    exact=all(x['byte_exact'] for x in payloads) and equivalent['downstream_actual_states_requests_and_native_work_exact']
    rows.append(dict(reference=label,actual_reference_available=True,actual_execution_and_quality_exact=exact,
        graph_payloads=payloads,reference_GNU_time_seconds=previous['elapsed_seconds'],
        reference_GNU_time_resolution_seconds=previous['display_resolution_seconds'],
        reference_original_observer_seconds=old['complete_wall_seconds'],
        descriptive_GNU_seconds_difference=time['elapsed_seconds']-previous['elapsed_seconds'],
        descriptive_GNU_percent_difference=100*(time['elapsed_seconds']/previous['elapsed_seconds']-1),
        statistical_or_undisturbed_speedup_established=False))
    files += [reference/'completion.json',reference/'config.json',reference/'measurement/gnu_time.txt',reference/'measurement/registration.json',path,*map(Path,equivalent['compared_files'])]
write(root/'completion.json',dict(passed=True,all_actual_work_comparisons_exact=all(x['actual_execution_and_quality_exact'] for x in rows),
    actual_CPD_ns=actual['CPD_ns'],actual_resources=actual['resources'],resource_accepted_steps=actual['resource_accepted_steps'],
    timing_accepted_steps=actual['timing_accepted_steps'],GNU_time_elapsed_seconds=time['elapsed_seconds'],
    GNU_time_display_resolution_seconds=time['display_resolution_seconds'],actual_driver_seconds=read(case/'flow/completion.json')['complete_driver_seconds'],
    waited_process_RSS_high_water_kib=time['waited_process_RSS_high_water_kib'],full_sampled_tree_PSS_available=False,
    original_observer_measurement_available=False,undisturbed_timing=False,comparisons=rows,VPR_calls_new=0,
    source_sha256={str(f):sha(f) for f in dict.fromkeys(files)},
    qualification='Actual original complete flow, independently verified quality and exact downstream state/request/native work comparisons. GNU-time scope matched on both sides; displayed-second precision explicit. Observer loss, sampling gap and brief overlap remain. A descriptive engineering observation, not a statistical speedup, complete PSS measurement, optimized domain/native overhead ratio or independent benchmark sample. No original failed/missing receipt overwritten.'))
print(dict(passed=True,all_actual_work_comparisons_exact=all(x['actual_execution_and_quality_exact'] for x in rows),
    actual_CPD_ns=actual['CPD_ns'],resources=actual['resources'],GNU_seconds=time['elapsed_seconds'],
    comparisons=[{k:v for k,v in row.items() if k not in ['graph_payloads']} for row in rows]),flush=True)
