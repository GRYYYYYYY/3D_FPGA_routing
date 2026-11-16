"""Preregister fresh balanced timing only after existing higher-priority cohorts."""
import copy
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from BNN_interleaved_timing_v1 import ORDER,validate_configs

root=D/'BNN_interleaved_timing_01';assert not root.exists()
native_path=D/'complete_BNN_closed_stream_flow_01/configs/bnn_native_closed_stream.json'
domain_path=D/'complete_BNN_domain_engineering_01/configs/bnn_domain_closed_stream.json'
native,domain=read(native_path),read(domain_path)
assert read(D/'complete_BNN_domain_engineering_01/comparison.json')['same_role_execution_exact']
assert read(D/'orphaned_BNN_engineering_comparison_01/completion.json')['all_actual_work_comparisons_exact']
inputs={}
for config in [native,domain]:
    for f,h in config['input_sha256'].items():
        assert f not in inputs or inputs[f]==h
        inputs[f]=h
paths=[Path(__file__).resolve(),D/'queue_BNN_interleaved_timing_01.py',D/'BNN_interleaved_timing_v1.py',
    D/'validate_BNN_interleaved_timing_01.py',D/'seed_census_analysis_pool_v2.py',
    D/'complete_resource_timing_equivalence_v1.py',D/'endpoint_timing_policy_streaming_v2.py',
    D/'measure_process_tree_v1.py',D/'run_complete_resource_timing_joint_stream_v1.py',D/'verify_complete_resource_timing_joint_stream_v1.py',
    native_path,domain_path,D/'complete_BNN_domain_engineering_01/comparison.json',D/'orphaned_BNN_engineering_comparison_01/completion.json']
for path in paths:
    if path.suffix=='.py':compile(path.read_text(),str(path),'exec')
    inputs[str(path)]=sha(path)
# Verify existing bound code now; all large inputs remain untouched until serial admission.
for f,h in inputs.items():
    if Path(f).suffix=='.py':assert sha(f)==h,(f,'source drift')
native['input_sha256']=inputs.copy();domain['input_sha256']=inputs.copy()
validate_configs(native,domain)
root.mkdir();(root/'configs').mkdir()
for role,config in [('native',native),('domain',domain)]:write(root/'configs'/f'{role}.json',config)
plan=dict(fixed_order=ORDER,predecessor=str(D/'robot_union_mechanism_01/queue'),
    references=dict(native=str(D/'complete_resource_timing_full_flow_01/bnn_native'),domain=str(D/'complete_BNN_domain_engineering_01/bnn_domain_closed_stream')),
    fixed_environment=dict(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1'),
    minimum_free_bytes_at_admission=512*1024**3,paired_order=[['native_0','domain_0'],['domain_1','native_1']],
    input_independence='Same known BNN circuit, architecture and actual placement; repeats are timing observations only. No independent input or CP1 confirmation count.',
    stopping='Exactly four registered measurement attempts for this batch, including failures; never a stopping condition for the research Goal. No automatic rerun or favorable-outcome substitution.',
    timing_scope='Same outer measure_process_tree_v1 observer at0.5s; each command verifies bound inputs, builds its own graph indexes, creates a fresh route and executes the complete fixed resource/current-STA portfolio with all rejections, rollback, nativeSTA and seals. Source compilation, packing/placement generation and readonly post-run equivalence audits remain outside. No historical quality/time substitution, cache flush or warmup route.',
    acceptance='Fixed registered algorithm, root envelopes and terminal rule; no terminal-wire extension, owner escalation or grouping changes. Same engineering both arms, only domain_mode/domain_feedback differ.',
    analysis='Retain4rows and all failures. Require complete measurements, same-role full-state/request/native-work/graph equivalence, same new initial roots and environment signatures before reporting two matched ratios, means and ranges. Missing memory samples disclosed; no exact-peak claim. No statistical or causal speedup inference from two repetitions.',
    qualification='Runs only after existing independent-input confirmation and robot union mechanism queue. Shared-host activity/OS cache remain uncontrolled; original22.95% result remains historical. CP1 and all earlier batches unchanged.',
    source_sha256={str(p):sha(p) for p in [*paths,root/'configs/native.json',root/'configs/domain.json']})
write(root/'plan.json',plan)
write(root/'preflight.json',dict(passed=True,native_calls=0,actual_repeated_timing_complete=False,only_algorithmic_arm_differences=['domain_mode','domain_feedback'],
    source_code_seals_checked=True,large_input_validation_deferred_to_serial_slot=True,new_independent_inputs=0,
    source_sha256={str(root/'plan.json'):sha(root/'plan.json'),**plan['source_sha256']}))
print(dict(prepared=True,root=str(root),fixed_order=ORDER,native_calls=0))
