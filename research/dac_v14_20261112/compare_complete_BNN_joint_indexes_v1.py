"""Report one actual full engineering control, preserving failures/divergence."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from complete_resource_timing_equivalence_v1 import compare

root=D/'complete_BNN_joint_index_flow_01';reference=D/'complete_resource_timing_full_flow_01/bnn_native'
case=root/'bnn_native_joint_indexes';observed=read(root/'queue/results.json')
assert not (root/'comparison.json').exists()
files=[Path(__file__).resolve(),D/'complete_resource_timing_equivalence_v1.py',root/'plan.json',root/'queue/results.json',reference/'completion.json']
if not observed['bnn_native_joint_indexes']['passed']:
 measured=case/'measurement/completion.json'
 payload=dict(passed=True,registered_new_roles=1,successful_new_roles=0,same_downstream_execution=False,
  quality=None,actual_command_seconds=read(measured)['complete_command_wall_seconds'] if measured.exists() else None,
  failure_stage=observed['bnn_native_joint_indexes'].get('failure_stage'),command_passed=observed['bnn_native_joint_indexes'].get('command_passed'),
  failed_returncode=observed['bnn_native_joint_indexes']['returncode'])
 if measured.exists():files.append(measured)
else:
 actual=read(case/'completion.json');old=read(reference/'completion.json');assert actual['passed'] and old['passed']
 configs=[read(p/'config.json') for p in [case,reference]]
 ignored={'input_sha256','cache_mode','preprocessing_strategy'}
 assert {k:v for k,v in configs[0].items() if k not in ignored}=={k:v for k,v in configs[1].items() if k not in ignored}
 assert configs[0]['cache_mode']=='joint_build_inside_flow' and configs[1]['cache_mode']=='build_inside_flow'
 assert all(configs[0]['input_sha256'].get(k)==v for k,v in configs[1]['input_sha256'].items())
 equivalent=compare(case,reference);write(root/'downstream_comparison.json',equivalent)
 payloads=[]
 for component,names in [('resource_flow/graph_audit_cache',['nodes.npy','edges.npy','switches.npy']),('resource_flow/full_graph_cache',['extra.npy','metadata.json']),('physical_query_graph',['graph.bin'])]:
  for name in names:
   paths=[p/'flow'/component/name for p in [case,reference]]
   digests=list(map(sha,paths));payloads.append(dict(component=component,file=name,byte_exact=digests[0]==digests[1]));files.extend(paths)
 exact=all(p['byte_exact'] for p in payloads) and equivalent['downstream_actual_states_requests_and_native_work_exact']
 payload=dict(passed=True,registered_new_roles=1,successful_new_roles=1,graph_payloads=payloads,
  same_downstream_execution=exact,actual_CPD_ns=actual['CPD_ns'],actual_resources=actual['resources'],
  actual_complete_seconds=actual['complete_wall_seconds'],reference_complete_seconds=old['complete_wall_seconds'],
  descriptive_seconds_difference=actual['complete_wall_seconds']-old['complete_wall_seconds'],
  comparable_engineering_cost_observation=exact,
  actual_sampled_tree_PSS_peak_kib=actual['sampled_tree_PSS_peak_kib'],actual_missing_memory_observations=actual['missing_memory_observations'],
  reference_resources=old['resources'],reference_CPD_ns=old['CPD_ns'])
 files += [case/'config.json',reference/'config.json',case/'completion.json',root/'downstream_comparison.json',*map(Path,equivalent['compared_files'])]
payload.update(native_calls_new=0,source_sha256={str(p):sha(p) for p in files},
 qualification='One prospective full native BNN engineering variant compared to its actual2059631wire/7933.245508622378s cold baseline. Every new graph payload is built fresh in the measured command, never imported from the standalone byte-validation prototype. Different preparation work intentionally remains in complete cost. Actual downstream states/requests/native work must match before reporting a comparable engineering-cost observation. Failed or divergent execution retains actual cost/quality and denominator, without claiming same-behavior acceleration. Shared host/OS cache/unmatched chronology, one observation per version, no statistical speedup or independent benchmark confirmation. No older2059627wire quality is substituted and no component-time delta is spliced into whole time.')
write(root/'comparison.json',payload);print({k:v for k,v in payload.items() if k not in ['source_sha256','qualification','graph_payloads']},flush=True)
