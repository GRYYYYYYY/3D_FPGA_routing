"""Freeze a one-factor preparation variant; no reference routes/queries imported."""
import copy
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

root=D/'complete_BNN_joint_index_flow_01';root.mkdir(exist_ok=False);(root/'configs').mkdir()
component=D/'joint_graph_indexes_BNN_payload_validation_01/completion.json';equivalence=D/'complete_resource_timing_equivalence_validation_01/completion.json'
for path in [component,equivalence]:
 proof=read(path);assert proof['passed'] and all(sha(p)==h for p,h in proof['source_sha256'].items())
case=D/'complete_resource_timing_full_flow_01/bnn_native';original=read(case/'config.json');assert read(case/'completion.json')['passed']
config=copy.deepcopy(original);config['cache_mode']='joint_build_inside_flow';config['preprocessing_strategy']='one_XML_traversal_three_exact_payload_formats'
files=[Path(__file__).resolve(),D/'build_joint_graph_indexes_v1.py',D/'run_complete_serial_joint_index_flow_v1.py',
 D/'run_complete_resource_timing_joint_indexes_v1.py',D/'verify_complete_resource_timing_joint_indexes_v1.py',
 D/'complete_resource_timing_equivalence_v1.py',D/'compare_complete_BNN_joint_indexes_v1.py',D/'queue_complete_BNN_joint_index_flow_01.py',component,equivalence]
config['input_sha256'].update({str(p):sha(p) for p in files})
path=root/'configs/bnn_native_joint_indexes.json';write(path,config)
assert all(config['input_sha256'].get(k)==v for k,v in original['input_sha256'].items())
assert config['route_command']==original['route_command'] and config['phase_binary_sha256']==original['phase_binary_sha256']
write(root/'plan.json',dict(fixed_order=['bnn_native_joint_indexes'],config=str(path),reference_complete_case=str(case),
 predecessor=str(D/'complete_serial_lazy_source_snapshot_01/queue'),prepared_files=[str(p) for p in files],
 qualification='One prospective native BNN full engineering variant; only graph preparation changes from three XML traversals to one joint builder. Same original XML/architecture/BLIF/pack/place, router count8/1.01/seed11, phase binaries, K8/rank3/current margins/resource envelopes, current-STA menu/fraction0.9 and all actual native/STA/scope/physical/restore/seal gates. Standalone component prototype files are never supplied to the algorithm: all three exact-format indexes are newly generated inside this measured command; query graph alias remains inside it. Original2059631wire/7933.245508622378s actual cold native output is the full reference, not historical2059627quality with unknown full cost. All actual downstream states/requests/native protocols and work must match before cost comparison; divergence/failure retained. One observation per version on shared host/uncontrolled OS cache, not statistical speedup or an independent benchmark. Existing jobs/rules/ownership not modified; wait until already registered lazy/source-snapshot cohort terminal and acquire the common serial slot.'))
print(dict(prepared=True,root=str(root),cache_mode=config['cache_mode'],new_native_calls=0),flush=True)
