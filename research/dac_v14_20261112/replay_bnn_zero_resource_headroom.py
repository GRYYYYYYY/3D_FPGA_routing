#!/usr/bin/env python3
"""Arithmetic fixed-resource checks on already legal states; no new routing."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from multiobjective_acceptance_v2 import decide
from run_native_scope_policy_v4 import run_dir

state=D/'timing_cone_bnn_dev_01/Tf';before=read(state/'endpoint_vector.json')
def resources(s):
 a=read(run_dir(s)/'independent_audit.json');assert a['audit']['passed'];p=a['physical_metrics']
 return dict(wirelength=p['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=p['sb_pairs_used'],CB_sources=p['cb_crossing_output_sources_used'])
original=resources(state);rows=[];bindings={str(p):sha(p) for p in [Path(__file__).resolve(),D/'multiobjective_acceptance_v2.py',state/'completion.json',state/'endpoint_vector.json',run_dir(state)/'independent_audit.json']}
paths=[D/'bnn_direct_repair_dev_01'/f'{m}_evaluation' for m in ['weighted_soft','physical_capacity']]
paths += [D/'bnn_release_joint_dev_01'/f'{m}_evaluation' for m in ['Tf_combined_weighted_soft','Tf_combined_physical_capacity','Tf_target_only_weighted_soft']]
for candidate in paths:
 assert read(candidate/'completion.json')['passed'];after=read(candidate/'endpoint_vector.json');res=resources(candidate)
 policies={mode:decide(mode,before,after,original,res,cpd_limit_s=before['cpd_s'],resource_limits=original,native_valid=True,transaction_complete=True,resource_objectives=('wirelength',)) for mode in ['timing_under_resources','resources_under_timing']}
 rows.append(dict(state=str(candidate),CPD_ns=after['cpd_s']*1e9,resources=res,policies=policies))
 for p in [candidate/'completion.json',candidate/'endpoint_vector.json',run_dir(candidate)/'independent_audit.json']:bindings[str(p)]=sha(p)
weighted=next(r for r in rows if '/Tf_combined_weighted_soft_evaluation' in r['state']);assert weighted['policies']['timing_under_resources']['accepted']
physical=next(r for r in rows if '/Tf_combined_physical_capacity_evaluation' in r['state']);assert not physical['policies']['timing_under_resources']['accepted']
out=D/'bnn_zero_resource_headroom_replay_01.json';assert not out.exists()
write(out,dict(passed=True,original_resources=original,CPD_cap_s=before['cpd_s'],rows=rows,source_sha256=bindings,new_native_calls=0,new_commits=0,
 qualification='Additional arithmetic eligibility replay on actual complete legal observations. Original experimental budgets, decisions and running batches are unchanged. Zero headroom is fixed original wire/SB/CB counts, CPD cap equals original full precision. Not a new algorithm run or complete-time measurement.'))
print([(Path(r['state']).name,{k:v['accepted'] for k,v in r['policies'].items()}) for r in rows],flush=True)
