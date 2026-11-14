#!/usr/bin/env python3
"""Bind completed timing-cone evidence without repeating native experiments."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

obs=read(D/'timing_cone_spmv_dev_04/completion.json')
mechanism=read(D/'spmv_timing_cone_analysis_01.json')
cone=read(D/'spmv_current_worst_arrival_cone_01.json')
ref=read(D/'spmv_current_worst_source_reference_01/completion.json')
for report in [obs,mechanism,cone,ref]:
 assert report['passed'] and all(sha(p)==h for p,h in report['source_sha256'].items())
assert len(mechanism['changed_delay_edges'])==1 and mechanism['changed_arrival_nodes']==[50202]
assert len(mechanism['reachable_endpoints'])==129 and not any(r['arrival_changed'] or r['required_changed'] for r in mechanism['reachable_endpoints'])
boundary=mechanism['masking_boundaries'];assert len(boundary)==1
assert all(v['before'] and v['after'] for v in boundary[0]['max_recurrence_verified'].values())
changed=next(p for p in boundary[0]['incoming'] if p['source_node']==50202)
winners=[p for p in boundary[0]['incoming'] if p['before_native_max_attained']]
assert len(winners)==1 and winners[0]['after_native_max_attained']
assert all(r['stop']==0 and r['cost_s']==r['lower_s']==r['current_physical_s'] for r in ref['queries'])
assert len(ref['queries'])==6 and not cone['unresolved_non_source_nodes']
builds={str(i):read(D/f'timing_cone_stage_0{i}/build_result.json') for i in [1,2,3]}
child_costs=read(D/'timing_cone_spmv_dev_03/process_costs.json')+read(D/'timing_cone_spmv_dev_04/process_costs.json')
failcost=read(D/'timing_cone_spmv_dev_02/process_costs.json')
stage=read(D/'timing_cone_stage_03/binding.json');original=read(D/'native_objective_stage_01/binding.json')
assert sha(D/'timing_cone_stage_03/bin/vpr')==stage['binary_sha256']
for n,h in original['source_sha256'].items():assert sha(D/'src'/n)==sha(D/'native_objective_stage_01/src'/n)==h
names=['report_timing_cone_progress.py','timing_cone_spmv_dev_04/completion.json','timing_cone_spmv_dev_03/process_costs.json','timing_cone_spmv_dev_04/process_costs.json','timing_cone_spmv_dev_02/process_costs.json',
 'spmv_timing_cone_analysis_01.json','spmv_dominant_arrival_cone_01.json','spmv_dominant_source_reference_01/completion.json',
 'spmv_current_worst_arrival_cone_01.json','spmv_current_worst_source_reference_01/completion.json',
 'current_sta_arrival_cone.py','current_sta_arrival_cone_validation_01.json','test_current_sta_arrival_cone.py',
 'query_current_cone_source_reference.py','native_timing_echo_v2.py','test_native_timing_echo_v2.py',
 'timing_cone_stage_03/binding.json','timing_cone_stage_03/all_source_hashes.json','timing_cone_stage_03/CMakeCache.txt',
 'timing_cone_stage_03/src/vpr/src/timing/h3d_native_timing_echo.h','timing_cone_stage_03/src/vpr/src/base/vpr_api.cpp',
 'timing_cone_stage_01/failure_diagnosis.json','timing_cone_stage_02/packaging_failure.json','timing_cone_stage_02/recovery_receipt.json',
 'timing_cone_spmv_dev_02/failure_diagnosis.json','timing_cone_spmv_dev_03/parser_failure_diagnosis.json',
 'run_timing_cone_state_analysis_v2.py','run_timing_cone_recovery.py','analyze_spmv_timing_cone_v2.py',
 'run_timing_cone_state_analysis_uncached.py','run_bnn_current_cone_observations.py','timing_cone_bnn_dev_01/registration.json']
names += [f'timing_cone_stage_0{i}/build_result.json' for i in [1,2,3]]
result=dict(passed=True,quality_promoted=False,new_work_pushed=False,observer_binary_sha256=stage['binary_sha256'],
 original_frozen_sources_unchanged=len(original['source_sha256']),native_observations=obs['roles'],
 mechanism=dict(changed_connection=[6997,1],changed_delay_edges=1,changed_arrival_nodes=1,unchanged_reachable_endpoints=129,
  masking_merge=51164,unique_dominant_connection=[6927,1],gap_before_ps=changed['before_gap_to_native_s']*1e12,gap_after_ps=changed['after_gap_to_native_s']*1e12,
  native_float32_recurrence_verified=True,exact_tie=False),
 current_worst_endpoint=cone['selected_endpoints'],current_worst_cone_connections=ref['queries'],
 current_cpd_ns=7.034697713237392,current_resources=dict(SB=1,CB=967,wirelength=148445),new_accepted_repairs=0,
 timings=dict(successful_observation_children_seconds=sum(r['complete_process_seconds'] for r in child_costs),
  failed_observation_child_seconds=sum(r['complete_process_seconds'] for r in failcost),
  successful_native_process_seconds=sum(r['timing']['native_process_seconds'] for r in obs['roles'].values()),
  successful_evaluation_internal_seconds=sum(r['timing']['complete_evaluation_seconds'] for r in obs['roles'].values()),
  cone_analysis_seconds=mechanism['complete_analysis_seconds'],automatic_cone_selection_seconds=cone['complete_process_seconds'],
  first_three_source_queries_seconds=read(D/'spmv_dominant_source_reference_01/completion.json')['complete_process_seconds'],
  remaining_three_queries_with_three_reused_seconds=ref['complete_process_seconds'],builds=builds,
  qualification='Development observations and engineering builds, not route algorithm formal timing. Nested child/native/audit times must not be summed twice. Cached complete audit measured in fresh observation, no uncached matched whole-process speedup claimed.'),
 failures_preserved=['initial missing sockpp configure','successful binary found at build/vpr/vpr, packaging recovered without rebuild',
  'auto execution engine selected TBB and hit thread guard; corrected to serial matching baseline',
  'parser incorrectly expected time instead of slack; fixed and completed native observations reused'],
 source_sha256={str(D/n):sha(D/n) for n in names},
 next_registered='timing_cone_bnn_dev_01/registration.json',research_complete=False,
 qualification='The six current worst-path routed connections individually attain exact optimistic distances with fixed terminals in the actual zero-RC graph. This is a conditional limit on this route-only intervention, not a global FPGA optimum or a claim that endpoint-vector improvements are exhausted. BNN initial observations are a separate new experiment and are not included as completed quality results.')
write(D/'timing_cone_progress_summary_01.json',result)
print(dict(passed=True,mechanism=result['mechanism'],timings=result['timings']))
